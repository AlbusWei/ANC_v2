# Trigger Runtime Policy Guidelines

> 版本: v0.1.0 | 适用范围: `trigger-schedule-runtime` / `trigger-event-runtime`

## 目标

为 `catchup_policy_ref` 与 `dedupe_policy_ref` 提供编写基线，强调“动态估计、实证校准、Fail-Closed”。

## 核心原则

1. 不使用固定全局时窗；时窗必须由策略动态计算。
2. 不低估 Agent 执行时长；分钟级到数十分钟级执行均视为正常区间。
3. 策略参数必须可回放、可解释、可审计。
4. 当策略无法计算明确决策时，默认 Fail-Closed 并升级。

## catchup_policy_ref 建议字段

1. `policy_id`
2. `trigger_type`
3. `risk_level`
4. `runtime_history_ref`
5. `window_function`
6. `min_samples`
7. `max_window_cap`（可选上限，不是固定窗口）
8. `escalation_threshold`

## 动态窗口计算建议

1. 基线输入：最近 N 次成功运行时长分布（建议 N>=20）。
2. 建议公式（示例）：
   - `computed_window = max(2 * p95_duration, 1.2 * median_duration + jitter_budget)`
3. 对高风险流程可放宽窗口并提高升级阈值，避免误判“长时但正常”的执行。
4. 每轮 dry-run 后必须回填策略参数与命中统计，迭代校准。

## 推荐时间（仅参考，不是硬编码）

1. schedule/heartbeat：可从 `2*p95` 起步，常见落在 10~60 分钟。
2. event（轻量证据归集）：可从 `1.5*p95` 起步，常见落在 5~30 分钟。
3. event（重度分析/归档）：可从 `2~3*p95` 起步，常见落在 20~90 分钟。

## dedupe_policy_ref 建议字段

1. `primary_key_template`: `source+event_id`
2. `fallback_key_template`: `source+canonical_event+entity_type+entity_id+from_status+to_status+emitted_by+time_bucket`
3. `time_bucket_strategy`：按 `trigger_type/risk_level` 动态给定
4. `collision_resolution`

## 证据要求

1. 每次计算应落盘：`computed_window_ref`
2. 每次决策应落盘：`catchup_reason_ref`
3. 每次冲突应落盘：`dedupe_key_ref`
