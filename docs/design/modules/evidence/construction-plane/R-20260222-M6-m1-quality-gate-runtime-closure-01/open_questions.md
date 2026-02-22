# Open Questions

1. Thread-1 差距基线是否需要并行输出“链路视图 + 资产视图”两套索引，以支持 Thread-2 快速映射。
2. Thread-4 若发现历史线程遗留缺口，是否采用“回写补丁 + 重新回归”作为固定流程。
3. OpenSpec change 的 specs delta 与 Scenario 由谁补齐并在何时完成，以便将 `needs_sync` 收敛为 `in_sync`。
