# skill-creator Review Rubric

## 评审维度

1. 触发条件是否清晰。
2. 输入输出契约是否可检查。
3. 失败路径是否 Fail-Closed。
4. Capability Contract YAML 是否可解析且字段完整。
5. 测试与 registry 是否同步。
6. review/smoke evidence 是否可追溯。

## 判定规则

- PASS: 六项全部满足，且无 P0 缺陷。
- REWORK: 任一项缺失或存在不可追溯路径。

## 快速检查问题

- 这个 skill 在什么场景必须调用？
- 如果输入缺失，系统如何回退？
- `test_mount` 是否与 registry `tests` 一致？
- 是否具备 review 与 active 的证据链？
