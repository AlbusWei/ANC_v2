# agent-creator - Test Cases

## Objective Alignment

验证 Agent 资产创建流程能够输出可注册、可治理、可追溯的资产，并在输入不完整时严格 Fail-Closed。

## Test Cases

### TC-001: Happy Path - 生成完整 Agent 资产计划

- Type: Objective
- Priority: P0
- Input: 合法 `agent_id/role_scope/interfaces/owner`
- Expected: 输出 `agent_doc_path/tools_doc_path/registry_patch_plan`，且字段完整
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失 owner

- Type: Objective
- Priority: P0
- Input: `owner` 为空
- Expected: 返回 `missing_fields=[owner]`，进程返回码为 2
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - interfaces 缺 protocol_ref

- Type: Objective
- Priority: P0
- Input: `interfaces` 项中缺 `protocol_ref`
- Expected: 返回 invalid protocol 错误并阻断输出
- Evaluation Method: Exact Match

### TC-004: Traceability - registry patch 与 test_mount 对齐

- Type: Objective
- Priority: P1
- Input: 一次完整创建输入
- Expected: 输出中的 registry patch `tests.test_doc` 与 skill `test_mount` 一致
- Evaluation Method: Rule Match

### TC-005: 边界检查 - 非法 agent_id 命名

- Type: Objective
- Priority: P1
- Input: `agent_id="M3-Agent"`
- Expected: 命名校验失败，返回码为 2
- Evaluation Method: Exact Match

### TC-006: 报告产出 - --report 输出结构

- Type: Objective
- Priority: P2
- Input: 合法输入 + `--report report.json`
- Expected: 报告含 `runner/decision/checked_fields` 字段
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [architect]
- Timeout Seconds: 600
- Retry Policy: max 1
