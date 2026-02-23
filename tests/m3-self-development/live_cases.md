# M3 Self-Development Meta 在线用例清单（Phase5）

## 1. 资产来源与生成规则

1. Skill 来源：`shared/registry/skill_registry.json` 中 `skill_id` 以 `meta.` 开头的条目。
2. Process 来源：`shared/registry/process_registry.json` 中 `skill_path` 位于 `processes/meta/` 的条目。
3. 每个资产固定 4 类场景：`HP/FC/TR/RB`。
4. Case ID 规则：
   - Skill：`MS-<PREFIX>-<SCENARIO>`
   - Process：`MP-<PREFIX>-<SCENARIO>`

## 2. Scenario 定义（统一模板）

| 场景 | 含义 | 预期退出码 | 主判定 |
|---|---|---|---|
| `HP` | 合法输入主链路 | `0` | 关键输出字段完整且可解析 |
| `FC` | 缺字段/冲突输入 | `2` | 触发 Fail-Closed 或等价阻断 |
| `TR` | 资产-契约-registry 可追溯 | `2`（缺链路时） | `case -> asset -> contract -> registry` 全链可回放 |
| `RB` | 回退/恢复语义存在且可执行 | `2`（缺恢复语义时） | process 关注 `fail_policy`，skill 关注 Fail-Closed 决策与恢复说明 |

## 3. Skill 用例前缀清单（8）

| skill_id | runtime key | case 前缀 |
|---|---|---|
| `meta.arch.agent-creator` | `agent-creator` | `MS-AGENT-CREATOR-{HP|FC|TR|RB}` |
| `meta.arch.objective-writer` | `objective-writer` | `MS-OBJECTIVE-WRITER-{HP|FC|TR|RB}` |
| `meta.arch.process-creator` | `process-creator` | `MS-PROCESS-CREATOR-{HP|FC|TR|RB}` |
| `meta.arch.skill-creator` | `meta-skill-creator` | `MS-META-SKILL-CREATOR-{HP|FC|TR|RB}` |
| `meta.arch.spec-writer` | `spec-writer` | `MS-SPEC-WRITER-{HP|FC|TR|RB}` |
| `meta.arch.template-validator` | `template-validator` | `MS-TEMPLATE-VALIDATOR-{HP|FC|TR|RB}` |
| `meta.qa.llm-judge` | `llm-judge` | `MS-LLM-JUDGE-{HP|FC|TR|RB}` |
| `meta.qa.test-designer` | `test-designer` | `MS-TEST-DESIGNER-{HP|FC|TR|RB}` |

## 4. Process 用例前缀清单（20）

