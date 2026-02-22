# M2 BPM Runtime Hardening W5 Execution Summary

## Metadata

- Date: 2026-02-22
- Branch: `codex/review-layers-modules`
- Scope: W5 `system-analyst` 生产化收口
- Runner Entry:
  - `tests/m2-bpm-runtime/run_tc_anl.py`

## 三流程状态变化明细

1. Agent 生命周期流
   - `system-analyst`: `planned -> review -> active`
   - 证据：`docs/design/agents/kernel/system-analyst.md`、`docs/design/inventories/agent-inventory.md`、`shared/registry/agent_directory.json`
2. Skill 生命周期流
   - `sys.arch.system-feedback-digest`: `draft -> active`
   - 证据：`skills/system/system-feedback-digest/SKILL.md`、`docs/design/skills/system-skills.md`、`docs/design/inventories/skill-inventory.md`、`shared/registry/skill_registry.json`
3. Process 生命周期流
   - `runtime-policy-calibration`: `planned -> active`
   - 证据：`processes/meta/runtime-policy-calibration/process.json`、`docs/design/processes/runtime-policy-calibration-process.md`、`docs/design/inventories/process-inventory.md`、`shared/registry/process_registry.json`

## 资产与契约变更摘要

1. 新增 `system-analyst` 运行资产（`IDENTITY/SOUL/TOOLS/USER/MEMORY`），并补齐 `AGENTS.md` 协作边界。
2. 新增生产技能 `sys.arch.system-feedback-digest`：
   - 输入契约：`handoff_ref` 指向满足 role-handoff 最小字段的交接包。
   - 输出契约：`status=completed` 时输出 digest 引用；`status=rejected` 时输出 reject 引用。
   - Fail-Closed：缺字段、目标角色不匹配、objective 不可达、证据不可达或为空均拒绝。
3. 新增可执行流程 `runtime-policy-calibration`（6 phase）：
   - `p1~p3` 由 `system-analyst` 执行分析主链。
   - `p4~p5` 强制治理同步与 admin 决策门禁。
   - `p6` 产出回滚观测闭环记录。
4. OpenClaw 运行配置联动：
   - `config/openclaw.projection.profiles.json` 将 `system-analyst` 纳入 `phase05-base/phase05-with-entry`。
   - `config/openclaw.phase05.fragment.json`、`config/openclaw.phase05.with-entry.fragment.json` 重新投影后可见 `system-analyst`。

## 调度样例结果与证据路径

1. Workspace 切换与配置校验
   - `python3 tools/openclaw/switch_workspace.py --repo-root .` 成功，`agent_count=8`。
   - `openclaw config get agents.list --json` 包含 `system-analyst`。
   - `openclaw skills info system-feedback-digest --json` 可解析到 `skills/system/system-feedback-digest/SKILL.md`。
2. 端到端测试
   - `python3 tests/m2-bpm-runtime/run_tc_anl.py`：PASS (3/3)
   - 报告：`docs/design/modules/evidence/bpm-runtime/w5_tc_anl_report.json`
3. 样例证据矩阵

| Case | Runtime Evidence Dir | Key Refs |
|---|---|---|
| TC-ANL-001 | `docs/design/modules/evidence/bpm-runtime/w5_system_analyst_prod_cases/TC-ANL-001/` | `handoff_input.json`, `handoff_evidence_index.json`, `analysis_digest.json`, `digest_output.json` |
| TC-ANL-002 | `docs/design/modules/evidence/bpm-runtime/w5_system_analyst_prod_cases/TC-ANL-002/` | `handoff_input.json`, `handoff_evidence_index.json`, `reject_output.json`, `digest_output.json` |
| TC-ANL-003 | `docs/design/modules/evidence/bpm-runtime/w5_system_analyst_prod_cases/TC-ANL-003/` | `process_input.json`, `process_output.json`, `runtime_policy_calibration/runtime_trace.json`, `runtime_policy_calibration/p5_decision_record.json` |

## DoD 勾选与未决风险

- [x] `system-analyst` 能接收 handoff 并产出结构化 digest。
- [x] 证据不足时正确拒绝（`reason_code=evidence_insufficient`）且拒绝记录可审计。
- [x] agent doc + inventory + registry 一致，并通过 `python3 shared/registry/registry_contract_tool.py verify`。
- [x] OpenClaw 运行配置可加载 `system-analyst` 与 `system-feedback-digest`。

未决风险：

1. `openclaw` 启动时存在 `plugins.entries.matrix` duplicate warning（历史环境配置噪音），本轮未改动插件层；当前不阻塞 `system-analyst` 路径。
2. `runtime-policy-calibration` 目前使用文件化样例数据验证，后续需在真实线上观测样本下追加长期漂移监测用例。
