# Runtime Data 隔离区（默认不入库）

本目录用于承接 ANC v2 运行时产生的非通用数据，默认不纳入 Git 版本控制。

## 目录用途

1. `runtime_data/execution/evidence/`
   - 运行流程的证据包、phase trace、stdout/stderr、临时报告。
2. `runtime_data/business/`
   - 业务执行中的输入样本、回放数据、沙盒数据。
3. `runtime_data/agent-memory/`
   - Agent 当日工作记忆与短期状态快照。
4. `runtime_data/private-assets/`
   - 非标准发布资产（私有/实验/验证用）：
   - `runtime_data/private-assets/agents/`
   - `runtime_data/private-assets/skills/`
   - `runtime_data/private-assets/processes/`
   - 可选 OpenClaw overlay：`runtime_data/private-assets/openclaw.overlay.json`
5. `runtime_data/exports/`
   - 需要人工筛选后再沉淀到仓库的候选材料（默认仍不入库）。

## 使用规则（强制）

1. 默认写入：所有流程执行产物与业务数据默认写入本目录。
2. 显式白名单：只有经过脱敏与治理审批的案例/模板，才允许复制到仓库公开目录（例如 `docs/design/modules/evidence/`）。
3. 禁止回写：不得将个人私有信息、真实业务数据直接写入 `docs/`、`agents/`、`skills/`、`processes/` 等版本控制目录。
4. 非标准资产隔离：临时 Agent/Skill/Process 资产必须放在 `runtime_data/private-assets/`，禁止注册到 `shared/registry/*.json`。
