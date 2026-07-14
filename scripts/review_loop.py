#!/usr/bin/env python3
"""Review-rewrite loop orchestrator for deep-industry-research.

Manages state in <run-dir>/review-state.json and renders prompts for sub-agents.
The main agent is responsible for actually spawning sub-agents (sessions_spawn);
this script just prepares prompts, parses results, and decides routing.

Subcommands:
    init             — initialize review-state.json with run config
    prepare-review   — render review prompt for next round
    parse-review     — parse latest review-round-N.md and update state
    prepare-rewrite  — render rewrite prompt for current round
    mark-rewrite     — record that rewrite for round N completed
    status           — print current state
    decide           — return next decision: continue|pass|plateau|max_rounds

State file schema (review-state.json):
{
  "run_dir": "...",
  "report_path": "...",
  "brief_path": "...",
  "source_index_path": "...",
  "evidence_gap_path": "...",
  "scoring_path": "...",
  "report_type": "knowledge_build",
  "report_title": "...",
  "max_rounds": 5,
  "plateau_threshold": 0.7,
  "pass_score": 9.0,
  "current_round": 0,
  "history": [
    {"round": 1, "score": 7.5, "route": "rewrite+search", "gates_passed": 4, "plateau": false, "summary": "..."},
    ...
  ],
  "rewrite_log": [
    {"round": 1, "items_addressed": 16, "items_skipped": 0, "summary": "..."}
  ]
}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
STATE_FILENAME = "review-state.json"

REVIEW_RESULT_PATTERN = re.compile(
    r"<<<REVIEW_RESULT>>>\s*(\{.*?\})\s*<<<END_REVIEW_RESULT>>>",
    re.DOTALL,
)
REWRITE_RESULT_PATTERN = re.compile(
    r"<<<REWRITE_RESULT>>>\s*(\{.*?\})\s*<<<END_REWRITE_RESULT>>>",
    re.DOTALL,
)


@dataclass
class ReviewRecord:
    round: int
    score: float
    route: str
    gates_passed: int
    plateau: bool
    summary: str


@dataclass
class RewriteRecord:
    round: int
    items_addressed: int
    items_skipped: int
    summary: str


@dataclass
class State:
    run_dir: str
    report_path: str
    brief_path: str
    source_index_path: str
    evidence_gap_path: str
    scoring_path: str
    report_type: str
    report_title: str
    max_rounds: int = 5
    plateau_threshold: float = 0.7
    pass_score: float = 9.0
    current_round: int = 0
    phase: str = "review_loop"  # review_loop | final | blocked
    history: list[dict] = field(default_factory=list)
    rewrite_log: list[dict] = field(default_factory=list)

    def latest_review(self) -> Optional[ReviewRecord]:
        if not self.history:
            return None
        return ReviewRecord(**self.history[-1])

    def previous_review(self) -> Optional[ReviewRecord]:
        if len(self.history) < 2:
            return None
        return ReviewRecord(**self.history[-2])


def state_path(run_dir: Path) -> Path:
    return run_dir / STATE_FILENAME


def load_state(run_dir: Path) -> State:
    p = state_path(run_dir)
    if not p.exists():
        raise FileNotFoundError(f"No review-state.json at {p}. Run `init` first.")
    data = json.loads(p.read_text(encoding="utf-8"))
    return State(**data)


def save_state(state: State) -> None:
    p = state_path(Path(state.run_dir))
    p.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")


def render_template(template_name: str, **kwargs) -> str:
    path = TEMPLATES_DIR / template_name
    text = path.read_text(encoding="utf-8")
    return text.format(**kwargs)


# ---- Subcommands ----

def cmd_init(args) -> int:
    run_dir: Path = args.run_dir.resolve()
    if not run_dir.exists():
        print(f"Error: run-dir not found: {run_dir}", file=sys.stderr)
        return 2

    # Resolve required files
    def resolve(p: Optional[Path], default_name: str) -> str:
        if p is not None:
            return str(p.resolve())
        candidate = run_dir / default_name
        return str(candidate.resolve())

    state = State(
        run_dir=str(run_dir),
        report_path=resolve(args.report, "final-report.md"),
        brief_path=resolve(args.brief, "research-brief.md"),
        source_index_path=resolve(args.source_index, "source-index.md"),
        evidence_gap_path=resolve(args.evidence_gap, "evidence-gap-log.md"),
        scoring_path=str((args.scoring or SCRIPT_DIR.parent / "references" / "scoring.md").resolve()),
        report_type=args.type,
        report_title=args.title,
        max_rounds=args.max_rounds,
        plateau_threshold=args.plateau_threshold,
        pass_score=args.pass_score,
        current_round=args.starting_round,
        history=[],
        rewrite_log=[],
    )

    # If starting_round > 0, hydrate history from existing review-round-N.md files
    if args.starting_round > 0:
        for n in range(1, args.starting_round + 1):
            review_file = run_dir / f"review-round-{n}.md"
            if review_file.exists():
                rec = parse_review_file(review_file)
                if rec:
                    state.history.append(asdict(rec))
                    print(f"  hydrated round {n}: score={rec.score} route={rec.route}", file=sys.stderr)

    save_state(state)
    print(f"Initialized review state at {state_path(run_dir)}", file=sys.stderr)
    print(f"  report_type={state.report_type}  current_round={state.current_round}", file=sys.stderr)
    return 0


def cmd_prepare_review(args) -> int:
    state = load_state(args.run_dir)
    next_round = state.current_round + 1
    review_output = Path(state.run_dir) / f"review-round-{next_round}.md"

    prev = state.latest_review()
    if prev:
        prev_summary = (
            f"上一轮（第 {prev.round} 轮）评审给出 **{prev.score}/10**，路由 **{prev.route}**，"
            f"通过 {prev.gates_passed}/7 关卡。摘要：{prev.summary}\n\n"
            f"执行 agent 已按上一轮评审清单修改，产出新版本。你需要严格独立评审本轮，"
            f"判断是否达到 {state.pass_score} 通过阈值，或仍需迭代。"
        )
        prev_review_path = Path(state.run_dir) / f"review-round-{prev.round}.md"
        previous_review_block = (
            f"   - `{prev_review_path}` — 上一轮评审报告（参考用，看 P0+P1 项是否真的解决）\n"
        )
        prev_checklist_block = (
            f"\n   - **逐项核对上一轮 P0+P1 清单是否真的解决**，对每项标记 ✅/⚠️/❌\n"
        )
        prev_score_str = str(prev.score)
        plateau_threshold = round(prev.score + state.plateau_threshold, 2)
    else:
        prev_summary = "这是第一轮评审。报告 v1 已完成，需要做完整独立评审。"
        previous_review_block = ""
        prev_checklist_block = ""
        prev_score_str = "N/A"
        plateau_threshold = state.pass_score

    prompt = render_template(
        "review_prompt.md",
        round_n=next_round,
        previous_review_summary=prev_summary,
        brief_path=state.brief_path,
        report_path=state.report_path,
        source_index_path=state.source_index_path,
        evidence_gap_path=state.evidence_gap_path,
        scoring_path=state.scoring_path,
        previous_review_block=previous_review_block,
        report_type=state.report_type,
        prev_checklist_block=prev_checklist_block,
        prev_score=prev_score_str,
        plateau_threshold=plateau_threshold,
        review_output_path=str(review_output),
        report_title=state.report_title,
    )

    if args.output_json:
        meta = {
            "next_round": next_round,
            "review_output_path": str(review_output),
            "agent_id": "main",
            "label": f"review-r{next_round}",
            "task": prompt,
        }
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        print(prompt)
    return 0


def parse_review_file(review_path: Path) -> Optional[ReviewRecord]:
    if not review_path.exists():
        return None
    text = review_path.read_text(encoding="utf-8")
    m = REVIEW_RESULT_PATTERN.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    return ReviewRecord(
        round=int(data.get("round", 0)),
        score=float(data.get("score", 0.0)),
        route=str(data.get("route", "unknown")),
        gates_passed=int(data.get("gates_passed", 0)),
        plateau=bool(data.get("plateau", False)),
        summary=str(data.get("summary", "")),
    )


def cmd_parse_review(args) -> int:
    state = load_state(args.run_dir)
    next_round = state.current_round + 1
    review_path = Path(state.run_dir) / f"review-round-{next_round}.md"

    rec = parse_review_file(review_path)
    if not rec:
        print(f"Error: could not parse review result from {review_path}", file=sys.stderr)
        print("(make sure the sub-agent wrote the <<<REVIEW_RESULT>>>...<<<END_REVIEW_RESULT>>> block)", file=sys.stderr)
        return 3

    if rec.round != next_round:
        print(f"Warning: review file says round={rec.round} but expected {next_round}", file=sys.stderr)
        rec.round = next_round

    state.current_round = next_round
    state.history.append(asdict(rec))
    save_state(state)

    decision = decide_next(state)
    out = {
        "round": rec.round,
        "score": rec.score,
        "route": rec.route,
        "gates_passed": rec.gates_passed,
        "plateau": rec.plateau,
        "summary": rec.summary,
        "decision": decision,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def decide_next(state: State) -> str:
    """Return: pass | plateau | max_rounds | continue. Also mutates state.phase."""
    result = _decide_next_inner(state)
    if result == "pass":
        state.phase = "final"
    elif result == "blocked":
        state.phase = "blocked"
    return result


def _decide_next_inner(state: State) -> str:
    latest = state.latest_review()
    if latest is None:
        return "continue"

    # Pass: score reached threshold
    #   Minimum 2 rounds enforced, exception: round 1 with score>=9.5 AND all 7 gates passed
    if latest.score >= state.pass_score:
        if latest.round >= 2:
            return "pass"
        if latest.round == 1 and latest.score >= 9.5 and latest.gates_passed >= 7:
            return "pass"
        # else: force continue for at least 2 rounds
        return "continue"
    # Pass: route says pass explicitly (same 2-round guard)
    if latest.route == "pass":
        if latest.round >= 2 or (latest.round == 1 and latest.score >= 9.5 and latest.gates_passed >= 7):
            return "pass"
        return "continue"
    # Blocked: cannot proceed
    if latest.route == "blocked":
        return "blocked"
    # Plateau: 2 consecutive rounds with delta < threshold
    prev = state.previous_review()
    if prev is not None:
        delta = latest.score - prev.score
        if delta < state.plateau_threshold and (latest.plateau or latest.route in ("rewrite", "rewrite+search")):
            # only call plateau if 2 small deltas in a row
            if len(state.history) >= 3:
                prev_prev = ReviewRecord(**state.history[-3])
                if prev.score - prev_prev.score < state.plateau_threshold:
                    return "plateau"
            elif latest.plateau:
                return "plateau"
    # Max rounds
    if latest.round >= state.max_rounds:
        return "max_rounds"
    return "continue"


def cmd_prepare_rewrite(args) -> int:
    state = load_state(args.run_dir)
    latest = state.latest_review()
    if not latest:
        print("Error: no review history. Run `parse-review` first.", file=sys.stderr)
        return 4

    review_path = Path(state.run_dir) / f"review-round-{latest.round}.md"
    rewrite_log_path = Path(state.run_dir) / f"rewrite-round-{latest.round}.log.md"

    prompt = render_template(
        "rewrite_prompt.md",
        round_n=latest.round,
        score=latest.score,
        route=latest.route,
        brief_path=state.brief_path,
        report_path=state.report_path,
        review_path=str(review_path),
        source_index_path=state.source_index_path,
        evidence_gap_path=state.evidence_gap_path,
        rewrite_log_path=str(rewrite_log_path),
    )

    if args.output_json:
        meta = {
            "round": latest.round,
            "review_path": str(review_path),
            "rewrite_log_path": str(rewrite_log_path),
            "agent_id": "main",
            "label": f"rewrite-r{latest.round}",
            "task": prompt,
        }
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        print(prompt)
    return 0


def cmd_mark_rewrite(args) -> int:
    state = load_state(args.run_dir)
    latest = state.latest_review()
    if not latest:
        print("Error: no review history.", file=sys.stderr)
        return 4

    rewrite_log_path = Path(state.run_dir) / f"rewrite-round-{latest.round}.log.md"
    items_addressed = args.items_addressed
    items_skipped = args.items_skipped
    summary = args.summary or ""

    # Try to parse from log file if exists
    if rewrite_log_path.exists() and items_addressed is None:
        text = rewrite_log_path.read_text(encoding="utf-8")
        m = REWRITE_RESULT_PATTERN.search(text)
        if m:
            try:
                data = json.loads(m.group(1))
                items_addressed = items_addressed or int(data.get("items_addressed", 0))
                items_skipped = items_skipped or int(data.get("items_skipped", 0))
                summary = summary or str(data.get("summary", ""))
            except json.JSONDecodeError:
                pass

    rec = RewriteRecord(
        round=latest.round,
        items_addressed=items_addressed or 0,
        items_skipped=items_skipped or 0,
        summary=summary,
    )
    state.rewrite_log.append(asdict(rec))
    save_state(state)
    print(json.dumps(asdict(rec), ensure_ascii=False, indent=2))
    return 0


def cmd_status(args) -> int:
    state = load_state(args.run_dir)
    decision = decide_next(state)
    out = {
        "run_dir": state.run_dir,
        "report_type": state.report_type,
        "current_round": state.current_round,
        "max_rounds": state.max_rounds,
        "history": state.history,
        "rewrite_log": state.rewrite_log,
        "decision": decision,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_decide(args) -> int:
    state = load_state(args.run_dir)
    decision = decide_next(state)
    print(decision)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Review-rewrite loop orchestrator.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize review state for a run directory.")
    p_init.add_argument("--run-dir", type=Path, required=True)
    p_init.add_argument("--report", type=Path, default=None)
    p_init.add_argument("--brief", type=Path, default=None)
    p_init.add_argument("--source-index", type=Path, default=None)
    p_init.add_argument("--evidence-gap", type=Path, default=None)
    p_init.add_argument("--scoring", type=Path, default=None)
    p_init.add_argument(
        "--type",
        required=True,
        choices=["knowledge_build", "direction_memo", "project_proposal", "decision_memo"],
    )
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--max-rounds", type=int, default=5)
    p_init.add_argument("--plateau-threshold", type=float, default=0.7)
    p_init.add_argument("--pass-score", type=float, default=9.0)
    p_init.add_argument(
        "--starting-round",
        type=int,
        default=0,
        help="If reviews already exist, hydrate state from review-round-1..N.md",
    )
    p_init.set_defaults(func=cmd_init)

    p_pr = sub.add_parser("prepare-review", help="Print review sub-agent prompt for next round.")
    p_pr.add_argument("--run-dir", type=Path, required=True)
    p_pr.add_argument("--output-json", action="store_true", help="Wrap prompt in JSON envelope (task/label/agent_id).")
    p_pr.set_defaults(func=cmd_prepare_review)

    p_ps = sub.add_parser("parse-review", help="Parse latest review-round-N.md and update state.")
    p_ps.add_argument("--run-dir", type=Path, required=True)
    p_ps.set_defaults(func=cmd_parse_review)

    p_rw = sub.add_parser("prepare-rewrite", help="Print rewrite sub-agent prompt for current round.")
    p_rw.add_argument("--run-dir", type=Path, required=True)
    p_rw.add_argument("--output-json", action="store_true")
    p_rw.set_defaults(func=cmd_prepare_rewrite)

    p_mr = sub.add_parser("mark-rewrite", help="Record rewrite completion (auto-parses log if present).")
    p_mr.add_argument("--run-dir", type=Path, required=True)
    p_mr.add_argument("--items-addressed", type=int, default=None)
    p_mr.add_argument("--items-skipped", type=int, default=None)
    p_mr.add_argument("--summary", type=str, default=None)
    p_mr.set_defaults(func=cmd_mark_rewrite)

    p_st = sub.add_parser("status", help="Print current state.")
    p_st.add_argument("--run-dir", type=Path, required=True)
    p_st.set_defaults(func=cmd_status)

    p_dc = sub.add_parser("decide", help="Print next decision: pass|plateau|max_rounds|continue|blocked.")
    p_dc.add_argument("--run-dir", type=Path, required=True)
    p_dc.set_defaults(func=cmd_decide)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
