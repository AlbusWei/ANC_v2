# M3 Self-Development Session4 测试基座

## 目标

本测试基座用于 `m3-self-development-e2e-online` 的 Session4，作为 Session5/Session6 内外主线 E2E 的统一可复用入口。

核心约束：

1. 采用单 runner：`tests/m3-self-development/run_tc_online.py`。
2. 通过 `--suite/--case` 做执行选择，默认执行 Session4 四类基座用例。
3. 复用既有评测能力，不重复实现评测引擎：
   - `tests/m3-runtime/run_skill_contract_validation.py`
   - `tests/m1-runtime/run_post_dev_regression.py`

## 覆盖范围

### 1. 主链路（Happy Flow，最高优先级）

- Case: `M3-S4-HAPPY-001`
- 目标：验证 Session3 落地的 `impact-analyzer/release-manager` 主链路可运行，作为后续 E2E 的基础前提。

### 2. 异常链路（Exception）

- Case: `M3-S4-EXC-001`
- 目标：验证 `M3 -> M1` 门禁链中 `hold` 路由可达，异常并非静默通过。

### 3. Fail-Closed

- Case: `M3-S4-FC-001`
- 目标：验证关键输入异常时链路阻断生效（`fail_closed`），并可追溯证据。

### 4. 回退/返工（Rollback/Rework）

- Case: `M3-S4-RW-001`
- 目标：验证 release-manager 的拒绝/阻断分支（回退包缺失、registry 同步失败）被正确触发。

## 入口与证据

- Runner: `tests/m3-self-development/run_tc_online.py`
- 默认证据根目录：`docs/design/modules/evidence/self-development/e2e-online/session4-foundation/latest`
- 固定结构：
  - `upstream/m3-runtime/`
  - `upstream/m1-runtime/`
  - `cases/<case_id>/`
  - `session4_tc_online_report.json`
  - `session4_tc_online_summary.md`

## Session5/Session6 预留

在 `tests/m3-self-development/live_cases.md` 预留并注册以下 case id，本会话仅登记，不执行：

1. `M3-INT-001~003`（Session5 内部主线）
2. `M3-EXT-001~003`（Session6 外部主线）
3. `M3-FC-101~103`（跨主线 Fail-Closed/旁路阻断）

若在 Session4 强制执行上述预留 case，runner 必须 Fail-Closed 返回非零。

## Fail-Closed 策略

1. 未知 suite 或未知 case：立即失败。
2. 选中 reserved case：立即失败（提示仅 Session5/Session6 可执行）。
3. 上游 runner 返回非零、报告缺失或关键断言不成立：立即失败。
4. 默认基座执行未覆盖四类判定（happy/exception/fail-closed/rollback）：立即失败。

## 建议命令

```bash
# Session4 基座全量（默认）
python3 tests/m3-self-development/run_tc_online.py

# 查看用例清单
python3 tests/m3-self-development/run_tc_online.py --list-cases

# 按 suite 执行
python3 tests/m3-self-development/run_tc_online.py --suite session4-happy,session4-rollback

# 按 case 执行
python3 tests/m3-self-development/run_tc_online.py --case M3-S4-HAPPY-001
```
