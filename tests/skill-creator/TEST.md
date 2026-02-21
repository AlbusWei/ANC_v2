# skill-creator - Test Cases

## Objective Alignment

验证 `skill-creator` 是否能在 Phase 0.5 生成可注册、可测试的 Skill 资产。

## Test Cases

### TC-001: 创建新技能资产

- Type: Objective
- Priority: P0
- Input:
  - skill_name: `example-skill`
  - objective_ref: `obj-example-skill`
  - scope: 创建文档型技能
  - constraints: 仅允许 Read/Write/Bash
- Expected:
  - 生成 `skills/example-skill/SKILL.md`
  - 生成 `tests/example-skill/TEST.md`
  - 生成 `skill_registry` 条目草案
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: skill-creator must output traceable skill assets
  - spec_ref: `skills/skill-creator/SKILL.md`
  - expected_conditions:
    - required files exist
    - frontmatter contains name/description/license/compatibility
    - test path is provided
  - actual_output_ref: `artifacts/skill-creator/tc-001-output.md`

### TC-002: 输入缺失时 Fail-Closed

- Type: Objective
- Priority: P0
- Input:
  - skill_name: `broken-skill`
  - objective_ref: ``
  - scope: 未提供
- Expected:
  - 返回缺失字段错误
  - 不创建不完整的 Skill 目录
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 9
- Judge Perspectives: default
- Timeout Seconds: 600
- Retry Policy: max 1
