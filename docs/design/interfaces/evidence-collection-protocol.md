# 证据采集协议

> 版本: v0.2.0 | SSOT 上游: [process_architecture.md](../../architecture/process_architecture.md) §证据链

## 概述

定义流程执行过程中证据的采集、存储和校验规则。

## 采集时机

每个流程阶段必须在以下时间点采集证据：
1. **阶段开始**: 记录 input_ref, actor, timestamp
2. **阶段结束**: 记录 output_ref, decision, reason, timestamp
3. **运行中（仅长任务/hold 场景）**: 记录活性快照与无进展窗口评估

## 采集格式

### 阶段日志 (log.md)

```markdown
# Phase {phase_id}: {phase_name}

## 执行信息
- Actor: {agent_id}
- Skill: {skill_id}
- 开始时间: {ISO8601}
- 结束时间: {ISO8601}

## 输入
- 输入引用: {input_ref}

## 输出
- 输出引用: {output_ref}

## 判定
- 决策: {pass|fail|hold|retry|debug|continue|test_invalid|skip}
- 原因: {reason}
```

### 阶段输入/输出 (input.md / output.md)

内容格式由具体 Skill 定义，但必须包含：
- 文档标题
- 来源引用（从哪个阶段/文档获取）
- 实际内容

### 活性快照（liveness.json，可选）

当阶段进入长时运行或 hold 治理时，必须额外记录：

- `progress_signals_ref`
- `no_progress_duration_seconds`
- `no_progress_window_seconds`
- `termination_rule_ref`

## 存储规则

### 目录结构

```
process_instances/{instance_id}/
  context.json
  p{n}-{phase_name}/
    input.md
    output.md
    log.md
```

### 不可变性

- 证据一旦写入不可修改（append-only）
- 重试产生新的证据记录，不覆盖旧记录
- 归档后的证据目录为只读

## 校验规则

| 校验项 | 条件 | 违反后果 |
|---|---|---|
| 证据完整性 | 每阶段有 input.md + output.md + log.md | Fail-Closed |
| 时间连续性 | 阶段 N+1 开始时间 >= 阶段 N 结束时间 | 警告 |
| Actor 一致性 | log.md 中 Actor 与 process.json 定义一致 | Fail-Closed |
| 引用可达性 | input_ref/output_ref 指向的文件存在 | Fail-Closed |
| 活性窗口合规 | hold 场景下 `no_progress_window_seconds >= 900` 且有证据来源 | Fail-Closed |
