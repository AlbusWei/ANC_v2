# TC-M5-HOOK-ONLINE-001~007

## TC-M5-HOOK-ONLINE-001 网关健康检查（线上）

- 目标: 确认 OpenClaw 网关在线、M5 运行链路可接入。
- 输入: `openclaw health --json`
- 期望:
  - 返回码为 `0`
  - 返回 JSON 且 `ok=true`
- 失败策略: 命令失败或 `ok!=true`，Fail-Closed。

## TC-M5-HOOK-ONLINE-002 Hook 面可达性检查（线上）

- 目标: 确认 Hook 列表与 Hook 检查接口可执行。
- 输入:
  - `openclaw hooks list --json`
  - `openclaw hooks check --json`
- 期望:
  - 两条命令均返回码 `0`
  - `hooks list` 返回 JSON 数组
  - `hooks check` 返回 JSON 对象
- 失败策略: 任一命令失败则 Fail-Closed。

## TC-M5-HOOK-ONLINE-003 Cron 状态检查（线上）

- 目标: 确认常态编排组件可用。
- 输入: `openclaw cron status --json`
- 期望:
  - 返回码为 `0`
  - 返回 JSON 且 `enabled=true`
- 失败策略: Cron 不可用或未启用则 Fail-Closed。

## TC-M5-HOOK-ONLINE-004 Hook 包安装与发现（线上）

- 目标: 通过真实 OpenClaw 命令完成 Hook 包安装并确认被网关发现。
- 输入:
  - `openclaw hooks install --link runtime_data/private-assets/hooks/anc-lifecycle-events`
  - `openclaw hooks install runtime_data/private-assets/hooks/anc-lifecycle-events`
  - `openclaw gateway restart`
  - `openclaw hooks list --json`
- 期望:
  - 安装命令成功（或已存在可接受）
  - `lifecycle-event-bridge` 出现在 hooks 列表且 `eligible=true`
- 失败策略: Hook 不可发现或不可用则 Fail-Closed。

## TC-M5-HOOK-ONLINE-005 Hook 触发桥接验证（线上）

- 目标: 验证平台事件可经 Hook 桥接生成 ingress 与 runtime 输出。
- 输入:
  - `openclaw gateway restart`（触发 `gateway:startup`）
  - 检查 `runtime_data/evolution/hooks/dispatch/` 与 `runtime_data/evolution/hooks/logs/lifecycle-event-bridge.jsonl`
- 期望:
  - 重启后产生新的 dispatch 记录
  - dispatch 指向的 `runtime_output_ref` 文件存在且状态可读
- 失败策略: 未产生新桥接证据则 Fail-Closed。

## TC-M5-HOOK-ONLINE-006 Batch9 Cron 编排落地（线上）

- 目标: 落地并校验 Batch9 两类 cron 任务（isolated/main+systemEvent）且显式 `tz`。
- 输入:
  - `openclaw cron add ... m5-improvement-review ... --session isolated --tz Asia/Shanghai`
  - `openclaw cron add ... m5-owner-review-reminder ... --session main --tz Asia/Shanghai`
  - `openclaw cron list --json`
- 期望:
  - 两任务均存在
  - `tz` 为显式值
  - `sessionTarget` 分别为 `isolated` / `main`
- 失败策略: 任一编排契约不满足则 Fail-Closed。

## TC-M5-HOOK-ONLINE-007 Cron 运行与 Heartbeat 审计（线上）

- 目标: 验证 cron 可运行、运行历史可审计、heartbeat 可给出最近状态。
- 输入:
  - `openclaw cron run <job-id> --expect-final`
  - `openclaw cron runs --id <job-id> --limit 1`
  - `openclaw system heartbeat enable`
  - `openclaw system event --mode now --text "..."`
  - `openclaw system heartbeat last`
- 期望:
  - cron run 返回成功
  - runs 历史最新记录 `status=ok`
  - heartbeat last 返回结构化状态对象（非空）
- 失败策略: 任一链路不可审计则 Fail-Closed。

## 执行入口

- `python3 tests/m5-self-evolution/run_tc_online.py`
