# Internal Productization E2E Flow

> 版本: v0.2.0 | 层级: P4

## 目标

将内部 Agent/Skill/Process 作为“内部产品”完成从需求到上线再到演化的完整闭环。

## 阶段

1. objective-intake
2. spec-authoring
3. test-design
4. implementation-execution
5. objective-evaluation
6. lifecycle-review
7. release-packaging
8. evolution-feedback

## 阶段到原子流程映射

| 阶段 | 原子流程 |
|---|---|
| objective-intake | AP-001, AP-002, AP-003 |
| spec-authoring | AP-004 |
| test-design | AP-005 |
| implementation-execution | AP-006 |
| objective-evaluation | AP-007, AP-008, AP-009 |
| lifecycle-review | AP-010, AP-011 |
| release-packaging | AP-012 |
| evolution-feedback | AP-013, AP-014, AP-015, AP-017 |

## 验收

- [ ] 每阶段有 owner 和证据路径
- [ ] 生命周期状态可进入 review 与 active
- [ ] 回归测试失败时自动阻断发布
