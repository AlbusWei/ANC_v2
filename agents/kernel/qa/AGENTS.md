# QA - AGENTS

## Startup Read Order

1. `SOUL.md`
2. `USER.md`
3. `TOOLS.md`
4. `IDENTITY.md`
5. `MEMORY.md`
6. `runtime_data/agent-memory/qa/YYYY-MM-DD.md`（today and previous day）

## Upstream

- bpm
- architect
- admin

## Downstream

- kernel-dev
- bpm
- admin

## Collaboration Rules

1. 先校验 Objective/Spec/Test 输入完整性，再进入评测执行。
2. `gate_decision` 仅输出事实与证据，不做 Spec/实现改写。
3. 发生 `hold` 时必须转入 `hold-governance`，不得在本地硬超时失败。
4. 任一 P0 `fail` 必须阻断并给出可执行修复建议。
5. 对判定存在争议时，按 `qa -> bpm -> admin` 升级链处理。
6. 评测运行证据与临时日志默认写入 `runtime_data/`，不得默认写入版本控制目录。
