# TC-ONLINE-001~004

## TC-ONLINE-001 网关健康检查（线上）

- 目标: 确认 OpenClaw 网关可用，运行时链路可接入。
- 输入: `openclaw health --json`
- 期望:
  - 命令返回码为 `0`
  - 输出可解析为 JSON 对象
- 失败策略: 命令失败或输出不可解析，Fail-Closed。

## TC-ONLINE-002 运行时工作区绑定检查（线上）

- 目标: 确认 OpenClaw 当前 `agents.defaults.repoRoot` 与当前 worktree 一致。
- 输入: `openclaw config get agents.defaults.repoRoot --json`
- 期望:
  - 命令返回码为 `0`
  - 返回路径严格等于当前仓库根目录
- 失败策略: 路径不一致则 Fail-Closed，禁止后续宣告 Done。

## TC-ONLINE-003 核心 Agent 可见性检查（线上）

- 目标: 确认 `bpm/admin/system-analyst` 已加载到运行时 agent 列表。
- 输入: `openclaw config get agents.list --json`
- 期望:
  - 命令返回码为 `0`
  - `agents.list` 至少包含 `bpm`、`admin`、`system-analyst`
- 失败策略: 任一核心 agent 缺失，Fail-Closed。

## TC-ONLINE-004 核心 Skill/Process 可加载性检查（线上）

- 目标: 确认 M2 收口所需核心技能与流程技能可被 OpenClaw 直接加载。
- 输入: 逐项执行 `openclaw skills info <skill> --json`
- 覆盖项:
  - `config-change-gatekeeper`
  - `system-config-updater`
  - `trigger-ingress-normalizer`
  - `trigger-matcher-dedupe`
  - `process-instance-manager`
  - `system-feedback-digest`
  - `trigger-schedule-runtime`
  - `trigger-event-runtime`
  - `runtime-policy-calibration`
- 期望:
  - 每项命令返回码为 `0`
  - `eligible=true`
  - `filePath` 可解析
- 失败策略: 任一项失败则 Fail-Closed。

## 执行入口

- `python3 tests/m2-bpm-runtime/run_tc_online.py`
