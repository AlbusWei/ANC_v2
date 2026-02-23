# M3 Self-Development Live Cases（Session4 基座）

## Case 编号规则

1. `M3-S4-*`：Session4 可执行基座用例（本回合必须可运行）。
2. `M3-INT-*`：Session5 内部主线 E2E 预留用例（本回合仅登记）。
3. `M3-EXT-*`：Session6 外部主线 E2E 预留用例（本回合仅登记）。
4. `M3-FC-*`：Session5/Session6 跨主线 Fail-Closed 与旁路阻断预留用例（本回合仅登记）。

## Session4 可执行用例矩阵

| case_id | suite | 类别 | 目标 | 状态 | 证据子路径 |
|---|---|---|---|---|---|
| `M3-S4-HAPPY-001` | `session4-happy` | 主链路 | 验证 M3 runtime happy 基线成立 | executable | `cases/M3-S4-HAPPY-001/` |
| `M3-S4-EXC-001` | `session4-exception` | 异常链路 | 验证 M1 hold 路由成立 | executable | `cases/M3-S4-EXC-001/` |
| `M3-S4-FC-001` | `session4-fail-closed` | Fail-Closed | 验证 M1 fail-closed 断言成立 | executable | `cases/M3-S4-FC-001/` |
| `M3-S4-RW-001` | `session4-rollback` | 回退/返工 | 验证 release-manager rollback/reject 分支成立 | executable | `cases/M3-S4-RW-001/` |

## Session5/Session6 预留用例矩阵

| case_id | 预期会话 | suite | 类别 | 状态 | 证据子路径（预留） |
|---|---|---|---|---|---|
| `M3-INT-001` | Session5 | `session5-internal` | 内部主线 | reserved | `cases/M3-INT-001/` |
| `M3-INT-002` | Session5 | `session5-internal` | 内部主线 | reserved | `cases/M3-INT-002/` |
| `M3-INT-003` | Session5 | `session5-internal` | 内部主线 | reserved | `cases/M3-INT-003/` |
| `M3-EXT-001` | Session6 | `session6-external` | 外部主线 | reserved | `cases/M3-EXT-001/` |
| `M3-EXT-002` | Session6 | `session6-external` | 外部主线 | reserved | `cases/M3-EXT-002/` |
| `M3-EXT-003` | Session6 | `session6-external` | 外部主线 | reserved | `cases/M3-EXT-003/` |
| `M3-FC-101` | Session5/6 | `session6-external` | 跨主线 Fail-Closed | reserved | `cases/M3-FC-101/` |
| `M3-FC-102` | Session5/6 | `session6-external` | 跨主线 Fail-Closed | reserved | `cases/M3-FC-102/` |
| `M3-FC-103` | Session5/6 | `session6-external` | 旁路阻断 | reserved | `cases/M3-FC-103/` |

## Runner 约束

1. 默认执行（不传 `--suite/--case`）仅运行四个 `M3-S4-*` 用例，并要求四类覆盖齐全。
2. 选择任何 `reserved` 用例时，runner 必须 Fail-Closed 并返回 `2`。
3. 上游证据目录固定为：
   - `upstream/m3-runtime/`
   - `upstream/m1-runtime/`
