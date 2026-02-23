# scaffold 输出规范

## 产物列表

1. `SKILL.md`
2. `TEST.md`

## `SKILL.md` 最小要求

1. frontmatter 包含 `name/description/license/compatibility/version`。
2. 正文包含 `Capability Contract (Machine-Readable)` 固定标题与 YAML 块。
3. 含触发矩阵、字段级输入输出约束、Fail-Closed 决策表、运行命令。

## `TEST.md` 最小要求

1. 至少 6 个测试用例。
2. 至少 2 个 Fail-Closed。
3. 至少 1 个 Traceability。
4. 包含 `Evaluation Configuration`。

## 质量红线

1. 生成内容不得包含 `TODO` 占位。
2. 路径必须使用仓库相对路径。
3. 产物应可直接进入 review gate 基础校验。
