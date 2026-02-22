# AP-028 Trigger Dispatch and Instance Start

> 版本: v0.2.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.process-instance-manager
- Input:
  - process_id
  - phase_id
  - dispatch_input_ref
  - lineage_ref
  - stack_depth
  - process_version
  - process_level
  - session_binding
- Output:
  - instance_id
  - dispatch_receipt_ref
  - session_binding_ref
- Fail-Closed:
  - process_id 未注册或不可执行 -> `fail`
  - 上下文隔离校验失败 -> `fail`
  - 会话绑定缺失或父子 session 复用 -> `fail`
- Evidence:
  - dispatch_receipt_ref
  - state_transition_ref
