# ANC v2 流程架构（SSOT-Process）

最后更新：2026-02-20  
版本：2.1.0-alpha

> 本文档定义 ANC v2 的流程原语、实例治理、调度协议、门禁规则与证据规范。

## 1. 目标与边界

流程架构保障：

1. 反身自开发/自进化可被执行、追踪与恢复。
2. Objective/Spec/Test 被流程化为硬门禁。
3. 多 Agent 协作在失败场景仍可回退与审计。

## 2. 递归流程模型（P1-P6）

P1-P6 是流程设计抽象层，支持 top-down 建模：

1. P1 企业价值链流程
2. P2 领域价值流流程
3. P3 产品生命周期流程
4. P4 端到端交付流程
5. P5 子流程模式
6. P6 原子流程

规则：

1. 允许同层流程引用与组合。
2. 任一流程可组合子流程。
3. 禁止无终止条件循环。
4. 递归执行采用栈帧隔离。

## 3. 原语与基本约束

### 3.1 原子流程（Atomic Process）

`Atomic = (Actor, Skill, Input, Output, SIPOC metadata)`

约束：

1. 一个原子流程只允许一个 Actor 调用一个 Skill。
2. 原子流程内部不允许嵌套子流程。
3. 任何 Skill 调用必须包装为原子流程进入 BPM。

### 3.2 复合流程（Composite Process）

1. 由多个 phase 组成。
2. 每个 phase 引用子流程（原子或复合）。
3. 支持 `sequence|condition|loop|fork_join|merge`。

## 4. 流程定义关键字段（新增）

每个 `process.json` 必须包含：

1. `process_level`（P1~P6）
2. `parent_process_id`（可空）
3. `composed_processes[]`
4. `lineage_policy`

## 5. 递归实例治理

父流程调用子流程时：

1. 创建独立子实例目录。
2. 写入 `parent_instance_id`, `lineage_ref`, `stack_depth`。
3. 子流程仅输出契约化结果给父流程。
4. stack_depth 超阈值时 Fail-Closed。

## 6. BPM 调度协议（最小字段）

### 发起请求

- process
- initiator
- objective_ref
- input_payload
- priority

### 任务分发

- instance_id
- parent_instance_id
- lineage_ref
- stack_depth
- phase_id
- actor
- skill_or_subprocess
- input_ref
- output_contract

### 完成应答

- instance_id
- lineage_ref
- stack_depth
- phase_id
- output_ref
- self_check

## 7. 证据链与目录

建议目录：

`agents/control/BPM/process_instances/<instance-id>/`

最小字段：

1. timestamp
2. actor
3. phase_id
4. input_ref
5. output_ref
6. decision
7. reason

## 8. Fail-Closed 与恢复升级

触发条件：

1. 流程定义不可解析。
2. SIPOC 缺失。
3. I/O 校验失败。
4. 关键证据缺失。
5. Objective/Spec/Test 追溯断链。
6. 递归无终止条件或 stack 深度违规。

升级链：`actor -> owner -> BPM -> admin -> human`

## 9. Canonical 路径约束

`development-process` 唯一 canonical 路径：
`processes/meta/development-process/`

`processes/development-process/` 视为 legacy。

## 10. 双主线流程

1. 内部产品孵化主线：`Objective -> Spec -> Test -> Implement -> Verify -> Lifecycle -> Release -> Evolution`
2. 外部客户交付主线：`Lead -> Discovery -> Solutioning -> Contract -> Delivery -> Acceptance -> Deployment -> Support -> Feedback`

复用规则：外部主线 `delivery-iterations` 强制复用内部开发闭环。
