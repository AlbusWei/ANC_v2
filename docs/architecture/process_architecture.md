# ANC v2 流程架构（SSOT-Process）

最后更新：2026-02-18  
版本：2.0.1-alpha

> 本文档定义 ANC v2 的流程原语、实例治理、调度协议、门禁规则与证据规范。
> 与系统 SSOT 冲突时，以 `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md` 为准。

## 1. 目标与边界

流程架构用于保障三件事：

1. 反身自开发/自进化可被执行、追踪与恢复。
2. Objective/Spec/Test 被流程化为硬门禁。
3. 多 Agent 协作在失败场景仍可回退与审计。

非目标：

1. 不替代具体业务流程设计。
2. 不定义底层 OpenClaw 实现细节。

## 2. 原语与基本约束

### 2.1 原子流程（Atomic Process）

定义：

`Atomic = (Actor, Skill, Input, Output, SIPOC metadata)`

硬约束：

1. 一个原子流程只允许一个 Actor 调用一个 Skill 完成一个任务。
2. 原子流程内部不允许嵌套子流程。
3. 任何 Skill 调用必须包装为原子流程后才能进入 BPM 编排。

### 2.2 复合流程（Composite Process）

1. 由多个 Phase 组成。
2. 每个 Phase 引用已注册的子流程（原子或复合）。
3. 支持控制结构：`sequence`, `condition`, `loop`, `fork_join`, `merge`。

## 3. SIPOC 强制规范

每个 Phase 必填：

1. Supplier：输入来源。
2. Input：输入格式与校验规则。
3. Process：执行逻辑（引用 Skill/Process）。
4. Output：输出格式与校验规则。
5. Client：输出消费方。

I/O 校验失败处理：

1. BPM 拒绝状态流转。
2. 退回到责任 Actor（或上游 Actor）修复。
3. 记录失败证据并触发重提交流程。

## 4. 流程定义模板（建议）

### 4.1 原子流程模板

```yaml
name: "spec-writing"
type: atomic
actor: "architect"
skill: "spec-writer"
sipoc:
  supplier: "requirement-intake"
  input:
    format: "markdown"
    validation: "must include objective_ref and constraints"
  process: "write spec draft"
  output:
    format: "markdown"
    validation: "must include I/O and acceptance criteria"
  client: "test-design"
```

### 4.2 复合流程模板

```yaml
name: "development-process"
type: composite
objective_ref: "obj-xxx"
phases:
  - phase_id: "p1"
    sub_process: "requirement-clarification"
    actor: "architect"
    input: {source: "request"}
    output: {target: "p2"}
    acceptance_criteria: "objective clarified"
  - phase_id: "p2"
    sub_process: "spec-writing"
    actor: "architect"
    input: {source: "p1.output"}
    output: {target: "p3"}
    acceptance_criteria: "spec complete"
control:
  mode: "sequence"
```

### 4.3 Process 目录打包规范（Agent Skills 对齐）

每个流程目录至少包含：

1. `SKILL.md`：Agent Skills 规范兼容文档（带 frontmatter）。
2. `process.json`：结构化流程定义（Phase、控制结构、I/O 约束）。
3. `PROCESS.md`：面向人类的说明文档（可选但推荐）。
4. 测试模板不放在流程目录，统一复用 `/Users/albus/MyProjects/ANC_v2/tests/template/TEST.md`。

`SKILL.md` frontmatter 至少包含：

1. `name`
2. `description`
3. `license`
4. `compatibility`

说明：BPM 执行 `process.json`，OpenClaw 技能加载识别 `SKILL.md`。
`SKILL.md` + `process.json` + `PROCESS.md` 是同一个 Process 模板包的不同视图，不是多个重复模板。

## 5. 流程实例生命周期

状态机：

`Created -> Running -> Waiting -> Completed | Failed | Cancelled -> Archived`

状态说明：

1. Created：实例已创建，待执行。
2. Running：正在执行。
3. Waiting：等待外部输入/审批/子流程回传。
4. Completed：全部阶段成功。
5. Failed：失败且不可恢复。
6. Cancelled：人工或系统主动终止。
7. Archived：归档终态。

