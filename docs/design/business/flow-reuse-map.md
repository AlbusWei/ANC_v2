# Flow Reuse Map

> 版本: v0.3.0

## 复用矩阵

| 外部交付流程阶段 | 复用标准义务 | internal 示例映射（非强制） | 说明 |
|---|---|---|---|
| solutioning-and-estimation | O2, O3 | spec-authoring + test-design | 方案与测试可验证化 |
| delivery-iterations | O4, O5, O6, O7 | implementation + objective-evaluation + lifecycle + release | 开发、门禁与发布闭环 |
| support-and-feedback | O8 | evolution-feedback | 反馈沉淀与改进规划 |

## 规则

1. 外部流程复用必须以 `/Users/albus/MyProjects/ANC_v2/docs/design/processes/development-loop-core-standard.md` 为规范真相源。
2. internal 映射仅为示例，不构成唯一依赖。
3. 外部流程复用内部流程时不得绕过质量门禁。
4. 复用节点必须保留父子实例引用。
5. 复用失败时回退到内部流程的失败策略。
