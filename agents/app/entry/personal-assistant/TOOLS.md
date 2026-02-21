# Personal-Assistant - TOOLS

## Allowed Skills

- request-intake
- status-reporter
- context-packager
- route-selector

## External Tools

- openclaw health --json
- openclaw sessions --json
- openclaw config get agents.list --json

## Usage Notes

- 禁止执行 `openclaw config set/unset` 与 `gateway call config.patch/apply`。
- 配置写请求必须先生成材料并提交 BPM。
