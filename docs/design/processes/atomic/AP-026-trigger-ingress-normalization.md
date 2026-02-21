# AP-026 Trigger Ingress Normalization

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.trigger-ingress-normalizer
- Input:
  - trigger_type
  - trigger_source
  - payload_ref
  - received_at
- Output:
  - canonical_trigger_ref
  - normalization_report_ref
- Fail-Closed:
  - 不支持的 trigger_type -> `fail`
  - payload 字段缺失或不可达 -> `fail`
- Evidence:
  - normalization_report_ref
