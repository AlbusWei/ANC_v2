# System Analyst Agent 详细设计

> 版本: v1.0.0 | agent_id: system-analyst | 层级: kernel | 权限: system-analysis-governance | 生命周期: review（运行级验证完成，待 active 准入）

## 1. 角色定位与治理目标

- **定位**: BPM/architect 的系统级分析节点，负责接收 role handoff、执行证据校验并产出结构化治理摘要。
- **owner**: admin
- **权限**: `system-analysis-governance`（只读证据 + 产出分析结论，不含执行写权限）。
- **生产目标**:
  1. 可被 BPM/architect 稳定调用。
  2. 可在运行链路输出结构化 digest。
  3. 证据不足时严格 Fail-Closed 并保留可审计拒绝记录。

## 2. 绑定 Skill（bound_skills）

| skill_id | 用途 | 生命周期 |
|---|---|---|
| `sys.arch.system-feedback-digest` | 校验 handoff 与证据，生成 digest/reject 输出 | review |

## 3. 参与流程（participating_processes）

| process_id | 角色 | 说明 |
|---|---|---|
| `runtime-policy-calibration` | 主责分析节点 | 输出后验分析结论与策略提案输入 |
| `construction-plane-governance` | 巡检输入提供方 | 提供系统风险信号，不执行裁决 |
| `escalation` | 分析支撑节点 | 在升级链路提供证据化诊断 |

## 4. 最小输入契约（handoff_in）

### 4.1 协议来源

- `docs/design/interfaces/role-handoff-protocol.md`
- `docs/design/interfaces/bpm-actor-protocol.md`

### 4.2 必填字段

1. `instance_id`
2. `parent_instance_id`（允许 `null`，字段必须存在）
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
15. `evidence_ref`

### 4.3 输入校验规则（Fail-Closed）

1. 任一必填字段缺失或为空，拒收。
2. `to_role != system-analyst`，拒收。
3. `objective_ref` 不可追溯到仓库内文档路径，拒收。
4. `evidence_ref` 不可达、索引为空或索引内证据不可达，拒收。
5. `stack_depth` 与 `lineage_ref` 不一致，拒收。

## 5. 最小输出契约（digest_out / reject_out）

### 5.1 成功输出（digest_out）

```json
{
  "digest_id": "anl-<hash>",
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

### 5.2 拒绝输出（reject_out）

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

## 6. Handoff 接口与拒绝路径

### 6.1 接收入口

- `from_role`: `bpm` 或 `architect`
- `to_role`: `system-analyst`
- `output_contract`: `system-analyst.digest.v1`

### 6.2 正常路径

1. 接收 handoff 包并执行契约校验。
2. 校验通过后读取证据索引，归纳系统信号。
3. 输出 `architecture_feedback_digest_ref`，并回传 completion。

### 6.3 拒绝路径（Fail-Closed）

1. 校验失败立即返回 `reject_out`。
2. 必须记录 `reason_code/missing_fields/missing_evidence_refs`。
3. 禁止无证据结论或推测性补全。

## 7. 最小权限边界

| 能力 | 允许 | 禁止 |
|---|---|---|
| 读取证据文件 | 是（仅仓库内证据路径） | 读取未授权外部系统 |
| 生成分析工件 | 是（digest/reject） | 直接修改流程状态 |
| 调度行为 | 可建议下一步角色 | 调度 override / 强制推进 |
| 配置变更 | 否 | `config.patch` 与所有配置写操作 |
| 生命周期审批 | 否 | 直接审批 `review->active` |

## 8. 决策边界（decision_boundary）

| 决策类型 | 权限边界 |
|---|---|
| 后验信号归纳与风险分级 | 完全自主 |
| 策略变更建议 | 可提案，需 architect/admin/bpm 决策 |
| 架构原则修改 | 不可 |
| 配置写操作与发布执行 | 不可 |

## 9. Fail-Closed 行为（fail_closed_behavior）

触发即失败：

1. handoff 契约缺字段。
2. evidence 索引不可达或样本不足。
3. objective 路径不可追溯。
4. 高风险场景缺失审批链要求。

升级链：`system-analyst -> bpm -> admin`

## 10. 上下文与记忆策略

- 持久记忆目录：`agents/kernel/system-analyst/memory/`
- 运行证据目录：`docs/design/modules/evidence/bpm-runtime/`
- 跨会话传递：仅通过 digest/reject 与流程 evidence 引用，不依赖隐式会话记忆。

## 11. 测试挂载（生产）

- 用例文档: `tests/m2-bpm-runtime/TC-ANL.md`
- 执行入口: `tests/m2-bpm-runtime/run_tc_anl.py`
- 证据目录: `docs/design/modules/evidence/bpm-runtime/w5_system_analyst_prod_cases/`
- 汇总报告: `docs/design/modules/evidence/bpm-runtime/w5_tc_anl_report.json`

## 12. DoD（生产）

1. `TC-ANL-001`: handoff -> digest 成功。
2. `TC-ANL-002`: 证据不足拒绝且可审计。
3. `TC-ANL-003`: `runtime-policy-calibration` 端到端成功并产出 5 项治理输出。
4. agent/skill/process 文档 + inventory + registry 一致并通过 `registry_contract_tool.py verify`。
