# AP-008 Subjective Evaluation

> 版本: v0.4.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.evaluation-runner（A/B subjective mode）
- Input:
  - preparation_bundle_ref
  - actual_output_refs（多版本对比）
  - subjective_test_plan（按复杂度定义轮次；9 轮仅推荐）
  - random_seed
- Bundle dereference:
  - tc_profile_map_ref
- Execution:
  - 强制盲测，随机化 X/Y
  - 记录 seed、轮次与样本标识，保证可复现
- Output:
  - subjective_eval_ref
  - subjective_verdict（`accept|reject|review`）
  - win_rate
- Decision:
  - 新版胜率 `>= 2/3`：接受
  - 新版胜率 `< 1/2`：拒绝
  - 中间区间：升级 `architect + admin` 审查
- Fail-Closed:
  - 样本污染
  - seed 缺失或不可复现
  - 计划轮次与执行记录不一致
- Evidence:
  - subjective_eval_ref
  - subjective_seed_ref
