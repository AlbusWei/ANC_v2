# ANC v2 流程架构（SSOT-Process）

最后更新：2026-02-24  
版本：2.2.0-alpha

> 本文档定义 ANC v2 的流程原语、实例治理、调度协议、门禁规则与证据规范。

## 1. 目标与边界

目标：

本体系是AI Native Company能够实现其愿景的核心模块。
我们希望能够将企业的业务价值创造过程，转化为被形式定义的、可被执行、追踪与恢复的、稳定流程实例。
则我们可以通过本流程体系，模拟一切企业业务体系，实现AI托管的全自动价值创造。
所需要模拟的业务流程包括但不限于：
1. 产品生命周期管理（PLM）
2. 需求管理（RM）
3. 项目管理（PM）
4. 测试管理（TM）
5. 部署管理（DM）
6. 运维管理（OM）
7. 客户服务管理（CSM）
8. 销售管理（SM）
9. 采购管理（PM）
10. 资金管理（FM）
11. 风险管理（RM）
12. 合规管理（CM）
……


流程架构保障：

1. 反身自开发/自进化可被执行、追踪与恢复。
2. `Objective -> Spec -> Test -> Development` 被流程化为硬门禁。
3. 多 Agent 协作在失败场景仍可回退与审计。

### 1.1 设计表达准则（质胜于形）

1. 流程文档首先回答“该流程在系统中为何存在”，再描述字段与协议细节。
2. `流程目标` 必须体现系统定位、问题定义、上下游价值，不得使用模板化口号替代设计意图。
3. `协作编排原则` 必须是流程特异化规则，能够解释该流程如何保障主线目标达成。
4. 若文档仅满足格式/契约但无法指导真实协作执行，按设计无效处理并返工。

## 2. 递归流程模型（P1-P6）

P1-P6 是流程设计抽象层，支持 top-down 建模：

1. P1 企业价值链流程
2. P2 领域价值流流程
3. P3 单一业务模块的全流程集合（portfolio），如产品生命周期管理流程
4. P4 可以实现端到端价值交付的完整流程
5. P5 子流程模式，可复用的、有一定整体性的任务序列，如产品生命周期管理中的需求分析、产品设计、开发、测试、部署等阶段的子流程。
6. P6 原子流程，某角色执行某具体任务（技能），如测试流程中的测试用例写作、测试执行等。

P4是我们常识中的“流程/SOP”所处的位置，往往可以完成一件用户可见的工作、带来一定价值，比如发布某个产品的一个版本更新到线上；针对某个采购需求进行供应商调研并产出报告；进行一周的retrospective、产出复盘报告……
P3往往就是一系列流程的portfolio，支撑某个具体的业务场景，比如内部产品的生命周期管理，实际上涉及许多相对独立的SOP，而不一定串行执行，比如需求分析和retrospective是周期性触发的流程，而产品研发流程是需要主动触发的（比如确定了一个研发计划后）。所以P3及以上的流程不会作为一个可执行资产注册在注册表里，但是会作为知识文档存在，指导一个业务线条的owner如何管理其日常工作，并确定可以被相关角色频繁阅读。

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

### 3.1.1 临时 AP 语法糖（inline_ap）

> 目标：在不破坏 AP 语义的前提下，支持“流程内临时定义 AP”，减少同 Actor 场景的递归栈开销。

1. `phase.target_type` 统一使用 `subprocess`。
2. 当 `phase.target_id` 命中 `process_registry.process_id` 时，按普通子流程调度。
3. 当 `phase.target_id` 未命中 `process_registry` 时，必须声明 `phase.inline_ap`：
   - `ap_id`（必须等于 `target_id`）
   - `skill_id`（必须命中 `skill_registry.skill_id`）
   - `actor`
   - `pierce_allowed`（布尔）
4. 当 `inline_ap.pierce_allowed=true` 且 `inline_ap.actor == phase.actor` 时，允许“同 Actor 穿透执行”（不新增递归栈帧）。
5. 当 Actor 不同或不满足穿透条件时，BPM 必须回退到标准子实例调度路径。

### 3.2 复合流程（Composite Process）

1. 由多个 phase 组成。
2. 每个 phase 引用子流程（原子或复合）。
3. 支持 `sequence|condition|loop|fork_join|merge`。

## 4. 流程定义关键字段

每个 `process.json` 必须包含：

1. `process_level`（P1~P6）
2. `parent_process_id`（可空）
3. `composed_processes[]`
4. `lineage_policy`
5. `phases[].target_type`
6. `phases[].target_id`
7. `phases[].requires_spec`
8. `collaboration_policy`（分层条件字段）

`collaboration_policy` 约束：

1. `P4` 流程必须声明。
2. `P5/P6` 若存在多 Actor 强协作，也必须声明。
3. 最小字段：`mode`、`dispatch_runtime`、`session_reset`。

## 5. 递归实例治理

父流程调用子流程时：

1. 创建独立子实例目录。
2. 写入 `parent_instance_id`, `lineage_ref`, `stack_depth`。
3. 子流程仅输出契约化结果给父流程。
4. `stack_depth` 超阈值时 Fail-Closed。

## 6. BPM 调度协议（Canonical）

### BPM Protocol Canonical Schema (Machine-Readable)

