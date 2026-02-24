# BPM - AGENTS

## Upstream

- admin
- architect
- hr
- personal-assistant

## Downstream

- kernel-dev
- qa

## Collaboration Rules

1. 调度前必须校验输入契约。
2. 每个 phase 完成后必须写 state 与 evidence。
3. 超时或死锁按升级链处理：actor -> owner -> bpm -> admin。
4. App 层系统级配置写请求必须经 BPM 门禁后由 admin 执行。
5. 调度链路默认将 process state/evidence/output 写入 `runtime_data/`，禁止默认落盘到版本控制目录。
