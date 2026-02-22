## Context

`m3-self-development-e2e-online` 是 M3 自开发双主线（内部/外部）E2E 的前置变更。本回合只做 Session1：

1. 设计闭合差距审计。
2. OpenSpec change 基座落盘。
3. M6 证据目录初始化。
4. 施工平面 Session2~Session7 依赖与 DoD 固化。

已确认约束：

- 不做功能开发与运行实现。
- 生命周期目标仅收敛到 `review`。
- 预存 `.entire/codex-bridge/session.json` 变更不纳入本次提交。

## Goals / Non-Goals

**Goals**

- 建立可审计、可执行、可追踪的 M3 Session1 基座。
- 用差距矩阵固化“设计条目 -> 应有资产 -> 现状 -> 阻断级别 -> 归属会话 -> 验收条件”。
- 将 Session2~Session7 明确为可执行依赖链与命令化 DoD。

**Non-Goals**

- 不新增/修改运行时代码逻辑。
- 不推进缺失资产到 `active`。
- 不在 Session1 开展内部/外部双主线 E2E 实跑。

## Decisions

### Decision A: 会话分解采用“闭合优先”

- S2：设计闭合差距收敛。
- S3：缺失资产最小可执行落地。
- S4：M3 专项运行级测试基座。
- S5：内部主线 E2E。
- S6：外部主线 E2E。
- S7：全链路对账收口（到 review）。

Rationale：先消除设计与契约闭合缺口，再进入资产实现与 E2E，降低后续返工风险。

### Decision B: 阻断级别统一为 `S0/S1/S2`

- `S0`: 当前会话硬阻断。
- `S1`: 下一会话开工阻断。
- `S2`: 可并行跟进但不能忽略。

Rationale：与会话依赖链直接对齐，方便 DoD 门禁判定。

### Decision C: 生命周期上限固定为 `review`

本 change 所有落盘动作只支持收敛到 `review`，禁止推进 `active`。

Rationale：当前目标是“设计闭合 + 资产落地基座”，尚未满足 active 准入所需运行观测窗口与回滚演练。

### Decision D: Session1 严禁功能开发

Session1 只输出治理契约与证据基线，不执行实现型任务。

Rationale：避免“边审计边开发”导致的边界漂移，确保后续会话输入稳定。

## Risks / Trade-offs

- [Risk] Session2~Session7 DoD 过于抽象导致执行偏差。
  - Mitigation: DoD 绑定具体文件与命令，不使用泛化表述。
- [Risk] 差距矩阵与 OpenSpec specs 不一致。
  - Mitigation: 要求 Session2 首项即执行一致性校验，并以 `openspec validate` 为硬门禁。
- [Risk] 环境切换漂移（OpenClaw repoRoot/skills 源目录偏移）。
  - Mitigation: Session1 固定记录 `switch_workspace` 后的两项配置读取结果。

## Migration Plan (Session-Level)

1. Session1：基座落盘（本回合完成）。
2. Session2：校正 M3 三流程 manifest 与标准闭合。
3. Session3：补齐 5 项缺失资产的最小可执行落盘并联动 design/inventory/registry。
4. Session4：建立 M3 专项运行级测试套件。
5. Session5/Session6：分别完成内部/外部主线 E2E。
6. Session7：执行全链路对账并将生命周期收敛到 `review`。

## Open Questions

- Session3 对 `registry-sync` 与 `escalation` 的资产粒度是否拆为 P6 + P5，或先以最小流程模板收口。
- Session4 的 M3 专项测试套件是否沿用 `tests/m2-bpm-runtime` 组织范式，或单独建 `tests/m3-self-development`。
- Session7 的 `round_close` 是否在同一回合落盘，或由下一轮 M6 回放统一关闭。
