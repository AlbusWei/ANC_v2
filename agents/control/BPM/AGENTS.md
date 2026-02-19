# BPM - AGENTS

## Upstream

- admin
- architect
- hr

## Downstream

- kernel-dev
- qa

## Collaboration Rules

1. 调度前必须校验输入契约。
2. 每个 phase 完成后必须写 state 与 evidence。
3. 超时或死锁按升级链处理：actor -> owner -> bpm -> admin。
