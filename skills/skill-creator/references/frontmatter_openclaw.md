# Frontmatter Compatibility Notes

## 最小必填字段

1. `name`
2. `description`
3. `license`
4. `compatibility`

## 建议字段

- `metadata`（单行 JSON）
- `allowed-tools`
- `version`

## 常见错误

- frontmatter 缺失 `---` 结束分隔。
- `name` 使用空格而非短横线。
- `metadata` 不是合法 JSON。

## 兼容建议

- 使用稳定、可比较的版本字符串。
- 不在 frontmatter 写多行复杂对象，复杂内容下沉到正文或 references。
