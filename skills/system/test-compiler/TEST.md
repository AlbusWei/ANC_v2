# test-compiler - Test Cases

## Objective Alignment

验证 TEST 编译能力可稳定产出 datapoints、profile 绑定和编译证据。

## Test Cases

### TC-001: 编译成功并输出映射

- Type: Objective
- Priority: P0
- Input: 合法 `TEST.md` + baseline profile
- Expected: 产出 `test_datapoints_ref/tc_profile_map_ref/compile_report_ref`
- Evaluation Method: Exact Match

### TC-002: TEST 模板错误触发 test_invalid

- Type: Objective
- Priority: P0
- Input: 缺少必填字段的 `TEST.md`
- Expected: 返回 `test_invalid` 且 compile_report 记录错误
- Evaluation Method: Exact Match
