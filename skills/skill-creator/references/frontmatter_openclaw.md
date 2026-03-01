# Frontmatter 兼容说明（meta-skill-creator）

## 最小必填字段

1. `name`
2. `description`
3. `license`
4. `compatibility`

## 建议字段

1. `allowed-tools`
2. `version`

## 运行名约束

1. 仓库内运行名固定为 `meta-skill-creator`。
2. `skill-creator` 为历史别名，不用于运行调用。

## 常见错误

1. frontmatter 缺失结尾 `---`。
2. `name` 非 kebab-case。
3. `compatibility` 字段缺失或格式错误。
