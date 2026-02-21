# 可复用流程模式

> 版本: v0.2.0

## 概述

本文档定义可在多个流程中复用的标准模式，减少流程设计的重复工作。

边界说明：

1. 本文档描述“可复用模式”，不承担流程合规判定真相源职责。
2. 开发闭环义务、条件触发与语法硬约束以 `/Users/albus/MyProjects/ANC_v2/docs/design/processes/development-loop-core-standard.md` 为准。

使用前置：

1. 先对齐 `/Users/albus/MyProjects/ANC_v2/docs/design/standards/process-definition-standard.md`。
2. 本文模式复用不得绕过 process standard 中的连续性约束与 phase 闭合约束。

## 模式 1: 因果驱动链 (Causal Drive Chain)

```
Objective → Spec → Test → Implement → Verify
```

- **适用**: 所有新建资产的开发流程
- **约束**: 不可跳步，每步产出是下步输入
- **Fail-Closed**: 任一步骤失败阻止后续步骤
- **实例**: development-process, full-development

## 模式 2: 循环重试 (Loop-on-Failure)

```
Phase N → Phase N+1 (verify)
    ↑         │ fail
    └─────────┘ (max K iterations)
```

- **适用**: 实现-验证循环
- **参数**: max_iterations (默认 2)
- **超出重试**: 升级到 owner 或 admin
- **实例**: development-process p3→p4 循环

## 模式 3: 审批门禁 (Approval Gate)

```
Request → Validate → Check Prerequisites → Approve/Reject → Execute
```

- **适用**: 生命周期转换、权限变更
- **约束**: 每步有明确的通过/拒绝条件
- **Fail-Closed**: 任一校验失败即拒绝
- **实例**: lifecycle-review, governed-config-change

## 模式 4: 升级链 (Escalation Chain)

```
Actor → Owner → BPM → Admin
```

- **适用**: 异常处理、权限不足、决策冲突
- **约束**: 每级有明确的决策权限边界
- **终止**: 任一级别解决即终止
- **实例**: escalation

## 模式 5: 基线-变更-回归 (Baseline-Change-Regression)

```
Establish Baseline → Make Change → Regression Verify
```

- **适用**: 重构、升级、配置变更
- **约束**: 基线测试必须先通过
- **Fail-Closed**: 回归测试失败则回滚变更
- **实例**: refactor, governed-config-change