| process_id | runtime key | case 前缀 |
|---|---|---|
| `construction-plane-governance` | `construction-plane-governance` | `MP-CONSTRUCTION-PLANE-GOVERNANCE-{HP|FC|TR|RB}` |
| `development-process` | `development-process` | `MP-DEVELOPMENT-PROCESS-{HP|FC|TR|RB}` |
| `escalation` | `escalation` | `MP-ESCALATION-{HP|FC|TR|RB}` |
| `evolution-feedback-planning` | `evolution-feedback-planning` | `MP-EVOLUTION-FEEDBACK-PLANNING-{HP|FC|TR|RB}` |
| `full-development` | `full-development` | `MP-FULL-DEVELOPMENT-{HP|FC|TR|RB}` |
| `governed-config-change` | `governed-config-change` | `MP-GOVERNED-CONFIG-CHANGE-{HP|FC|TR|RB}` |
| `hold-governance` | `hold-governance` | `MP-HOLD-GOVERNANCE-{HP|FC|TR|RB}` |
| `hotfix` | `hotfix` | `MP-HOTFIX-{HP|FC|TR|RB}` |
| `hotfix-intake-normalization` | `hotfix-intake-normalization` | `MP-HOTFIX-INTAKE-NORMALIZATION-{HP|FC|TR|RB}` |
| `hotfix-scope-spec-baseline` | `hotfix-scope-spec-baseline` | `MP-HOTFIX-SCOPE-SPEC-BASELINE-{HP|FC|TR|RB}` |
| `implementation-execution-core` | `implementation-execution-core` | `MP-IMPLEMENTATION-EXECUTION-CORE-{HP|FC|TR|RB}` |
| `lifecycle-review` | `lifecycle-review` | `MP-LIFECYCLE-REVIEW-{HP|FC|TR|RB}` |
| `objective-scope-baseline` | `objective-scope-baseline` | `MP-OBJECTIVE-SCOPE-BASELINE-{HP|FC|TR|RB}` |
| `quality-gate-evaluation` | `quality-gate-evaluation` | `MP-QUALITY-GATE-EVALUATION-{HP|FC|TR|RB}` |
| `quality-gate-preparation` | `quality-gate-preparation` | `MP-QUALITY-GATE-PREPARATION-{HP|FC|TR|RB}` |
| `refactor` | `refactor` | `MP-REFACTOR-{HP|FC|TR|RB}` |
| `registry-sync` | `registry-sync` | `MP-REGISTRY-SYNC-{HP|FC|TR|RB}` |
| `release-packaging-governed` | `release-packaging-governed` | `MP-RELEASE-PACKAGING-GOVERNED-{HP|FC|TR|RB}` |
| `runtime-policy-calibration` | `runtime-policy-calibration` | `MP-RUNTIME-POLICY-CALIBRATION-{HP|FC|TR|RB}` |
| `spec-authoring-contract` | `spec-authoring-contract` | `MP-SPEC-AUTHORING-CONTRACT-{HP|FC|TR|RB}` |

## 5. 输入载荷模板

### 5.1 runner 模式（示例）

```json
{
  "asset_id": "meta.arch.agent-creator",
  "scenario": "HP",
  "runner_input": {
    "agent_id": "demo-agent",
    "role_scope": {
      "responsibilities": ["输出资产计划"],
      "boundaries": ["不修改实现"]
    },
    "interfaces": [{"protocol_ref": "docs/design/interfaces/meta-self-modification-protocol.md"}],
    "owner": "architect"
  }
}
```

### 5.2 online_qa 模式（示例）

```json
{
  "asset_id": "full-development",
  "scenario": "TR",
  "qa_online_contract": {
    "required_fields": [
      "gate_decision",
      "asset_id",
      "scenario",
      "reason_code",
      "expected_exit_code",
      "traceability_refs",
      "recovery_or_rollback"
    ]
  }
}
```

## 6. 预期输出模板

```json
{
  "gate_decision": "pass|fail|hold|test_invalid|fail_closed",
  "asset_id": "<asset_id>",
  "scenario": "HP|FC|TR|RB",
  "reason_code": "<machine_readable_reason>",
  "expected_exit_code": 0,
  "traceability_refs": ["<path1>", "<path2>"],
  "recovery_or_rollback": "<text_or_ref>"
}
```

## 7. 判定规则

1. `HP`：主判定必须为通过语义（`pass/approved/allow`），且关键输出字段完整。
2. `FC`：必须返回阻断语义（`fail_closed/fail/hold/test_invalid`）并给出原因码。
3. `TR`：`traceability_refs` 非空且指向存在路径；并可映射到 registry 条目。
4. `RB`：必须给出回退/恢复说明；process 需具备 `fail_policy.retry/escalation_chain`。

## 8. 失败码规范

| reason_code | 说明 |
|---|---|
| `missing_required_fields` | 输入关键字段缺失 |
| `invalid_contract_refs` | 契约引用不存在或不可读 |
| `online_asset_unavailable` | openclaw 运行时资产不可见或不可执行 |
| `traceability_broken` | case 到资产/契约/registry 链路断裂 |
| `rollback_semantics_missing` | 缺回退/恢复语义 |
| `assertion_failed` | 断言不成立 |
| `unexpected_error` | 非预期异常 |

## 9. 套件定义

1. `meta-skills`：全部 skill case。
2. `meta-processes`：全部 process case。
3. `online-critical`：每资产 `HP+FC`。
4. `final-regression`：分层执行（先 `online-critical` 再 `final-regression-full`）。
5. `final-regression-full`：全量 112 case。
