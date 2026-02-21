# AP-028 Trigger Dispatch and Instance Start

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.process-instance-manager
- Input:
  - process_id
  - dispatch_input_ref
  - lineage_ref
- Output:
  - instance_id
  - dispatch_receipt_ref
- Fail-Closed:
  - process_id 未注册或不可执行 -> `fail`
  - 上下文隔离校验失败 -> `fail`
- Evidence:
  - dispatch_receipt_ref
  - state_transition_ref
