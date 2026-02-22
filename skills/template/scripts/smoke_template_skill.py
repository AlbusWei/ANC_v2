#!/usr/bin/env python3
import argparse
from pathlib import Path

REQUIRED_FRONTMATTER = ["name:", "description:", "license:", "compatibility:"]
REQUIRED_BODY = [
    "## Capability Contract (Machine-Readable)",
    "## Input Contract",
    "## Output Contract",
    "## Execution Steps",
    "## Fail-Closed Rules",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke check template skill structure")
    parser.add_argument("--skill-file", required=True)
    parser.add_argument("--test-file", required=True)
    args = parser.parse_args()

    skill = Path(args.skill_file)
    testf = Path(args.test_file)

    if not skill.exists() or not testf.exists():
        print("fail: missing skill/test file")
        return 1

    text = skill.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED_FRONTMATTER + REQUIRED_BODY if item not in text]
    if missing:
        print("fail: missing " + ",".join(missing))
        return 1

    test_text = testf.read_text(encoding="utf-8")
    if "Priority: P0" not in test_text:
        print("fail: test file missing P0")
        return 1

    print("pass: template structure valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
