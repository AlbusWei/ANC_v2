# M6 Construction-Plane Runtime Evidence Index

> Round set: 2026-02-21 | Runner: `processes/meta/construction-plane-governance/scripts/run_round.py`

## 主场景结果

| 场景 | round_id | 结果 | 关键结论 | 结果文件 |
|---|---|---|---|---|
| A (正常回合) | `R-20260221-M6-m6-construction-round-sync-11` | PASS | `p1 -> p5` 全链路通过，输出包完整 | `docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-11/round-result.json` |
| B (计数冲突) | `R-20260221-M6-m6-construction-round-sync-12` | FAIL | `p5` 对账阻断（`checkpoint_count != commit_count`） | `docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-12/round-result.json` |
| C (语义冲突未裁决) | `R-20260221-M6-m6-construction-round-sync-13` | FAIL | `p4` OpenSpec 同步冲突阻断 | `docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-13/round-result.json` |

## M6 门禁负例（verify-m6）

| 负例 | 目录 | 阻断原因 |
|---|---|---|
| 多 `openspec_ref` | `docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-14/` | round evidence 出现多个 `openspec_ref` |
| 缺 checkpoint 事件 | `docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-15/` | `round_close checkpoint_count` 与 checkpoint 事件数量不一致 |
| 缺 round_close（由 p4 提前失败导致） | `docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-13/` | round evidence 缺失终止事件 |

## 可追溯命令

1. `python3 shared/registry/registry_contract_tool.py verify`
2. `python3 shared/registry/registry_contract_tool.py verify-m6 --round-dir docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-11`
3. `python3 shared/registry/registry_contract_tool.py verify-m6 --round-dir docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-12`
4. `python3 shared/registry/registry_contract_tool.py verify-m6 --round-dir docs/design/modules/evidence/construction-plane/R-20260221-M6-m6-construction-round-sync-13`

## 开发后补测（Round 6）

- 测试计划：`tests/m6-governance/TEST.md`
- 执行脚本：`tests/m6-governance/run_post_dev_regression.py`
- 补测结果：`docs/design/modules/evidence/construction-plane/runtime-validation-round-6/outputs/regression_report.json`
- 补测摘要：`docs/design/modules/evidence/construction-plane/runtime-validation-round-6/outputs/regression_summary.md`
- Gate 决策：`pass`（13/13 通过，生成时间 `2026-02-22T10:50:51Z`）
