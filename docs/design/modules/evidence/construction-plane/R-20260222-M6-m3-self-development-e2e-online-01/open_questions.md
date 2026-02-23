# Open Questions

1. Session3 中 `registry-sync` 与 `escalation` 的最小落地边界应采用独立复合流程，还是先以 P6 原子流程封装再由上级编排。
2. Session4 的 M3 专项测试入口是否采用单 runner 汇总，还是按 `full-development/hotfix/refactor` 拆分 runner。（Closed：采用单 runner + `--suite/--case`，默认执行 Session4 四类基座全量）
3. Session7 的回合关闭是否在本 round 直接执行 `round_close`，或在后续回合统一做 close 审计。
