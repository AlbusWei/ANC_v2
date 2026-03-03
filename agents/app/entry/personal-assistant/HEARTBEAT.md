# HEARTBEAT.md

## asset-health-check（常态巡检）

- 检查 `runtime_data/private-assets/evolution/` 下策略文件是否存在且可读。
- 检查 `runtime_data/evolution/hooks/logs/lifecycle-event-bridge.jsonl` 最近增量是否出现 `status=error`。
- 检查最近一次 `m5-improvement-review` 与 `m5-owner-review-reminder` 的 cron run 状态；若失败，给出 run id 与升级建议。
- 仅执行巡检与风险提示，不主动发起 owner 评审提醒（该动作由 cron 任务负责）。

无异常时回复 `HEARTBEAT_OK`。
