# M2 BPM Runtime Hardening Live Regression Cases

## 目标

本清单用于 `tests/m2-bpm-runtime/run_post_dev_regression.py` 的 live 回归输入，确保线上可达性与 W1/W2/W3/W3-B/W5 关键链路在收口回合可追溯、可复核、可 Fail-Closed。

## 用例矩阵

| 套件 | 回归目标 | 入口命令 | 证据输出 |
|---|---|---|---|
| Online `TC-ONLINE-001~004` | OpenClaw 网关/工作区/核心 agent 与技能可达 | `python3 tests/m2-bpm-runtime/run_tc_online.py` | `docs/design/modules/evidence/bpm-runtime/live-regression/latest/w0_tc_online_report.json` |
| W1 `TC-INS-001~005` | 实例生成/迁移/回放链路可运行 | `python3 tests/m2-bpm-runtime/run_tc_ins.py --run-live-migration` | `docs/design/modules/evidence/bpm-runtime/live-regression/latest/w1_*` |
| W2 `TC-GCC-001~003` | 配置治理门禁与更新器回滚闭环 | `python3 tests/m2-bpm-runtime/run_tc_gcc.py` | `docs/design/modules/evidence/bpm-runtime/live-regression/latest/w2_*` |
| W3 `TG-SCH-001~004` `TG-EVT-001~003` | Trigger Runtime 调度/去重/补跑链路可运行 | `python3 tests/m2-bpm-runtime/run_tc_tg.py` | `docs/design/modules/evidence/bpm-runtime/live-regression/latest/w3_*` |
| W3-B `TC-QA-PROC-001~002` | QA 三流程调度链路可运行 | `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py` | `docs/design/modules/evidence/bpm-runtime/live-regression/latest/w3b_*` |
| W5 `TC-ANL-001~003` | `system-analyst` + `runtime-policy-calibration` 生产链路可运行 | `python3 tests/m2-bpm-runtime/run_tc_anl.py` | `docs/design/modules/evidence/bpm-runtime/live-regression/latest/w5_*` |

## 门禁规则

1. `docs/design/modules/evidence/bpm-runtime/checkpoint_commit_map.jsonl` 必须存在且为非空 JSONL。
2. `docs/design/modules/evidence/bpm-runtime/git_range.txt` 必须包含 `base_commit/head_commit/range`。
3. `git_range` 范围内每个 commit 必须存在 `Entire-Checkpoint` trailer 且在 checkpoint map 中可对账。
4. 任一关键文件缺失或任一套件失败即 Fail-Closed，回归结果必须为 `failed`。
