# Process Definition Standard

> 版本: v0.4.0 | 适用范围: 原子/复合/业务流程

## 1. 目标

统一流程定义，使 BPM 可调度、可回放、可恢复。

## 2. 最小必填字段（process.json）

1. `process_id`
2. `version`
3. `process_level`（P1~P6）
4. `phases[]`
5. `control_flow[]`
6. `fail_policy`
7. `evidence_policy`
8. `lineage_policy`

## 2.1 P-Level 语义约束（新增）

1. `process_level` 是流程分类学标签（P1~P6），用于设计组织与治理检索。
2. `process_level` 不直接决定运行时是否可执行；运行行为由 `process.json` 契约与 BPM 调度规则决定。
3. `P4/P5/P6` 在执行引擎侧都可作为可调度流程单元，差异主要体现在抽象层级与复用方式。
4. 若流程可独立产出用户可见交付物，通常归类为 P4；若主要作为可复用子流程模式，通常归类为 P5。

## 3. 递归字段

1. `parent_process_id`：父流程 ID（无父级可空）
2. `composed_processes[]`：被组合的子流程 ID 列表
3. `lineage_policy`：父子实例隔离与回填规则

## 4. 原子流程约束

1. 一个原子流程仅允许一个 Actor 调用一个 Skill。
2. 原子流程内部不得再嵌套子流程。
3. 原子流程必须声明 SIPOC 与证据字段。

## 5. 复合流程约束

1. 阶段可以引用原子流程或复合流程。
2. 必须有终止条件，禁止无界自循环。
3. 失败处理必须声明重试次数和升级路径。

## 6. 连续性约束（新增）

1. 单个复合流程不得跨越非连续生命周期段。
2. 出现断点（例如 `test-design` 与 `post-implementation-evaluation`）必须拆分为多个复合流程。
3. 跨断点衔接必须由上级流程显式编排，不允许在同一顺序链硬拼。

## 7. Phase 闭合约束（新增）

1. 每个 phase 必须映射到已定义原子流程（P6）或已定义复合子流程（P4/P5）。
2. phase 名称、子流程 ID、I/O 契约必须一一对应。
3. 未定义映射的 phase 视为流程不可执行，默认 Fail-Closed。

## 8. 验收条目

- [ ] process.json 字段完整
- [ ] 流程可映射到 P1-P6
- [ ] 证据链字段完整
- [ ] 失败策略可执行
- [ ] 连续性约束满足
- [ ] phase 闭合约束满足
