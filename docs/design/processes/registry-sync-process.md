# registry-sync 流程设计

> 版本: v0.1.0 | 分类: Governance Process | 层级: P6 | 类型: 治理原子流程（AP-011 包装语义） | process_id: registry-sync | owner: hr | 生命周期: draft

## 目标

将注册表同步从“散点动作”收敛为统一治理原子流程，确保生命周期迁移后的 registry 写入与校验具备稳定契约、可审计证据与 Fail-Closed 语义。

## 定位与边界

1. `registry-sync` 保持 P6 原子流程口径，不升级为 P5/P4 复合流程。
2. 本流程是 `AP-011 Registry Sync` 的治理包装语义，不承接实现、评测、发布动作。
3. 本流程只处理“同步与校验”，不负责生命周期审批裁决。

## 调用方与实现落点

1. 调用方：
   - `full-development`（`lifecycle-gate-sync` 阶段）
   - `hotfix`（`lifecycle-gate-sync` 阶段）
   - `refactor`（`lifecycle-gate-sync` 阶段）
   - `lifecycle-review`（`sync-registry` 阶段）
2. 实现落点（Session3 已落地）：
   - `processes/meta/registry-sync/SKILL.md`
   - `processes/meta/registry-sync/PROCESS.md`
   - `processes/meta/registry-sync/process.json`
   - `processes/meta/registry-sync/scripts/registry_sync_runner.py`

## 输入契约

必填字段：

1. `target_registry_ref`
2. `registry_patch_plan_ref`
3. `requested_transition_ref`
4. `verify_scope`
5. `evidence_ref`

校验规则：

1. `target_registry_ref` 必须指向受控 registry（`skill/process/agent` 三表之一）。
2. `registry_patch_plan_ref` 必须可追溯到本回合变更意图与资产列表。
3. `verify_scope` 不能为空，且不得越权扩展到未授权目录。

## 输出契约

1. `registry_sync_ref`
2. `registry_verify_report_ref`
3. `sync_decision`（`pass|fail|blocked`）
4. `reasons`

## 执行语义（AP 映射）

1. 原子映射：`AP-011 Registry Sync`
2. Actor：`hr`（默认）或 `bpm`（编排回填场景）
3. Skill：`sys.qa.registry-validator`（运行资产阶段由 Session3 落地绑定）

## Fail-Closed

1. `registry_patch_plan_ref` 缺失或不可解析，直接 `fail`。
2. registry 目标路径不可达、字段冲突或契约违规，直接 `fail`。
3. `python3 shared/registry/registry_contract_tool.py verify` 返回非零，`sync_decision=fail`。
4. 证据链不可追溯时 `blocked`，禁止上游流程继续推进生命周期迁移。

## test_mount（统一入口）

1. `tests/m3-runtime/run_skill_contract_validation.py`（统一技能契约入口）
2. `python3 shared/registry/registry_contract_tool.py verify`

## 生命周期与推进规则

1. 本文档阶段：运行资产已落地，生命周期保持 `draft`。
2. 本回合已新增运行目录与 registry 实条目，并通过 contract 校验。
3. 在完成更大规模运行级回归前，禁止将流程状态声明为 `review/active`。
