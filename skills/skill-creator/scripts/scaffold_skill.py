#!/usr/bin/env python3
import argparse
from pathlib import Path

SKILL_TEMPLATE = """---
name: \"{name}\"
description: \"{description}\"
license: \"Apache-2.0\"
compatibility:
  openclaw: \">=2026.2\"
  agentskills: \">=0.2\"
allowed-tools:
  - Read
  - Write
  - Bash
version: \"0.1.0\"
---

# {name}

## Objective

[Describe objective]

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: {objective_ref}
input_contract:
  format: json
  required: []
  validation: []
output_contract:
  format: json
  required: []
  machine_judgement: []
fail_closed_rules:
  - missing required input
test_mount:
  test_doc: {test_doc}
  methodology_ref: docs/architecture/test_methodology.md
```

## Input Contract

- TODO

## Output Contract

- TODO

## Execution Steps

1. TODO

## Fail-Closed Rules

- TODO
"""

TEST_TEMPLATE = """# {name} - Test Cases

## Objective Alignment

验证 {name} 的核心能力。

## Test Cases

### TC-001: Happy Path

- Type: Objective
- Priority: P0
- Input: [valid input]
- Expected: [expected output]
- Evaluation Method: Exact Match

### TC-002: Fail-Closed Path

- Type: Objective
- Priority: P0
- Input: [invalid input]
- Expected: [fail-closed outcome]
- Evaluation Method: Exact Match

### TC-003: Traceability Path

- Type: Objective
- Priority: P0
- Input: [valid input]
- Expected: [traceable evidence refs]
- Evaluation Method: Rule Match
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold ANC skill skeleton")
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--layer", required=True, choices=["meta", "system", "business"])
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--objective-ref", required=True)
    parser.add_argument("--output-root", default="skills")
    args = parser.parse_args()

    skill_dir = Path(args.output_root) / args.layer / args.namespace / args.skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    test_doc = f"skills/{args.layer}/{args.namespace}/{args.skill_name}/TEST.md"
    skill_md = skill_dir / "SKILL.md"
    test_md = skill_dir / "TEST.md"

    if not skill_md.exists():
        skill_md.write_text(
            SKILL_TEMPLATE.format(
                name=args.skill_name,
                description="TODO: describe trigger and use cases",
                objective_ref=args.objective_ref,
                test_doc=test_doc,
            ),
            encoding="utf-8",
        )

    if not test_md.exists():
        test_md.write_text(TEST_TEMPLATE.format(name=args.skill_name), encoding="utf-8")

    print(f"created={skill_dir}")
    print(f"skill_md={skill_md}")
    print(f"test_md={test_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
