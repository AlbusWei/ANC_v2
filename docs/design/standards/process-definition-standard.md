# Process Definition Standard

> 版本: v0.2.0 | 适用范围: 原子/复合/业务流程

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

## 6. 验收条目

- [ ] process.json 字段完整
- [ ] 流程可映射到 P1-P6
- [ ] 证据链字段完整
- [ ] 失败策略可执行
