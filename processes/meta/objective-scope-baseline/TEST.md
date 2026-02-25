# objective-scope-baseline - Test Plan

## 覆盖目标

1. 主链路：输入 `objective_context_ref` 后产出 `objective_ref/scope_baseline_ref`。
2. Fail-Closed：缺失输入或冲突上下文时拒绝推进。
3. 可追溯：阶段输出与证据字段可回放。

## 最小用例

1. TC-OSB-001: Happy path。
2. TC-OSB-002: 缺失 `objective_context_ref`。
3. TC-OSB-003: 上下文冲突导致阻断。

## Runner 执行与返回码约定

### Happy Path 示例

```bash
python3 processes/meta/objective-scope-baseline/scripts/objective_scope_baseline_runner.py \
  --input tmp/session5/objective_scope_input.json \
  --output tmp/session5/objective_scope_output.json \
  --evidence-dir tmp/session5/objective_scope_evidence
```

### Fail-Closed 示例（缺失 `objective_context_ref`）

```bash
python3 processes/meta/objective-scope-baseline/scripts/objective_scope_baseline_runner.py \
  --input tmp/session5/objective_scope_input_missing_ref.json \
  --output tmp/session5/objective_scope_output_missing_ref.json \
  --evidence-dir tmp/session5/objective_scope_evidence_missing_ref
```

### 返回码语义

1. `0`：通过，输出包含 `objective_ref/scope_baseline_ref`。
2. `2`：Fail-Closed，输入缺失、引用不可达或子流程失败。
3. `1`：运行异常。
