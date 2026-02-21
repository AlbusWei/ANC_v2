# Processes & Business Review Checklist

> Branch: `codex/review-processes-business`
> Worktree: `.`

## 1. 目标

核对 P1~P6 递归流程、双主线（内部孵化/外部交付）与原子流程映射完整性。

## 1.1 本分支设计立场（讨论结论）

1. 本分支以架构设计与 high-level design 为主，不做一次性业务流程实现。
2. `internal-productization-e2e-flow` 与 `software-vendor-e2e-flow` 用于澄清与验证架构，不作为规范真相源。
3. 流程规范应由独立标准文档承载，示例流程只做“映射示例”。
4. 合规判定采用“义务覆盖”而非固定阶段命名：核心义务强制，`Release/Evolution` 条件触发。
5. 条件触发采用混合策略：`process_type` 默认义务 + 输出物推断二次校验，冲突即 Fail-Closed。
6. 流程语法强约束：`phase` 只能引用子流程（复合或原子），所有 skill 调用必须先包装为原子流程。
7. 原子包装采用混合策略：高风险动作必须强类型原子流程；低风险动作可走通用包装器并受风险门禁约束。
8. `governance_bundle` 以 `process.json` 为执行真相来源，供 BPM 在流程实例启动时加载治理快照。

## 2. Entire 执行要求（每次会话）

1. `entire status --detailed`
2. `.../entire_codex_bridge.py start`
3. 每回合改动后 `sync`
4. commit 后检查 `Entire-Checkpoint`
5. `.../entire_codex_bridge.py end`

## 3. 允许修改范围

1. `docs/design/processes/`
2. `docs/design/business/`
3. `docs/design/inventories/process-inventory.md`

## 4. 禁止修改范围

1. `docs/design/data-models/`
2. `docs/design/interfaces/`
3. `shared/registry/`

## 5. 核对项

- [x] P1~P6 各层定义职责清晰，无与 L0~L5 混淆。
- [x] P4 两条主线都有完整阶段定义。
- [x] 外部主线 `delivery-iterations` 明确复用“开发闭环标准义务”，而非绑定某个示例流程文档。
- [x] 每个 P4 阶段都能落到 P6 原子流程。
- [x] 原子流程目录 AP-001~AP-017 与业务映射一致。
- [x] 递归规则说明包含终止条件与失败策略。
- [x] process inventory canonical/legacy 说明与流程文档一致。
- [ ] 无“同名流程不同语义”冲突（`development-process` canonical/legacy 资产语义仍需迁移收敛）。
- [x] 示例流程与规范文档分层清晰：示例可替换，规范不漂移。
- [x] `phase -> subprocess` 语法一致，文档中不存在“直接调用 skill 作为 phase 执行单元”的表述。
- [x] `process_type` 权威枚举由标准文档集中定义，流程文档仅引用，不自行发明类型值。
- [ ] `governance_bundle`（process-level）能追溯到语法、义务、风险策略与核对清单来源（标准已定义，待落地到流程 `process.json`）。

## 6. 完成定义（DoD）

- [x] 形成“P4→P6 追溯表”并在文档中可见。
- [ ] 所有业务流程引用路径均可达（需在主工作区完成同名文档落位后复核）。
- [x] 提交只含流程与业务相关文件。
- [x] checklist 中包含“流程开发与治理元流程”的背景、约束与后续工作清单。

## 7. 建议提交粒度

1. `processes: p-level and recursion consistency`
2. `business: dual-flow reuse and atomic traceability`

## 8. 流程开发与治理元流程工作清单（未完成，待细化讨论）

1. 补充 `phase -> subprocess` 迁移说明，明确现有 `skill_or_process` 写法的过渡与退役计划。
2. 在开发型流程 `process.json` 实际引入 `process_type + governance_bundle` 字段，并定义最小校验样例。
3. 定义 canonical 路径可达性策略（worktree 评审期与主工作区合并后的一致性检查规则）。
4. 收敛 `development-process` canonical/legacy 同名异义风险（明确删除/冻结 legacy 的执行语义）。
