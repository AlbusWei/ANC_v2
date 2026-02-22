# lifecycle-review 流程设计

> 版本: v0.1.0 | 分类: Governance Process | 层级: P4 | owner: hr | 生命周期: draft | 最后更新: 2026-02-22

## 目标

将生命周期审批从“文档化约定”升级为“最小可执行流程资产”，作为 `M1` 质量门禁结果接入 `M4` 生命周期治理的可执行接点。

## 连续性与 phase 闭合

1. 本流程仅覆盖生命周期治理连续段，不跨实现/发布等非连续生命周期断点。
2. phase 闭合约束：
   - `validate-request`
   - `check-prerequisites`
   - `quality-gate`
   - `execute-transition`
   - `sync-registry`
3. 断点处理：若涉及 M3 开发链路接线或运行证据汇聚，必须由后续线程在上级流程中编排，当前流程不内置跨断点编排逻辑。

## 输入契约

1. `final_gate_verdict_ref`
2. `target_asset_ref`
3. `requested_transition`

## 输出契约

1. `lifecycle_transition_ref`
2. `registry_sync_ref`
3. `lifecycle_review_report_ref`

## 阶段定义

1. `validate-request`
   - actor: `hr`
   - 目标：校验输入字段完整性与引用可达性。
   - 输出：`validated_request_ref`
2. `check-prerequisites`
   - actor: `hr`
   - 目标：校验目标资产当前状态、迁移目标状态、状态机合法性。
   - 输出：`prerequisites_check_ref`
3. `quality-gate`
   - actor: `hr`
   - 目标：核验 `final_gate_verdict_ref` 为 `pass`。
   - 输出：`quality_gate_check_ref`
4. `execute-transition`
   - actor: `hr`
   - 目标：记录 `from_status -> to_status` 生命周期迁移证据。
   - 关联原子流程：`AP-010 Lifecycle Transition`
   - 输出：`lifecycle_transition_ref`
5. `sync-registry`
   - actor: `hr`
   - 目标：执行 registry contract 校验并记录同步证据。
   - 关联原子流程：`AP-011 Registry Sync`
   - 输出：`registry_sync_ref` + `lifecycle_review_report_ref`

## 控制流

`validate-request -> check-prerequisites -> quality-gate -> execute-transition -> sync-registry -> end`

## Fail-Closed

1. 非法状态迁移直接拒绝（例如 `active -> retired` 直跳）。
2. 证据缺失或不可解析直接拒绝（`final_gate_verdict_ref`、`target_asset_ref`、当前状态证据）。
3. 质量门禁 verdict 非 `pass` 直接拒绝。
4. `registry_contract_tool.py verify` 失败直接拒绝。

## 运行入口

1. Process 资产：`processes/meta/lifecycle-review/process.json`
2. Runner：`processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`
3. 最小调用：
   - `python3 processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py --input <input.json> --output <output.json>`