```yaml
contract_version: 0.4.0
task_dispatch:
  required:
    - instance_id
    - phase_id
    - actor
    - target_type
    - target_id
    - input_ref
    - objective_ref
    - output_contract
    - lineage_ref
    - stack_depth
    - process_version
    - process_level
    - session_binding
    - evidence_dir
  optional:
    - parent_instance_id
    - spec_ref
    - constraints
  constraints:
    target_type_enum: [subprocess]
    target_id_registry_binding:
      subprocess: shared/registry/process_registry.json#entries[].process_id
      inline_ap: phases[].inline_ap.ap_id
    inline_ap_required_when: phase.target_type == subprocess && target_id not in process_registry
    inline_ap_required_fields: [ap_id, skill_id, actor, pierce_allowed]
    inline_ap_skill_binding: shared/registry/skill_registry.json#entries[].skill_id
    inline_ap_pierce_rule: inline_ap.pierce_allowed=true -> inline_ap.actor == phase.actor
    output_contract_format: contract_ref
    spec_ref_required_when: phase.requires_spec == true
    legacy_aliases_forbidden:
      - skill
      - skill_or_process
      - skill_or_subprocess
task_completion:
  required:
    - instance_id
    - phase_id
    - actor
    - lineage_ref
    - stack_depth
    - session_id
    - output_ref
    - self_check
    - evidence_ref
    - status
  self_check_required:
    - decision
    - reason
    - rule_refs
  constraints:
    status_enum: [completed, failed]
    rule_refs_format: repo_relative_path#anchor
lineage:
  recursive_trigger: parent_instance_id exists
  recursive_requires:
    - instance_id
    - parent_instance_id
    - lineage_ref
    - stack_depth
    - session_binding
  root_stack_depth: 0
```

### 任务分发（Dispatch）

1. `target_type` 只允许 `subprocess`。
2. `target_id` 必须满足二选一：命中 `process_registry.process_id`，或命中 `inline_ap.ap_id`。
3. 采用 `inline_ap` 时，`inline_ap.skill_id` 必须命中 `skill_registry.skill_id`；这种情况意味着，该phase的执行者和当前流程的执行者是同一个人，所以可以不新建会话直接穿透执行所包装的技能。
4. `output_contract` 使用 `contract_ref`（稳定 ID 或 `repo_relative_path#anchor`）。
5. 当 `phase.requires_spec=true` 时，`spec_ref` 必填。
6. `session_binding.session_id` 必须随调度显式映射到 OpenClaw `--session-id`。

### 6.1 phase 输入拼接与跨 phase 交接规则

> 目标：保证“多 agent 多会话协作”在自然语言主导下仍有稳定交接骨架。

1. BPM 在分发前必须组装 `dispatch_context`，至少包含：
   - phase 目的（`phase_purpose`）、完成标准（`done_definition`）、交接要求（`handoff_note`）
   - 本 phase 输入引用（`input_ref`，可为多引用列表）
   - 上游交接摘要（如上一阶段输出引用与关键结论）
2. phase 输入拼接优先级：
   - 显式输入（上级流程/编排器提供的输入引用）
   - 父实例最近可用输出引用
   - `requires_spec=true` 时的 `spec_ref`
3. BPM 发给 Actor 的消息应优先采用自然语言任务描述，但必须显式附带输入引用与完成标准，禁止只给“执行 pX”。
4. phase 完成后，Actor 至少回填：`output_ref`、`self_check.decision`、`self_check.reason`；下一阶段只消费可追溯引用，不消费隐式会话记忆。
5. 若输入引用缺失、上游输出不可达或交接语义不完整，按 Fail-Closed 处理，不得静默跳过。

### 完成应答（Completion）

1. `self_check` 必须包含 `decision/reason/rule_refs`。
2. `rule_refs` 必须是 `repo_relative_path#anchor`。
3. 旧别名字段立即失效，不保留兼容窗口。

## 7. 证据链与目录

建议目录：

`agents/control/BPM/process_instances/<instance-id>/`

最小字段：

1. `timestamp`
2. `actor`
3. `phase_id`
4. `input_ref`
5. `output_ref`
6. `decision`
7. `reason`

## 8. Fail-Closed 与恢复升级

触发条件：

1. 流程定义不可解析。
2. SIPOC 缺失。
3. I/O 校验失败。
4. 关键证据缺失。
5. Objective/Spec/Test 追溯断链。
6. 递归无终止条件或 `stack_depth` 违规。
7. 协议字段与 canonical schema 不一致。

升级链：`actor -> owner -> BPM -> admin -> human`

## 9. Canonical 路径约束

`development-process` 唯一 canonical 路径：
`processes/meta/development-process/`

`processes/development-process/` 已退役并从运行资产中移除（仅保留历史提交追溯）。

## 10. 双主线流程

1. 内部产品孵化主线：`Objective -> Spec -> Test -> Implement -> Verify -> Lifecycle -> Release -> Evolution`
2. 外部客户交付主线：`Lead -> Discovery -> Solutioning -> Contract -> Delivery -> Acceptance -> Deployment -> Support -> Feedback`

复用规则：外部主线 `delivery-iterations` 强制复用内部开发闭环。
