# skill-creator Review Rubric

## 评审维度

1. 触发条件是否清晰。
2. 输入输出契约是否可检查。
3. 失败路径是否 Fail-Closed。
4. 测试与 registry 是否同步。

## 判定规则

- PASS: 四项全部满足，且无 P0 缺陷。
- REWORK: 任一项缺失或存在不可追溯路径。

## 快速检查问题

- 这个 skill 在什么场景必须调用？
- 如果输入缺失，系统会如何回退？
- 测试用例能否覆盖核心 Objective？
