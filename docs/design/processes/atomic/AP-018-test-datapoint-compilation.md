# AP-018 Test Datapoint Compilation

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.test-compiler
- Input:
  - test_doc_ref
  - objective_ref
  - spec_ref
- Output:
  - test_datapoints_ref
  - compile_report_ref
- Fail-Closed:
  - `TEST.md` 不可解析 -> `test_invalid`
  - 编译结果与测试用例数量不一致 -> `fail`
  - 关键字段缺失 -> `test_invalid`
- Evidence:
  - compile_report_ref
  - test_datapoints_ref
