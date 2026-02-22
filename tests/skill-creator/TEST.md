# skill-creator - Test Cases

## Objective Alignment

验证 `skill-creator` 可生成符合 ANC 标准且可推进生命周期的技能资产。

## Test Cases

### TC-001: Happy Path - 生成完整技能骨架

- Type: Objective
- Priority: P0
- Input: 合法 `skill_name/objective_ref/scope/constraints`
- Expected:
  - 生成 `SKILL.md` 与 `TEST.md`
  - frontmatter 含 `name/description/license/compatibility`
  - Capability Contract 字段完整
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 关键输入缺失

- Type: Objective
- Priority: P0
- Input: 缺失 `objective_ref` 或非法 `skill_name`
- Expected:
  - 返回缺失字段错误
  - 不推进生命周期
- Evaluation Method: Exact Match

### TC-003: Traceability - registry 与证据闭环

- Type: Objective
- Priority: P0
- Input: 一次完整 skill 创建回合
- Expected:
  - `test_mount` 与 registry tests 对齐
  - review/smoke evidence 可追溯
- Evaluation Method: Rule Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [architect, qa]
- Timeout Seconds: 600
- Retry Policy: max 1
