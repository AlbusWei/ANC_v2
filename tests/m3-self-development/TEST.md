# M3 Self-Development Meta 资产在线 QA 测试基座（Phase5）

## 1. 测试目标与范围

本测试基座服务于变更 `m3-meta-asset-quality-hardening` 的 Phase5，采用 QA 主导闭环：

1. `计划 -> 用例 -> 执行 -> 缺陷 -> 回归`。
2. 以 `openclaw` 在线运行行为为主验收，静态校验仅作辅助。
3. 覆盖全量 Meta 资产：
   - 8 个 Meta Skills（`meta.*`）
   - 20 个 Meta Processes（`processes/meta/*` 且已在 registry 登记）
4. 每个具体资产固定覆盖四类场景：`HP/FC/TR/RB`。

## 2. QA 闭环流程

### 2.1 Plan（计划）

1. 以 registry 为唯一资产发现入口，不手工维护资产名单。
2. 每个资产自动展开四类场景：
   - `HP`（Happy）
   - `FC`（Fail-Closed）
   - `TR`（Traceability）
   - `RB`（Rollback/Recovery）
3. 生成标准 case 对象（输入载荷、预期输出、判定规则、失败码、契约引用）。

### 2.2 Case（用例）

1. 每个 case 必须可回链到：
   - 资产契约文档（`SKILL.md` / `process.json`）
   - registry 记录（`skill_registry.json` / `process_registry.json`）
2. 每个流程资产至少包含一条 `openclaw agent --agent qa` 在线调用场景。
3. Runner 复用优先：
   - Skill runner 模式：`agent-creator`、`process-creator`、`template-validator`、`meta-skill-creator`
   - 已有上游复用：`tests/m1-runtime/run_post_dev_regression.py`、`tests/m3-runtime/run_skill_contract_validation.py`

### 2.3 Execute（执行）

统一入口：`tests/m3-self-development/run_meta_qa_online.py`

1. `--list-cases`：列出完整 case 清单。
2. `--dry-run`：仅检查可执行性、覆盖完整性、追溯完整性，不执行在线 case。
3. `run`：执行在线与 runner 场景并产出缺陷与回归输入。

### 2.4 Defect（缺陷）

缺陷记录固定字段：

1. `severity`：`P0|P1|P2`
2. `asset_id`
3. `scenario`
4. `reason_code`
5. `repro`
6. `evidence_ref`

分级规则：

1. `P0`：Happy/Fail-Closed 主判定失败、在线调用不可执行。
2. `P1`：Traceability/回退恢复断链。
3. `P2`：非阻断类补充改进项。

### 2.5 Regression（回归）

`final-regression` 采用分层执行：

1. 第一层：`online-critical`（每资产关键在线 + Fail-Closed）
2. 第二层：`final-regression-full`（全量矩阵）
3. 两层都通过才允许最终 `pass`。

## 3. 门禁规则（Fail-Closed）

任一命中即判失败并返回非零：

1. 仅有静态检查、没有在线场景。
2. 任一 case 无法追溯到具体资产与契约。
3. 任一流程资产缺少在线场景。
4. `--dry-run` 未产出自然语言结论（目标/覆盖/现象/风险/准入）。

返回码约定：

1. `0`：通过。
2. `2`：Fail-Closed（覆盖缺口/证据缺失/断言失败等）。
3. `1`：执行异常。

## 4. 证据目录规范

证据根目录：

`runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/`

运行结构：

1. `latest/`
2. `latest/runs/<run_id>/`
3. `latest/runs/<run_id>/cases/<case_id>/`

每轮固定输出：

1. `meta_qa_online_report.json`
2. `meta_qa_online_summary.md`
3. `defects.json`
4. `defect_summary.md`
5. `regression_plan.json`

每 case 固定证据：

1. `input.json`
2. `output.json`
3. `assertions.json`
4. `command_trace.json`
5. `stdout.txt`
6. `stderr.txt`

## 5. 运行命令

```bash
# 列出全量 case（应为 112）
python3 tests/m3-self-development/run_meta_qa_online.py --list-cases

# Phase5 门禁：只做可执行性与覆盖校验
python3 tests/m3-self-development/run_meta_qa_online.py --dry-run

# 按套件执行
python3 tests/m3-self-development/run_meta_qa_online.py --suite meta-skills
python3 tests/m3-self-development/run_meta_qa_online.py --suite online-critical
python3 tests/m3-self-development/run_meta_qa_online.py --suite final-regression
```

## 6. 准入判定（Phase5）

Phase5 准入只看两件事：

1. 在线用例是否可执行（运行入口、资产可见性、契约追溯完整）。
2. 覆盖是否满足（每资产四类场景 + 每流程在线场景）。

若任一未满足：`Phase5 = fail`，不得宣告 Done。
