# 证据链 Schema

> 版本: v0.2.0 | SSOT 上游: [process_architecture.md](../../architecture/process_architecture.md) §证据链

## 概述

证据链是流程执行的可审计记录。每个流程阶段必须产出完整的证据记录。

## 阶段证据记录 Schema

```json
{
  "timestamp": "string (ISO8601, required)",
  "actor": "string (agent_id, required)",
  "phase_id": "string (p1|p2|..., required)",
  "input_ref": "string (输入文件路径, required)",
  "output_ref": "string (输出文件路径, required)",
  "decision": "string (pass|fail|hold|retry|debug|continue|test_invalid|skip, required)",
  "reason": "string (决策原因, required)",
  "runtime_gate_state": "string (pass|fail|hold|test_invalid, optional)",
  "liveness_snapshot_ref": "string (optional)"
}
```

### 字段约束

| 字段 | 约束 | 说明 |
|---|---|---|
| timestamp | ISO8601 格式 | 阶段完成时间 |
| actor | 已注册 agent_id | 执行者 |
| phase_id | 匹配 process.json 定义 | 阶段标识 |
| input_ref | 文件路径存在 | 输入文档引用 |
| output_ref | 文件路径存在 | 输出文档引用 |
| decision | pass/fail/hold/retry/debug/continue/test_invalid/skip | 阶段判定 |
| reason | 非空字符串 | 判定原因 |
| runtime_gate_state | pass/fail/hold/test_invalid（可选） | 门禁运行态 |
| liveness_snapshot_ref | 文件路径存在（可选） | 活性快照 |

## 证据目录结构

```
process_instances/{instance_id}/
  context.json          # 实例上下文
  p1-{phase_name}/
    input.md            # 阶段输入
    output.md           # 阶段输出
    log.md              # 阶段日志（含证据记录）
  p2-{phase_name}/
    ...
  artifacts/            # 流程产物
    spec.md
    test-plan.md
    ...
```

## LLM-Judge 评估证据 Schema

```json
{
  "eval_type": "string (objective|subjective, required)",
  "objective_ref": "string (required)",
  "spec_ref": "string (required for objective)",
  "actual_output_ref": "string (required)",
  "verdict": {
    "pass": "boolean (required)",
    "confidence": "number (0.0-1.0, required)",
    "remarks": "string (required)",
    "suggestions": ["string"]
  },
  "timestamp": "string (ISO8601)",
  "judge_model": "string (LLM 模型标识)"
}
```

## 活性快照 Schema（hold/长任务）

```json
{
  "timestamp": "string (ISO8601, required)",
  "progress_signals_ref": "string (required)",
  "no_progress_duration_seconds": "integer (>=0, required)",
  "no_progress_window_seconds": "integer (>=900, required)",
  "termination_rule_ref": "string (required)"
}
```
