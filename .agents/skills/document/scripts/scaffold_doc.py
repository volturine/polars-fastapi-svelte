#!/usr/bin/env python3

import pathlib
import sys


SECTIONS = {
    "decision": [
        "Summary",
        "Context",
        "Problem",
        "Decision",
        "Options Considered",
        "Tradeoffs",
        "Rollout Or Follow-Up",
    ],
    "spec": [
        "Summary",
        "Goals",
        "Non-Goals",
        "Current State",
        "Proposed Design",
        "Edge Cases",
        "Risks",
        "Testing And Rollout",
    ],
    "proposal": [
        "Summary",
        "Problem Or Opportunity",
        "Proposal",
        "Expected Impact",
        "Cost And Constraints",
        "Risks",
        "Next Steps",
    ],
    "rfc": [
        "Summary",
        "Motivation",
        "Detailed Design",
        "Alternatives",
        "Migration Or Rollout",
        "Open Questions",
    ],
    "runbook": [
        "Purpose",
        "Preconditions",
        "Procedure",
        "Verification",
        "Failure Modes",
        "Escalation",
    ],
    "prd": [
        "Summary",
        "Problem",
        "Users",
        "Goals",
        "Requirements",
        "Non-Goals",
        "Metrics",
        "Risks And Dependencies",
    ],
}


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print(f"usage: {sys.argv[0]} <output-path> <doc-type> [title]", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).resolve()
    kind = sys.argv[2].strip().lower()
    title = sys.argv[3].strip() if len(sys.argv) == 4 else kind.replace("-", " ").title()

    sections = SECTIONS.get(kind)
    if sections is None:
        print(f"unknown doc type: {kind}", file=sys.stderr)
        print(f"known types: {', '.join(sorted(SECTIONS))}", file=sys.stderr)
        return 1

    lines = [f"# {title}", ""]
    for name in sections:
        lines.append(f"## {name}")
        lines.append("[To be written]")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"created document scaffold at {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
