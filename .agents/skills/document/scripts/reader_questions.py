#!/usr/bin/env python3

import pathlib
import re
import sys


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print(f"usage: {sys.argv[0]} <doc-path> [count]", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).resolve()
    count = int(sys.argv[2]) if len(sys.argv) == 3 else 5
    text = path.read_text(encoding="utf-8")
    heads = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)

    questions = [
        "What problem is this document trying to solve?",
        "What is the main proposal or decision?",
        "Why is this approach preferred over the alternatives?",
        "What are the main risks or tradeoffs?",
        "What should happen next after reading this document?",
    ]

    for name in heads:
        if len(questions) >= count:
            break
        questions.append(f"What should a reader learn from the '{name}' section?")

    for idx, item in enumerate(questions[:count], start=1):
        print(f"{idx}. {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
