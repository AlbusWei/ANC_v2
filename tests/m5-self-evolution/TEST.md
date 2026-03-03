# M5 Self-Evolution 测试入口

## 本目录用例范围

1. Batch 6：事件策略与去重规则回归
2. Batch 7：Runner 结束点领域事件产出回归
3. Batch 8：Hook 平台桥接包结构与 fail-closed 行为
4. Batch 9：Cron / Heartbeat 线上编排与审计
5. Batch 10：主链与异常链准入回归（含 Hook 专项）

## 执行命令

1. `python3 -m pytest tests/m5-self-evolution -q`
2. `python3 tests/m5-self-evolution/run_tc_online.py`

## 关键文档

1. `tests/m5-self-evolution/TC-M5.md`
2. `tests/m5-self-evolution/TC-ONLINE.md`
