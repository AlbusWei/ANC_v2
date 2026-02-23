#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LAYER_CHOICES = ("meta", "system", "business")


def validate_segment(value: str, field_name: str) -> None:
    if not NAME_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} 必须为 kebab-case：{value}")


def build_skill_markdown(
    *,
    skill_name: str,
    description: str,
    objective_ref: str,
    test_doc: str,
) -> str:
    return f"""---
name: \"{skill_name}\"
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

# {skill_name}

## Objective

围绕 `{objective_ref}` 提供可执行能力，并确保输入约束、输出契约与 Fail-Closed 行为可测试、可追溯。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新建资产 | 关键输入齐全 | 产出符合标准的技能文档与测试文档 | 关键字段缺失 |
| 重构资产 | 变更范围明确 | 更新契约并同步测试 | 约束冲突 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: {objective_ref}
input_contract:
  format: json
  required:
    - primary_input
  validation:
    - primary_input must be non-empty
output_contract:
  format: markdown_or_json
  required:
    - primary_output
  machine_judgement:
    - output includes required fields
fail_closed_rules:
  - missing required input fields
  - output contract validation failed
test_mount:
  test_doc: {test_doc}
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `primary_input` | string/object | 非空且可解析 | 空值或不可解析 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `primary_output` | string/object | 满足 output_contract 定义 | 结构化校验 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 输入缺失 | `missing_fields != []` | 阻断并返回缺失字段 | `2` |
| 契约不满足 | `contract_valid=false` | 阻断并返回失败项 | `2` |
| 运行时异常 | 未捕获异常 | 中止并输出异常摘要 | `1` |

## 运行命令

```bash
# 根据实际技能补充运行命令；无 runner 时给出文档化门禁命令。
python3 shared/registry/registry_contract_tool.py verify
```
"""


def build_test_markdown(skill_name: str) -> str:
    return f"""# {skill_name} - Test Cases

## Objective Alignment

验证 `{skill_name}` 的能力定义满足可执行、可测试与可追溯要求。

## Test Cases

### TC-001: Happy Path - 主链路通过

- Type: Objective
- Priority: P0
- Input: 合法输入
- Expected: 产出满足 output_contract
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失关键输入

- Type: Objective
- Priority: P0
- Input: 缺失 required 字段
- Expected: 阻断并返回缺失字段
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - 约束冲突

- Type: Objective
- Priority: P0
- Input: 构造约束冲突输入
- Expected: 阻断并返回冲突原因
- Evaluation Method: Rule Match

### TC-004: Traceability - 输入输出映射

- Type: Objective
- Priority: P1
- Input: 合法输入
- Expected: 输出字段可回链到输入与契约
- Evaluation Method: Rule Match

### TC-005: 异常路径恢复

- Type: Objective
- Priority: P1
- Input: 部分可恢复异常
- Expected: 输出恢复/回退建议
- Evaluation Method: Human Review

### TC-006: 文档门禁一致性

- Type: Objective
- Priority: P2
- Input: 完整执行结果
- Expected: test_mount、registry tests 与文档一致
- Evaluation Method: Rule Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [architect, qa]
- Timeout Seconds: 600
- Retry Policy: max 1
"""


def write_text(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def scaffold_skill(
    *,
    skill_name: str,
    layer: str,
    namespace: str,
    objective_ref: str,
    description: str,
    output_root: str,
    force: bool = False,
) -> Dict[str, str]:
    validate_segment(skill_name, "skill_name")
    validate_segment(namespace, "namespace")
    if layer not in LAYER_CHOICES:
        raise ValueError(f"layer 必须为 {LAYER_CHOICES} 之一：{layer}")
    if not objective_ref.strip():
        raise ValueError("objective_ref 不能为空")

    output_root_path = Path(output_root)
    if output_root_path.is_absolute():
        raise ValueError("output_root 必须使用仓库相对路径")

    skill_dir = output_root_path / layer / namespace / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    test_doc = (output_root_path / layer / namespace / skill_name / "TEST.md").as_posix()
    skill_md = skill_dir / "SKILL.md"
    test_md = skill_dir / "TEST.md"

    skill_written = write_text(
        skill_md,
        build_skill_markdown(
            skill_name=skill_name,
            description=description,
            objective_ref=objective_ref,
            test_doc=test_doc,
        ),
        force=force,
    )
    test_written = write_text(test_md, build_test_markdown(skill_name), force=force)

    return {
        "skill_dir": skill_dir.as_posix(),
        "skill_md": skill_md.as_posix(),
        "test_md": test_md.as_posix(),
        "test_doc": test_doc,
        "skill_written": str(skill_written).lower(),
        "test_written": str(test_written).lower(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold ANC skill skeleton")
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--layer", required=True, choices=LAYER_CHOICES)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--objective-ref", required=True)
    parser.add_argument("--description", default="由 meta-skill-creator 生成的技能骨架")
    parser.add_argument("--output-root", default="skills")
    parser.add_argument("--force", action="store_true", help="覆盖已有 SKILL.md/TEST.md")
    args = parser.parse_args()

    result = scaffold_skill(
        skill_name=args.skill_name,
        layer=args.layer,
        namespace=args.namespace,
        objective_ref=args.objective_ref,
        description=args.description,
        output_root=args.output_root,
        force=args.force,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
