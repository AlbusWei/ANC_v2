# AP-006 Implementation Execution

> 版本: v0.3.0 | 层级: P6 | 类型: 原子流程

- Actor: kernel-dev / frontend-dev / backend-dev / data-engineer
- Skill: manual-task 或实现类技能
- Input:
  - spec_ref
  - test_plan_ref
- Output:
  - implementation_ref
- Fail-Closed:
  - 实现不可追溯到 spec 时退回
- Evidence:
  - implementation_ref
- Draft manual fallback exception:
  - 新建复合流程没有适用的原子流程时， `draft` 阶段允许上层流程例外引用 AP-006 作为 manual fallback
  - 不得用于替代 AP-020 与 AP-022/AP-023/AP-025
  - 进入 `review/active` 前必须替换为语义专用 AP
