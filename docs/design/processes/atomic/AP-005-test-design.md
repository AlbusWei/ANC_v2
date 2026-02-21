# AP-005 Test Design

> 版本: v0.4.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: meta.qa.test-designer
- Input:
  - objective_ref
  - spec_ref
  - risk_focus（必须包含 P0 场景）
  - test_doc_ref（`TEST.md`）
- Output:
  - test_plan_ref
  - test_cases_ref
  - risk_coverage_ref
- Scope boundary:
  - AP-005 仅负责测试设计
  - 编译与 profile 绑定由 AP-018/AP-019 负责
- Fail-Closed:
  - P0 用例缺失时阻断实现
  - 测试设计与 objective/spec 不可追溯时失败
- Evidence:
  - test_plan_ref
  - risk_coverage_ref
