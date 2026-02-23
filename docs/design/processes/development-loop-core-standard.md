# Development Loop Core Standard

> 版本: v0.2.0 | 分类: Process Standard | 作用域: P4 开发型流程

## 1. 目标与边界

1. 定义 ANC v2 开发闭环的规范真相源，供不同业务流程复用。
2. 本标准关注 high-level 义务与治理约束，不绑定单一业务流程实现。
3. `internal-productization-e2e-flow` 与 `software-vendor-e2e-flow` 仅作为参考映射，不是规范真相源。

## 2. process_type 权威枚举（v1）

### 2.1 active_types_v1（参与当前合规判定）

1. `dev.internal-productization`
2. `dev.external-delivery-iteration`
3. `dev.hotfix`
4. `dev.refactor`
5. `dev.prototype`

### 2.2 reserved_namespaces（预留，不参与当前判定）

1. `gov.*`
2. `evo.*`
3. `biz.*`
4. `meta.*`

规则：

1. 流程文档/流程清单只能引用本节已定义类型值。
2. 新增类型必须先更新本标准，再进入流程资产或 checklist。

## 3. 义务模型（Obligation Model）

### 3.1 核心强制义务（所有开发型流程必选）

| obligation_id | 名称 |
|---|---|
| O1 | Objective |
| O2 | Spec |
| O3 | Test |
| O4 | Implement |
| O5 | Verify |
| O6 | Lifecycle |

### 3.2 条件义务（按触发规则判定）

| obligation_id | 名称 |
|---|---|
| O7 | Release |
| O8 | Evolution |

统一约束：

1. 每个义务必须有独立证据条目，即使多个义务压缩在同一阶段执行。
2. 义务缺失、义务无证据、义务证据与门禁结论冲突时，Fail-Closed。

## 4. 条件触发算法（混合策略）

目标公式：

`required_obligations = core_obligations ∪ defaults(process_type) ∪ inferred(output_artifacts)`

### 4.1 defaults(process_type)

| process_type | 默认附加义务 |
|---|---|
| `dev.internal-productization` | O7, O8 |
| `dev.external-delivery-iteration` | O7, O8 |
| `dev.hotfix` | O7 |
| `dev.refactor` | 无 |
| `dev.prototype` | 无 |

### 4.2 inferred(output_artifacts)

1. 出现 `versioned_release_package`、`deployment_bundle`、`customer_handoff_pack` 时，强制包含 O7。
2. 出现 `runtime_feedback_digest`、`improvement_backlog`、`retro_report` 时，强制包含 O8。

### 4.3 冲突处理

1. 流程声明义务少于推断义务：Fail-Closed。
2. 义务判定结论互相矛盾：Fail-Closed 并升级治理审批。

## 5. Phase 语法与组合约束

1. `phase` 只能引用子流程（复合流程或原子流程）。
2. 不允许将 skill 作为 phase 直接执行单元。
3. 任意 skill 调用必须先包装为 P6 原子流程。
4. 一个 phase 可组合多个子流程，但必须声明终止条件与失败策略。
5. `phase_process_type` 可选；若声明，必须与其引用子流程的义务能力兼容。

## 6. 原子包装策略（Typed + Generic）

### 6.1 Typed AP（高风险动作，强制）

以下动作必须使用强类型原子流程，不可走通用包装器：

1. 生命周期状态迁移
2. registry 写入或结构变更
3. 系统配置写操作
4. 发布签发与客户验收签收

### 6.2 Generic AP（低风险动作，可选）

1. 允许通过通用原子流程（如 `ap-skill-invoke`）调用低风险技能。
2. 必须使用 allowlist，且输出调用参数、执行结果与证据引用。
3. 若动作风险等级高于 Generic AP 授权边界，Fail-Closed。

## 7. process.json 治理绑定（governance_bundle）

每个开发型流程的 `process.json` 应包含：

1. `process_type`
2. `governance_bundle.syntax_ref`
3. `governance_bundle.obligation_ref`
4. `governance_bundle.risk_policy_ref`
5. `governance_bundle.checklist_ref`

建议行为：

1. BPM 在实例启动时加载 `governance_bundle` 并生成治理快照。
2. 缺失引用、引用不可达、引用冲突时，拒绝实例启动（Fail-Closed）。

## 8. 合规判定与追溯产物

最小验收：

1. 义务覆盖追溯表可见：`phase -> obligations -> AP -> evidence -> fail_action`。
2. P4 每个阶段可追溯到 P6 原子流程。
3. 证据链满足门禁校验并支持审计回放。

## 9. 与示例流程关系

1. `internal-productization-e2e-flow`：覆盖 O1~O8 的参考实现。
2. `software-vendor-e2e-flow`：其 `delivery-iterations` 阶段采用 `dev.external-delivery-iteration` 义务集合的参考实现。
3. 示例可替换，标准语义不可漂移。

## 10. M3 Phase2 子流程模型约束（新增）

1. `development-process/full-development/hotfix/refactor` 的核心阶段必须优先复用现行 P5 子流程库。
2. 现行 P5 子流程库固定为：
   1. `objective-scope-baseline`
   2. `hotfix-intake-normalization`
   3. `hotfix-scope-spec-baseline`
   4. `spec-authoring-contract`
   5. `implementation-execution-core`
   6. `release-packaging-governed`
   7. `evolution-feedback-planning`
3. 历史包装流程已退役，禁止作为目标态 phase target 回流。
4. 若检测到历史包装流程回流或 phase I/O 不闭合，必须 Fail-Closed 并阻断阶段收口。
