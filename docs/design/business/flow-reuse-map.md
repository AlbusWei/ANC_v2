# Flow Reuse Map

> 版本: v0.2.0

## 复用矩阵

| 外部交付流程阶段 | 复用内部孵化阶段 | 说明 |
|---|---|---|
| solutioning-and-estimation | spec-authoring + test-design | 用内部标准定义方案质量 |
| delivery-iterations | implementation + objective-evaluation + lifecycle + release | 直接复用内部开发治理闭环 |
| support-and-feedback | evolution-feedback | 复用演化分析与改进流程 |

## 规则

1. 外部流程复用内部流程时不得绕过质量门禁。
2. 复用节点必须保留父子实例引用。
3. 复用失败时回退到内部流程的失败策略。
