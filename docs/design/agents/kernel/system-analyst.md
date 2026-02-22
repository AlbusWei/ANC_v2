# System Analyst Agent 详细设计

> 版本: v0.4.0 | agent_id: system-analyst | 层级: kernel | 权限: system-analysis-governance | 生命周期: review（P1 最小可运行）

## 1. 角色定位与治理目标

- **定位**: BPM/architect 的系统级分析节点，负责接收 role handoff，输出结构化诊断摘要（digest）。
- **owner**: admin
- **权限**: `system-analysis-governance`（只读证据 + 产出分析结论，不含执行写权限）。
- **P1 目标**:
  1. 可接收 `role-handoff-protocol` 交接包。
  2. 可产出可机读、可追溯、可回放的结构化 digest。
  3. 证据不足时拒绝输出结论并生成可审计拒绝记录。

## 2. 最小输入契约（handoff_in）

### 2.1 协议来源

- 协议基线: `docs/design/interfaces/role-handoff-protocol.md`
- BPM 调度约束: `docs/design/interfaces/bpm-actor-protocol.md`

### 2.2 必填字段

1. `instance_id`
2. `parent_instance_id`（无父实例时可为 `null`，但字段必须存在）
3. `lineage_ref`
4. `stack_depth`
5. `phase_id`
6. `objective_ref`
7. `input_ref`
8. `output_ref`
9. `output_contract`
10. `from_role`
11. `to_role`（必须等于 `system-analyst`）
12. `acceptance_criteria`
13. `deadline`
14. `risk_notes`
15. `evidence_ref`（证据索引文件路径，索引内需包含可达证据列表）

### 2.3 输入校验规则（Fail-Closed）

1. 任一必填字段缺失或为空，拒收。
2. `to_role != system-analyst`，拒收。
3. `evidence_ref` 不可达，或索引内证据为空，拒收。
4. `objective_ref` 不可追溯到仓库内文档引用，拒收。
5. `stack_depth` 与 `lineage_ref` 格式不一致，拒收。

## 3. 最小输出契约（digest_out / reject_out）

### 3.1 成功输出（digest_out）

成功时必须产出 `architecture_feedback_digest_ref`，结构如下：

```json
{
  "digest_id": "anl-<timestamp>-<short_hash>",
  "instance_id": "string",
  "objective_ref": "string",
  "source_handoff_ref": "string",
  "summary": "string",
  "findings": [
    {
      "signal": "string",
      "impact": "string",
      "confidence": "low|medium|high",
      "evidence_refs": ["string"]
    }
  ],
  "risk_level": "low|medium|high",
  "recommendations": [
    {
      "action": "string",
      "target_role": "architect|bpm|admin",
      "requires_decision": true
    }
  ],
  "generated_at": "ISO8601"
}
```

### 3.2 拒绝输出（reject_out）

证据不足或契约不满足时必须产出拒绝记录，且不得输出结论性 digest：

```json
{
  "status": "rejected",
  "reason_code": "handoff_contract_violation|evidence_insufficient|lineage_mismatch",
  "instance_id": "string",
  "missing_fields": ["string"],
  "missing_evidence_refs": ["string"],
  "required_actions": ["补齐证据索引", "修复handoff字段"],
  "auditable_ref": "string",
  "generated_at": "ISO8601"
}
```

## 4. Handoff 接口与拒绝路径

### 4.1 接收入口

- `from_role`: `bpm` 或 `architect`
- `to_role`: `system-analyst`
- `output_contract`: `system-analyst.digest.v1`

### 4.2 正常路径

1. 接收 handoff 包并执行字段/证据校验。
2. 校验通过后读取 `evidence_ref` 指向的证据索引。
3. 归纳 `summary + findings + recommendations`。
4. 输出 `architecture_feedback_digest_ref`，并回传 completion 给 BPM/architect。

### 4.3 拒绝路径（Fail-Closed）

1. 校验失败立即返回 `reject_out`。
2. 记录 `reason_code`、缺失字段、缺失证据与补救动作。
3. 不允许“推测性补全”或“无证据结论”。

## 5. 最小权限边界

| 能力 | 允许 | 禁止 |
|---|---|---|
| 读取证据文件 | 是（仅仓库内证据路径） | 读取未授权外部系统 |
| 生成分析工件 | 是（digest/reject） | 直接修改流程状态 |
| 调度行为 | 可建议下一步目标角色 | 直接调用调度 override / 强制推进 |
| 配置变更 | 否 | 任何 `config.patch` / 写配置行为 |
| 生命周期审批 | 否 | 直接审批 `review->active` |

## 6. 参与流程与协作边界

| process_id | 角色 | 说明 |
|---|---|---|
| runtime-policy-calibration | 主责分析节点 | 基于运行证据输出校准建议 |
| construction-plane-governance | 巡检输入提供方 | 仅提供诊断输入，不作裁决 |
| escalation | 分析支撑节点 | 提供证据化诊断，升级决策由 admin/bpm 负责 |

边界声明：

1. `system-analyst` 不负责架构原则裁决（由 `architect` 负责）。
2. `system-analyst` 不负责发布/配置写操作（由 `bpm/admin` 负责）。
3. `system-analyst` 不负责实现修复（由 `kernel-dev` 或相应执行角色负责）。

## 7. 测试挂载（P1）

- 用例文档: `tests/m2-bpm-runtime/TC-ANL.md`
- 执行入口: `tests/m2-bpm-runtime/run_tc_anl.py`
- 证据目录: `docs/design/modules/evidence/bpm-runtime/w4_system_analyst_cases/`
- 汇总报告: `docs/design/modules/evidence/bpm-runtime/w4_tc_anl_report.json`

## 8. DoD 对齐（本回合）

1. `TC-ANL-001`: 能接收 handoff 并产出结构化 digest。
2. `TC-ANL-002`: 证据不足时拒绝输出且拒绝记录可审计。
3. agent doc + inventory + registry 三方一致，且通过 `registry_contract_tool.py verify`。
