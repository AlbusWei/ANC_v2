# Runtime Validation Round (Meta Assets)

本目录用于沉淀 `m3-meta-asset-quality-hardening` Phase5/Phase6 的在线运行验证证据。

目录约定：

1. `latest/`：最新一轮执行的聚合报告与回归计划。
2. `latest/runs/<run_id>/`：按轮次归档的原始执行证据。
3. `latest/runs/<run_id>/cases/<case_id>/`：单用例证据目录。

每轮固定产物：

1. `latest/meta_qa_online_report.json`
2. `latest/meta_qa_online_summary.md`
3. `latest/defects.json`
4. `latest/defect_summary.md`
5. `latest/regression_plan.json`

每个 case 固定证据：

1. `input.json`
2. `output.json`
3. `assertions.json`
4. `command_trace.json`
5. `stdout.txt`
6. `stderr.txt`