## 6. BPM 调度协议（最小字段）

### 6.1 发起请求

```markdown
- process: <process-id>
- initiator: <actor-id>
- objective_ref: <objective-id>
- input_payload: <path-or-inline>
- priority: P0/P1/P2
```

### 6.2 任务分发

```markdown
- instance_id: <id>
- phase_id: <id>
- actor: <actor-id>
- skill_or_subprocess: <name>
- input_ref: <path>
- output_contract: <summary>
- acceptance_criteria: <summary>
- deadline: <timestamp>
```

### 6.3 完成应答

```markdown
- instance_id: <id>
- phase_id: <id>
- output_ref: <path>
- self_check: pass/fail
- notes: <summary>
```

### 6.4 OpenClaw CLI 接口映射

流程运行中常用 CLI 接口：

1. 网关状态：`openclaw health --json`
2. 查看会话：`openclaw sessions --json`
3. 发送执行消息：`openclaw agent --message \"...\"`
4. 配置读取：`openclaw config get agents.list --json`
5. 配置变更：`openclaw gateway call config.patch --params '{\"raw\":\"...\",\"baseHash\":\"...\"}' --json`

## 7. 栈帧式递归隔离

父流程调用子流程时：

1. 创建新实例目录（子栈帧）。
2. 继承权限上下文，不继承执行上下文。
3. 子流程输出经契约校验后回填父流程当前 Phase。
4. 父流程必须记录 `child_instance_id` 与 `output_ref`。

禁止：

1. 子流程直接写父流程运行态。
2. 父子实例共享同一可变 `context` 文件。

## 8. 实例目录与证据链

建议目录：

```text
/Users/albus/MyProjects/ANC_v2/agents/control/BPM/process_instances/<instance-id>/
  context.md
  state.json
  evidence/
    <phase-id>/
      input.md
      output.md
      log.md
  artifacts/
```

归档目录建议：

```text
/Users/albus/MyProjects/ANC_v2/agents/control/BPM/process_instances/archive/<instance-id>/
```

证据最小字段：

1. `timestamp`
2. `actor`
3. `phase_id`
4. `input_ref`
5. `output_ref`
6. `decision`
7. `reason`

## 9. Fail-Closed 与恢复升级

Fail-Closed 触发：

1. 流程定义不可解析。
2. Phase 缺 SIPOC 字段。
3. I/O 校验失败且无法修复。
4. 关键证据缺失。
5. Objective/Spec/Test 追溯断链。

恢复升级链：

`actor -> owner -> BPM -> admin`

处理策略：

1. 可重试错误：有限重试。
2. 不可重试错误：立即失败并回滚。
3. 超时阻塞：督办后升级。
4. 无法恢复：终止并生成迭代工单。

## 10. 三驱动门禁流程化

固定顺序：

`Objective -> Spec -> Tests -> Implement -> Verify -> Release`

阶段准入规则：

1. 无 Objective 不得写 Spec。
2. 无 Spec 不得设计正式 Test。
3. 无 Test 不得进入实现。
4. Verify 必须验证 Objective 达成，不是仅验证格式正确。
5. Release 必须双门槛通过（目标达成 + 评审通过）。

## 11. 预定义原子流程（初始化建议）

1. `manual-task`：人工 fallback。
2. `spec-writing`：编写规范。
3. `test-designing`：设计测试。
4. `llm-judging`：LLM 评估。
5. `skill-creating`：创建技能。
6. `report-generating`：生成评测报告。

## 12. 验收检查清单

流程架构合格至少满足：

1. 原子流程定义清晰且可检查。
2. 复合流程 Phase 都可追溯到注册表资产。
3. 父子流程隔离策略可执行。
4. 失败路径有明确回退与升级。
5. 证据链可定位到每个 Phase 的输入输出。

## 13. 外部参考

1. OpenClaw Gateway Configuration：https://docs.openclaw.ai/gateway/configuration
2. OpenClaw CLI：https://docs.openclaw.ai/cli/index
3. Agent Skills 规范：https://agentskills.io/specification
4. OpenClaw 接口契约（本仓库）：`/Users/albus/MyProjects/ANC_v2/docs/architecture/openclaw_interface.md`
