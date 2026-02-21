# Internal Productization E2E Flow

> 版本: v0.4.0 | 层级: P4

## 目标

将内部 Agent/Skill/Process 作为“内部产品”完成从需求到上线再到演化的完整闭环。

## 定位

参考实现（reference example），用于说明开发闭环标准如何映射到具体流程；不作为规范真相源。

## 规范绑定

1. 义务模型与触发规则来源：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/development-loop-core-standard.md`
2. 建议流程类型：`dev.internal-productization`

## 阶段

1. objective-intake
2. spec-authoring
3. quality-gate-preparation
4. implementation-execution
5. quality-gate-evaluation
6. lifecycle-review
7. release-packaging
8. evolution-feedback

## 阶段到义务映射（示例）

| 阶段 | Obligation |
|---|---|
| objective-intake | O1 Objective |
| spec-authoring | O2 Spec |
| quality-gate-preparation | O3 Test |
| implementation-execution | O4 Implement |
| quality-gate-evaluation | O5 Verify |
| lifecycle-review | O6 Lifecycle |
| release-packaging | O7 Release |
| evolution-feedback | O8 Evolution |

## 阶段到原子流程映射

| 阶段 | 原子流程 |
|---|---|
| objective-intake | AP-001, AP-002, AP-003 |
| spec-authoring | AP-004 |
| quality-gate-preparation | AP-005, AP-018, AP-019 |
| implementation-execution | AP-006 |
| quality-gate-evaluation | AP-007, AP-008, AP-009, AP-020 |
| lifecycle-review | AP-010, AP-011 |
| release-packaging | AP-012 |
| evolution-feedback | AP-013, AP-014, AP-015, AP-017 |

## 验收

- [ ] 每阶段有 owner 和证据路径
- [ ] 生命周期状态可进入 review 与 active
- [ ] 回归测试失败时自动阻断发布

## 复合流程约束

1. `quality-gate-preparation` 之后必须先经过 `implementation-execution` 才能进入 `quality-gate-evaluation`。
2. `quality-gate-evaluation` 出现 `hold` 必须转入 `/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`。
3. 质量门禁复用文档：
   - `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-preparation-process.md`
   - `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-evaluation-process.md`
