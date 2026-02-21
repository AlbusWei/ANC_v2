# AP-027 Trigger Match and Dedupe

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.trigger-matcher-dedupe
- Input:
  - canonical_trigger_ref
  - match_policy_ref
  - dedupe_policy_ref
- Output:
  - match_result
  - dedupe_decision
  - dedupe_key_ref
- Fail-Closed:
  - 去重冲突不可判定 -> `fail`
  - 目标流程不存在 -> `fail`
- Evidence:
  - matcher_evidence_ref
  - dedupe_key_ref
