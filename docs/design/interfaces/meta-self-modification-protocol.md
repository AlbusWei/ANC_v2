# 元层自修改门禁协议

> 版本: v0.1.0 | SSOT 上游: [system_overview.md](../../architecture/system_overview.md) §元层自修改

## 概述

当系统需要修改自身的创建规则（模板、流程定义、评估标准等元层资产）时，必须通过本协议定义的 7 步门禁流程。这是防止无限自引用递归和质量退化的关键机制。

## 适用范围

以下修改触发本协议：
- 修改 Agent/Skill/Process 模板
- 修改 development-process 流程定义
- 修改 llm-judge 评估标准
- 修改 Registry 字段契约
- 修改架构文档（system_overview.md 等 SSOT）

以下修改不触发本协议：
- 使用现有流程创建新的 Object 层资产
- 修改 Object 层资产的实现细节
- 更新 construction_plane.md 进度

## 7 步门禁流程

### Step 1: 变更提案

- **Actor**: 任意 Agent
- **输出**: 变更提案文档（描述、动机、影响范围）

### Step 2: 影响分析

- **Actor**: architect
- **Skill**: impact-analyzer
- **输出**: 影响分析报告（受影响资产清单、风险评估）

### Step 3: 测试基线建立

- **Actor**: qa
- **Skill**: regression-runner
- **输出**: 当前元层资产的测试基线快照

### Step 4: admin 审批

- **Actor**: admin
- **输入**: 变更提案 + 影响分析
- **输出**: 批准/拒绝决策 + 原因

### Step 5: 实现变更

- **Actor**: kernel-dev
- **前置**: Step 4 批准
- **输出**: 修改后的元层资产

### Step 6: 回归验证

- **Actor**: qa
- **Skill**: regression-runner, llm-judge
- **输出**: 回归测试报告（与 Step 3 基线对比）

### Step 7: 发布与注册

- **Actor**: hr
- **前置**: Step 6 回归通过
- **输出**: 更新后的 Registry 条目、版本号递增

## Fail-Closed 触发

| 条件 | 处理 |
|---|---|
| 影响分析发现高风险 | 暂停，需 admin 额外评审 |
| admin 拒绝 | 终止，记录拒绝原因 |
| 回归测试失败 | 回滚变更，恢复基线版本 |
| 任一步骤证据缺失 | 阻止后续步骤 |

## 与普通开发流程的区别

| 维度 | 普通开发 | 元层自修改 |
|---|---|---|
| 审批 | BPM 自动编排 | 需 admin 显式批准 |
| 影响分析 | 可选 | 必须 |
| 回归测试 | 标准 | 必须含基线对比 |
| 步骤数 | 4 (Spec→Test→Impl→Verify) | 7 (含影响分析+审批+回归) |
| 回滚 | 标准 | 必须可回滚到基线 |
