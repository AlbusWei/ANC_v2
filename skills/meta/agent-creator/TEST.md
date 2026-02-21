# agent-creator - Test Cases

## Objective Alignment

验证 Agent 资产创建流程可产出可注册、可治理工件。

## Test Cases

### TC-001: 生成 agent 资产骨架

- Type: Objective
- Priority: P0
- Input: 新 agent_id + role_scope + interfaces + owner
- Expected: 产出 agent 文档路径、TOOLS 路径与 registry patch 计划
- Evaluation Method: Human Review

### TC-002: 缺失 owner 时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: owner 为空
- Expected: 阻断产出并返回缺失字段
- Evaluation Method: Exact Match
