# AP-011 Registry Sync

> 版本: v0.2.0 | 层级: P6 | 类型: 原子流程

- Actor: hr / bpm
- Skill: registry-validator
- Input: registry patch plan
- Output: 已校验 registry 更新
- Fail-Closed: 路径不可达或字段冲突时失败
- Evidence: registry_sync_ref
