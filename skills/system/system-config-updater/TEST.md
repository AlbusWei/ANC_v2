# system-config-updater - Test Cases

## Objective Alignment

验证配置补丁执行遵循 hash 安全和失败回滚约束。

## Test Cases

### TC-001: 正常补丁执行

- Type: Objective
- Priority: P0
- Input: 有效 `base_hash` 与 `patch_raw`
- Expected: 输出 `hash_before/hash_after/execution_status/receipt_ref`
- Evaluation Method: Exact Match

### TC-002: hash 不匹配 fail-closed

- Type: Objective
- Priority: P0
- Input: 过期 `base_hash`
- Expected: 执行失败并输出回滚状态
- Evaluation Method: Exact Match

## Runtime Suite Mapping

- M2 W2 运行级拒绝分支：`tests/m2-bpm-runtime/TC-GCC.md#tc-gcc-002-expired-basehash-must-be-rejected`
