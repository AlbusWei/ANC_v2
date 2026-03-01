# M1/M3 门禁真实性与证据隔离设计

> Status: Superseded
> Superseded-By: `docs/plans/SSOT-design.md`
> Superseded-On: 2026-03-01

> 日期：2026-02-27
> 范围：M3 自开发 + M1 测试门禁

## 1. 目标

在不增加大量字段约定的前提下，确保：

1. simulated/skeleton 仅用于开发自测，不可用于准入。
2. 准入结论必须来自拟真用例下的线上真实执行证据链。
3. 运行证据默认写入 `tmp/runtime_data/...`，避免污染仓库提交。

## 2. 已确认决策（与用户对齐）

### D1 路径策略

- 采用 `tmp/runtime_data/...` 作为运行时证据与 artifacts 默认路径。
- 仓库内 `runtime_data/` 仅用于模板、说明、索引，不承载大体量运行产物。

### D2 simulated/skeleton 边界

- 允许 simulated/skeleton 作为开发环节自测能力。
- 禁止 simulated/skeleton 进入最终门禁准入链路。

### D3 门禁判定方式

- 采用“证据反查”而非“声明字段”作为核心判定。
- 最终 gate 在准入前必须满足以下最小证据集（缺一即 Fail-Closed）：
  1. openclaw 调用证据（command + return code + session 映射）；
  2. 关键 phase 输出引用存在且可追溯；
  3. 拟真 case 报告，且包含失败路径与回退路径断言。

### D4 低字段负担原则

- 不引入大规模新增业务字段协议。
- 通过“证据文件存在性 + 最小结构校验”实现强约束。
- 把校验逻辑集中到统一 verifier，避免多处口径漂移。

## 3. 方案对比

### 方案 A（推荐）：门禁证据反查中枢

- 在最终 gate 聚合点增加统一 verifier。
- verifier 只做证据反查与完整性校验。
- 任何 simulated/skeleton 结果若无法满足真实证据链，自动不通过。

优点：
- 判定口径单点统一；
- 抗“字段伪装”能力强；
- 维护成本低于分散校验。

风险：
- 初次接入需要梳理证据索引与引用路径。

### 方案 B：分散到各 runner 各自校验

优点：局部改动快。

缺点：
- 口径易漂移；
- 复用和审计困难；
- 容易出现“某 runner 放松导致漏检”。

## 4. 实施顺序（按优先级 B > A）

1. 先落地门禁证据反查中枢（先堵住 simulated/skeleton 准入风险）；
2. 统一证据默认路径口径为 `tmp/runtime_data/...`（文档与脚本对齐）；
3. 清理 runner 描述与默认行为，消除“骨架/模拟被误当准入能力”的表达。

## 5. 验收标准

当且仅当以下全部满足，门禁可给出通过：

1. 可回放 openclaw 真实调用链路（含 session 映射）；
2. 关键 phase 输出可逐跳追溯；
3. 拟真 case 覆盖 Happy + 失败路径 + 回退路径，并断言通过；
4. 证据落盘在 `tmp/runtime_data/...`，且索引可定位。

若任一条件不满足，输出 `fail`（Fail-Closed）。
