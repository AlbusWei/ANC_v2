# HOLD Triage Signals

最小进展信号：

1. `log_delta`：日志有增量
2. `phase_progress`：流程阶段推进
3. `output_heartbeat`：输出流心跳

动作建议：

- `continue`: 三类信号都存在
- `retry`: 有心跳但阶段未推进
- `debug`: 仅日志有活动
- `fail`: 三类都缺失且无法补证
