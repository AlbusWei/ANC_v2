# Recursive Process Architecture

> 版本: v0.2.0 | 上游: `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`

## 1. 总览

ANC v2 流程架构采用递归流程模型：流程可组合流程，直到原子流程（P6）为止。

## 2. 双主线

1. 内部产品孵化主线：`Objective -> Spec -> Test -> Implement -> Verify -> Lifecycle -> Release -> Evolution`
2. 外部客户交付主线：`Lead -> Discovery -> Solutioning -> Contract -> Delivery -> Acceptance -> Deployment -> Support -> Feedback`

## 3. P1-P6 映射

| 层级 | 职责 | 典型产物 |
|---|---|---|
| P1 | 企业级价值链 | 企业流程蓝图 |
| P2 | 领域价值流 | 领域流程地图 |
| P3 | 产品生命周期 | 生命周期流程包 |
| P4 | 端到端交付流程 | 可执行复合流程 |
| P5 | 子流程模式 | 复用流程片段 |
| P6 | 原子流程 | actor+skill 原子单元 |

## 4. 递归执行语义

1. BPM 为每个子流程创建独立实例目录。
2. `parent_instance_id`、`lineage_ref`、`stack_depth` 用于回溯递归链。
3. 父流程仅读取子流程输出契约并回填。

## 5. Fail-Closed 规则

1. 子流程输出不满足契约 -> 父流程阻断。
2. 检测到无终止条件循环 -> 实例 fail 并升级。
3. 关键证据缺失 -> 拒绝状态推进。

## 6. 验收

- [ ] P4 流程全部可追溯到 P6
- [ ] 同层组合案例存在且可解释
- [ ] 递归链上下文字段完整
