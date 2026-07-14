#!/usr/bin/env python3
"""Rule-based linter for deep-industry-research reports.

Catches mechanical violations of USER.md hard rules before sending to LLM review:
- Marketing-tone words
- Bare URLs (not in markdown link)
- Bare WeChat homepage links
- "待补" placeholders
- "对快手的启示" / "对我们意味什么" section endings
- Storyline-style chapter titles
- Project-mode words in Knowledge-Build reports (MVP, Kill, hit-rate %, engineer-month)
- Specific numbers that look unverified (no nearby URL link)

Usage:
    uv run lint_report.py <report.md> [--brief <brief.md>] [--type knowledge_build|direction_memo|project_proposal|decision_memo]

Exits non-zero if any P0/P1 violation found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---- Rule definitions ----

MARKETING_WORDS = [
    r"最完整",
    r"最全",
    r"极高",
    r"极强",
    r"推荐保存",
    r"推荐收藏",
    r"信息密度最高",
    r"值得直接对标",
    r"不可错过",
    r"必读",
    r"绝对",
    r"完美",
    r"全网首发",
    r"独家",
    r"重磅",
    r"惊艳",
    r"颠覆",
]

PROJECT_MODE_WORDS = [
    r"\bMVP\b",
    r"Kill\s*Criteria",
    r"成功标准[:：]",
    r"停止条件[:：]",
    r"命中率\s*[\d\.]+\s*%",
    r"误操作\s*[<>≤≥]",
    r"P[012]\s*[（(]?(?:阶段|路径)",
    r"工程师月",
]

KUAISHOU_BENCHMARK_PATTERNS = [
    r"对快手的启示",
    r"对我们意味什么",
    r"我们[应该]?(?:可以)?对标",
    r"我们怎么(?:做|对标|跟进)",
    r"快手[应该]?(?:可以)?对标",
    r"快手如何(?:做|应对)",
]

# A storyline title is "## N、Title：subtitle" with a verb-ish subtitle.
# We only flag in Knowledge-Build reports.
STORYLINE_TITLE_PATTERN = re.compile(
    r"^#{2,3}\s*[一二三四五六七八九十\d]+[、.\s].*?[：:].+$",
    re.MULTILINE,
)

BIDU = re.compile(r"待补|TBD|TODO[:：]?", re.IGNORECASE)

# Bare URL: a URL that's not inside markdown link [text](url) and not inside <url>
BARE_URL_PATTERN = re.compile(r"(?<![\(\<])(https?://[^\s\)<>\]]+)")
# Markdown link URLs to exclude
MD_LINK_URL_PATTERN = re.compile(r"\[[^\]]+\]\((https?://[^\)]+)\)")

# WeChat MP homepage as link target (not an article URL)
BARE_WX_HOMEPAGE = re.compile(r"\]\(https?://mp\.weixin\.qq\.com/?\)")

# Report type marker in brief or report header
TYPE_MARKER_PATTERN = re.compile(
    r"报告类型[\s:：*]*[*]*\s*(?:[*]+\s*)?(方向汇报型|立项材料型|学习/?调研型|"
    r"调研/?学习型|决策备忘型|"
    r"Direction\s*Memo|Project\s*Proposal|Knowledge\s*Build|Decision\s*Memo)",
    re.IGNORECASE,
)

REPORT_TYPE_MAP = {
    "方向汇报型": "direction_memo",
    "立项材料型": "project_proposal",
    "学习/调研型": "knowledge_build",
    "学习调研型": "knowledge_build",
    "调研/学习型": "knowledge_build",
    "调研学习型": "knowledge_build",
    "决策备忘型": "decision_memo",
    "direction memo": "direction_memo",
    "project proposal": "project_proposal",
    "knowledge build": "knowledge_build",
    "decision memo": "decision_memo",
}

# Specific-number heuristics for "未对齐数字嫌疑": large rounded numbers near no link
SUSPICIOUS_NUMBER_PATTERN = re.compile(
    r"(?:约|超过|高达|增长|涨幅|涨)?\s*[\d,\.]+\s*(?:亿|万|%|％)",
)


# ---- Issue model ----

SEVERITY_P0 = "P0"  # blocks delivery
SEVERITY_P1 = "P1"  # USER.md hard rule
SEVERITY_P2 = "P2"  # nice to fix

@dataclass
class Issue:
    rule: str
    severity: str
    line: int
    excerpt: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "line": self.line,
            "excerpt": self.excerpt[:120],
            "note": self.note,
        }


@dataclass
class LintResult:
    report_path: str
    report_type: Optional[str]
    issues: list[Issue] = field(default_factory=list)

    @property
    def p0_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == SEVERITY_P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == SEVERITY_P1)

    @property
    def p2_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == SEVERITY_P2)

    @property
    def has_blockers(self) -> bool:
        return self.p0_count > 0 or self.p1_count > 0


# ---- Helpers ----

def detect_report_type(brief_path: Optional[Path], report_text: Optional[str] = None) -> Optional[str]:
    # Try brief first
    if brief_path and brief_path.exists():
        text = brief_path.read_text(encoding="utf-8")
        m = TYPE_MARKER_PATTERN.search(text)
        if m:
            raw = m.group(1).strip().lower().replace("/", "")
            mapped = REPORT_TYPE_MAP.get(raw, None)
            if mapped:
                return mapped
    # Fallback: try report header
    if report_text:
        m = TYPE_MARKER_PATTERN.search(report_text)
        if m:
            raw = m.group(1).strip().lower().replace("/", "")
            return REPORT_TYPE_MAP.get(raw, None)
    return None


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def excerpt_at(text: str, line_no: int, span: int = 80) -> str:
    lines = text.splitlines()
    if 0 < line_no <= len(lines):
        return lines[line_no - 1][:span].strip()
    return ""


# ---- Rules ----

def check_marketing_words(text: str) -> list[Issue]:
    issues = []
    for word in MARKETING_WORDS:
        for m in re.finditer(word, text):
            ln = line_of(text, m.start())
            issues.append(Issue(
                rule="marketing_word",
                severity=SEVERITY_P1,
                line=ln,
                excerpt=excerpt_at(text, ln),
                note=f"推销性表述: {m.group(0)}",
            ))
    return issues


def check_kuaishou_benchmark(text: str) -> list[Issue]:
    issues = []
    lines = text.splitlines()
    for pattern in KUAISHOU_BENCHMARK_PATTERNS:
        for m in re.finditer(pattern, text):
            ln = line_of(text, m.start())
            line_text = lines[ln - 1] if 0 < ln <= len(lines) else ""
            stripped = line_text.lstrip()
            # Skip blockquote lines (Brief excerpts) and "不在范围"-style scope declarations
            if stripped.startswith(">"):
                continue
            if "不在范围" in line_text or "不写" in line_text or "排除" in line_text:
                continue
            issues.append(Issue(
                rule="kuaishou_benchmark",
                severity=SEVERITY_P0,
                line=ln,
                excerpt=excerpt_at(text, ln),
                note=f"USER.md 禁止: {m.group(0)}（章末'对快手的启示'/对标段落）",
            ))
    return issues


def check_project_mode_words(text: str, report_type: Optional[str]) -> list[Issue]:
    """Only flag in Knowledge-Build / Direction-Memo reports."""
    if report_type not in ("knowledge_build", "direction_memo"):
        return []
    issues = []
    lines = text.splitlines()
    for pattern in PROJECT_MODE_WORDS:
        for m in re.finditer(pattern, text):
            ln = line_of(text, m.start())
            line_text = lines[ln - 1] if 0 < ln <= len(lines) else ""
            stripped = line_text.lstrip()
            # Skip blockquote / scope-declaration lines
            if stripped.startswith(">"):
                continue
            if "不在范围" in line_text or "不写" in line_text or "排除" in line_text:
                continue
            issues.append(Issue(
                rule="project_mode_word",
                severity=SEVERITY_P1,
                line=ln,
                excerpt=excerpt_at(text, ln),
                note=f"调研/汇报型不应出现立项词: {m.group(0)}",
            ))
    return issues


def check_storyline_titles(text: str, report_type: Optional[str]) -> list[Issue]:
    """Only flag in Knowledge-Build reports per USER.md.

    P2 severity (heuristic, easily false-positives on enumerated subtitles like
    'X：A vs B'). Surface for human review, don't block.
    """
    if report_type != "knowledge_build":
        return []
    issues = []
    for m in STORYLINE_TITLE_PATTERN.finditer(text):
        ln = line_of(text, m.start())
        title = m.group(0).strip()
        colon_match = re.search(r"[：:]", title)
        if not colon_match:
            continue
        subtitle = title[colon_match.end():].strip()
        if len(subtitle) < 6:  # short noun phrase, OK
            continue
        # Allow enumerated subtitles like "A vs B", "A、B、C"
        if re.search(r"\s+vs\s+|、|，|,", subtitle):
            continue
        issues.append(Issue(
            rule="storyline_title",
            severity=SEVERITY_P2,
            line=ln,
            excerpt=title,
            note="标题含冒号 + 长副标题，可能是 storyline 句式（人审）",
        ))
    return issues


def check_placeholders(text: str) -> list[Issue]:
    issues = []
    for m in BIDU.finditer(text):
        ln = line_of(text, m.start())
        issues.append(Issue(
            rule="placeholder",
            severity=SEVERITY_P1,
            line=ln,
            excerpt=excerpt_at(text, ln),
            note=f"USER.md 禁止占位: {m.group(0)}",
        ))
    return issues


def check_bare_urls(text: str) -> list[Issue]:
    issues = []
    md_link_urls = set()
    for m in MD_LINK_URL_PATTERN.finditer(text):
        md_link_urls.add(m.group(1))

    # Find URLs not preceded by ( and check if they're in markdown link form
    for m in BARE_URL_PATTERN.finditer(text):
        url = m.group(1).rstrip(".,;)]")
        # Strip any markdown angle brackets
        if url in md_link_urls:
            continue
        # Check if url appears in a markdown link by scanning surrounding context
        start = max(0, m.start() - 200)
        ctx = text[start:m.end() + 5]
        # If url is wrapped in ](url) somewhere, it's a markdown link
        if re.search(r"\]\(\s*" + re.escape(url), ctx):
            continue
        ln = line_of(text, m.start())
        issues.append(Issue(
            rule="bare_url",
            severity=SEVERITY_P0,
            line=ln,
            excerpt=excerpt_at(text, ln),
            note=f"裸链未包成 markdown link: {url[:60]}",
        ))
    return issues


def check_bare_wx_homepage(text: str) -> list[Issue]:
    issues = []
    for m in BARE_WX_HOMEPAGE.finditer(text):
        ln = line_of(text, m.start())
        issues.append(Issue(
            rule="wx_homepage_as_link",
            severity=SEVERITY_P0,
            line=ln,
            excerpt=excerpt_at(text, ln),
            note="链接指向微信公众号首页而非文章原 URL",
        ))
    return issues


def check_unsourced_numbers(text: str) -> list[Issue]:
    """Heuristic: a sentence containing a large rounded number (亿/万/%) with
    no markdown link in the same paragraph.

    P2 only — high false-positive rate, surfaces for human review.
    """
    issues: list[Issue] = []
    # Split by blank line into paragraphs
    paragraphs = re.split(r"\n\s*\n", text)
    offset = 0
    for para in paragraphs:
        if SUSPICIOUS_NUMBER_PATTERN.search(para) and not MD_LINK_URL_PATTERN.search(para):
            # Find first match line
            m = SUSPICIOUS_NUMBER_PATTERN.search(para)
            if m:
                abs_offset = offset + m.start()
                ln = line_of(text, abs_offset)
                # Skip if this is a heading or table separator
                excerpt = excerpt_at(text, ln)
                if excerpt.startswith("|") or excerpt.startswith("#"):
                    pass
                else:
                    issues.append(Issue(
                        rule="unsourced_number_suspect",
                        severity=SEVERITY_P2,
                        line=ln,
                        excerpt=excerpt,
                        note=f"段内含大数字 '{m.group(0)}' 但无 markdown 链接，可能未对齐",
                    ))
        offset += len(para) + 2
    return issues


# ---- Main ----

def lint(report_path: Path, brief_path: Optional[Path], report_type_override: Optional[str]) -> LintResult:
    text = report_path.read_text(encoding="utf-8")
    report_type = report_type_override or detect_report_type(brief_path, text)

    issues: list[Issue] = []
    issues.extend(check_marketing_words(text))
    issues.extend(check_kuaishou_benchmark(text))
    issues.extend(check_project_mode_words(text, report_type))
    issues.extend(check_storyline_titles(text, report_type))
    issues.extend(check_placeholders(text))
    issues.extend(check_bare_urls(text))
    issues.extend(check_bare_wx_homepage(text))
    issues.extend(check_unsourced_numbers(text))

    issues.sort(key=lambda i: (i.severity, i.line))

    return LintResult(
        report_path=str(report_path),
        report_type=report_type,
        issues=issues,
    )


def format_human(result: LintResult) -> str:
    lines = []
    lines.append(f"# Lint report: {result.report_path}")
    lines.append(f"Report type: {result.report_type or 'unknown (no brief or marker)'}")
    lines.append(f"P0={result.p0_count}  P1={result.p1_count}  P2={result.p2_count}")
    lines.append("")
    if not result.issues:
        lines.append("✅ No issues found.")
    else:
        for sev in (SEVERITY_P0, SEVERITY_P1, SEVERITY_P2):
            sev_issues = [i for i in result.issues if i.severity == sev]
            if not sev_issues:
                continue
            lines.append(f"## {sev} ({len(sev_issues)})")
            for i in sev_issues:
                lines.append(f"- L{i.line:>4} [{i.rule}] {i.note}")
                lines.append(f"        > {i.excerpt}")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Lint a deep-industry-research report against USER.md hard rules.")
    ap.add_argument("report", type=Path, help="Path to report markdown")
    ap.add_argument("--brief", type=Path, default=None, help="Path to research brief (for type detection)")
    ap.add_argument(
        "--type",
        choices=["knowledge_build", "direction_memo", "project_proposal", "decision_memo"],
        default=None,
        help="Override report type",
    )
    ap.add_argument("--json", action="store_true", help="Output JSON instead of human-readable")
    args = ap.parse_args()

    if not args.report.exists():
        print(f"Error: report not found: {args.report}", file=sys.stderr)
        sys.exit(2)

    result = lint(args.report, args.brief, args.type)

    # Gate: final-report.md may only exist when review-state.json shows phase="final"
    if args.report.name == "final-report.md":
        state_path = args.report.parent / "review-state.json"
        if state_path.exists():
            try:
                state_data = json.loads(state_path.read_text(encoding="utf-8"))
                phase = state_data.get("phase")
                if phase and phase != "final":
                    print(
                        f"❌ BLOCK: final-report.md written but review-state.json phase='{phase}' (expected 'final'). "
                        "阶段二/三未完成，禁止交付 final-report.md。请先跑完 review 循环，达到 pass 后再重命名。",
                        file=sys.stderr,
                    )
                    sys.exit(3)
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️  Could not read review-state.json: {e}", file=sys.stderr)

    if args.json:
        out = {
            "report_path": result.report_path,
            "report_type": result.report_type,
            "p0": result.p0_count,
            "p1": result.p1_count,
            "p2": result.p2_count,
            "issues": [i.to_dict() for i in result.issues],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(format_human(result))

    sys.exit(1 if result.has_blockers else 0)


if __name__ == "__main__":
    main()
