# ANC v2 术语表

最后更新：2026-02-21

> 本文件定义 ANC 关键术语，避免协作歧义。

| 术语 | 英文 | 定义 |
|---|---|---|
| 原子流程 | Atomic Process | 最小不可再分流程单元，一个 Actor 调用一个 Skill 完成一个任务。 |
| 复合流程 | Composite Process | 由多个 Phase 构成的流程，每个 Phase 引用子流程。 |
| Actor | Actor | 流程阶段的执行者，可为 Agent 或人类。 |
| BPM | Business Process Manager | 控制层流程引擎，负责调度、状态、证据、恢复。 |
| 因果驱动链 | Causal Drive Chain | `Objective -> Spec -> Test -> Development`。 |
| 施工平面 | Construction Plane | 全体协作者共享的项目状态与计划视图。 |
| 内部产品 | Internal Product | Agent、Skill、Process 的统称。 |
| 元层 | Meta Layer | 用于开发/治理其他内部产品的层。 |
| 对象层 | Object Layer | 面向业务交付的层。 |
| Objective | Objective | 目标定义，回答“为什么做、做到什么程度”。 |
| Spec | Specification | Objective 的形式化表达，定义边界与约束。 |
| Test | Test | Spec 的可验证镜像，验证目标达成。 |
| SSOT | Single Source of Truth | 唯一信源文档。 |
| SIPOC | SIPOC | Supplier/Input/Process/Output/Client 的流程描述框架。 |
| 证据链 | Evidence Chain | 可审计的输入、输出、执行日志与裁决记录。 |
| 规范触发包 | Canonical Trigger Envelope | 触发输入标准化后的统一结构，供匹配、去重、调度复用。 |
| 去重账本 | Dedupe Ledger | 记录去重键、去重判定与冲突处理结果的审计条目集合。 |
| 去重策略引用 | Dedupe Policy Ref (`dedupe_policy_ref`) | 指向去重策略定义的引用，约束主键/回退键构造与冲突处理。 |
| 补跑策略引用 | Catchup Policy Ref (`catchup_policy_ref`) | 指向补跑策略定义的引用，用于动态计算补跑窗口与升级条件。 |
| 时间桶策略 | Time Bucket Strategy | 将事件时间归并为动态时间桶的策略，用于回退语义去重与窗口估计。 |
| 递归谱系引用 | Lineage Ref (`lineage_ref`) | 递归/子流程实例的谱系标识，用于追溯 parent-child 调用链。 |
| 触发运行时监督模式 | Trigger Runtime Supervisor | 可选 P5 路由模式，根据触发类型分发到对应 P4 运行流程。 |
| 运行策略校准 | Runtime Policy Calibration | 面向后验运营分析的 P5 治理流程，用于形成策略调参提案与决策记录。 |
| 栈帧隔离 | Stack Frame Isolation | 子流程独立实例运行，继承权限但隔离执行上下文。 |
| Fail-Closed | Fail-Closed | 证据不足或协议错误时默认失败并回退。 |
| LLM Judge | LLM-as-Judge | 使用大模型对输出进行目标达成度判定的评测方法。 |
