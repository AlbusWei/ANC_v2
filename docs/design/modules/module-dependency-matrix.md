# 模块依赖矩阵

> 版本: v0.2.0

## 建设顺序

```
M6 (Construction Plane) → M2 (BPM Engine) → M1 (Test System) → M3 (Self-Dev) → M4 (Lifecycle) → M5 (Self-Evolution)
```

## 依赖矩阵

行依赖列（✓ = 行模块依赖列模块）：

| | M1 Test | M2 BPM | M3 Self-Dev | M4 Lifecycle | M5 Evolution | M6 Construction |
|---|---|---|---|---|---|---|
| M1 Test | — | ✓ | | | | ✓ |
| M2 BPM | | — | | | | ✓ |
| M3 Self-Dev | ✓ | ✓ | — | ✓ | | |
| M4 Lifecycle | ✓ | ✓ | | — | | |
| M5 Evolution | ✓ | ✓ | ✓ | ✓ | — | |
| M6 Construction | | | | | | — |

## 阶段映射

| 模块 | 建设阶段 | 优先级 | 前置条件 |
|---|---|---|---|
| M6 Construction Plane | Phase 0 | P0 | 无 |
| M2 BPM Engine | Phase 0-1 | P0 | M6 |
| M1 Test System | Phase 0-1 | P0 | M2, M6 |
| M3 Self-Development | Phase 1-2 | P1 | M1, M2, M4 |
| M4 Lifecycle Management | Phase 1 | P1 | M1, M2 |
| M5 Self-Evolution | Phase 2-4 | P2 | M1, M2, M3, M4 |

## 关键路径

```
M6 → M2 → M1 → M4 → M3 → M5
```

M4 和 M1 可部分并行建设，但 M3 需要两者都就绪。

## 触发治理路径（本轮补充）

1. 策略面：`M4` 维护 trigger 生命周期、override 与风险规则。
2. 运行面：`M2` 消费策略并执行匹配、去重、补跑和升级。
3. 设计期测试锚点：`/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules/docs/design/modules/trigger-governance-test-proposal.md`

## 循环依赖检查

无循环依赖。依赖图为有向无环图（DAG）。
