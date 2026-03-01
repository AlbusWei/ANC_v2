# meta-skill-creator - Test Cases

## Objective Alignment

验证 `meta-skill-creator` 能生成可直接进入 review 门禁的技能资产，并执行历史别名软禁用策略。

## Test Cases

### TC-001: Happy Path - 生成完整技能骨架

- Type: Objective
- Priority: P0
- Input: 合法 `skill_name/layer/namespace/objective_ref/description`
- Expected:
  - 生成 `SKILL.md` 与 `TEST.md`
  - `SKILL.md` 含 Capability Contract 固定块
  - 输出包含 registry patch plan
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失 objective_ref

- Type: Objective
- Priority: P0
- Input: 缺失 `objective_ref`
- Expected: 返回码 2，阻断生成
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - 非法 skill_name

- Type: Objective
- Priority: P0
- Input: `skill_name="M3 Skill"`
- Expected: 命名校验失败并返回原因
- Evaluation Method: Exact Match

### TC-004: Traceability - test_mount 与 registry 对齐

- Type: Objective
- Priority: P1
- Input: 一次完整创建回合
- Expected: `test_doc_path` 与 registry `tests.test_doc` 可追溯一致
- Evaluation Method: Rule Match

### TC-005: 历史别名策略检查

- Type: Objective
- Priority: P1
- Input: 查询调用规范文档
- Expected: 文档明确 `meta-skill-creator` 为唯一入口，`skill-creator` 仅历史别名
- Evaluation Method: Rule Match

### TC-006: 脚手架质量检查

- Type: Objective
- Priority: P2
- Input: 运行 `scaffold_skill.py` 生成样例
- Expected: 生成物中无 `TODO` 占位且满足 review 基线字段
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [architect, qa]
- Timeout Seconds: 600
- Retry Policy: max 1
