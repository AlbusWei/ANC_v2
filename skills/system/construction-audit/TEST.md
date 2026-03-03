# construction-audit - Test Cases

## Objective Alignment

验证施工联动审计技能能够识别缺口并在证据不足时 Fail-Closed。

## Test Cases

### TC-001: 联动完整时输出可闭合报告

- Type: Objective
- Priority: P0
- Input: 提供完整 `round_id/scope_baseline_ref/changed_assets/linkage_targets/superpower_ref`
- Expected: 产出 `linkage_report_ref`，`missing_items=[]`，`blocking_risks=[]`
- Evaluation Method: Exact Match

### TC-002: 缺少 registry 目标时拒绝通过

- Type: Objective
- Priority: P0
- Input: `linkage_targets` 不含 registry 范围
- Expected: 返回失败并标记阻断项
- Evaluation Method: Exact Match

### TC-003: 证据引用不可达触发 Fail-Closed

- Type: Objective
- Priority: P1
- Input: `scope_baseline_ref` 指向不存在路径
- Expected: 返回失败并记录不可达证据引用
- Evaluation Method: Exact Match

### TC-004: 架构回合缺失 Superpower 映射触发 Fail-Closed

- Type: Objective
- Priority: P0
- Input: 架构边界变更但不提供 `superpower_ref`
- Expected: 返回失败并标记同步阻断项
- Evaluation Method: Exact Match

### TC-005: 仓库外绝对输出路径不应导致崩溃

- Type: Objective
- Priority: P0
- Input: `--output /tmp/...` 且其他输入合法
- Expected: 返回 `0` 或 `3`（取决于判定），标准输出为输出路径，不得抛异常
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 900
- Retry Policy: max 1
