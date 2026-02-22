# TC-GCC-001~003

## TC-GCC-001 Governed Patch + Rollback (Low Risk Live)

- Type: Objective
- Priority: P0
- Preconditions:
  - OpenClaw workspace 已切换到当前 worktree
  - 目标键位 `messages.groupChat.historyLimit` 可读写
- Input:
  - 完整 `governed-config-change` 请求（含 evidence_refs、authorization、rollback_plan）
  - `change_request.delta=+1`
- Expected:
  - 流程 verdict=`pass`
  - 真实写入成功并生成 `hash_before/hash_after_apply`
  - rollback 成功并恢复原值
  - 证据链完整：`request/gate/auth/receipt/verify`
- Evaluation Method: Exact Match

## TC-GCC-002 Expired baseHash Must Be Rejected

- Type: Objective
- Priority: P0
- Preconditions:
  - 获取当前 `config.get.hash`
- Input:
  - `system-config-updater` 入参使用过期 `base_hash`
  - 其他字段保持合法（含 authorization）
- Expected:
  - runner fail-closed（exit code=2）
  - 输出 `execution_status=failed`
  - `failure_code=base_hash_mismatch`
  - 配置 hash 不发生变化
- Evaluation Method: Exact Match

## TC-GCC-003 Missing Evidence Must Be Rejected

- Type: Objective
- Priority: P0
- Preconditions:
  - 目标键位维持默认低风险路径
- Input:
  - `governed-config-change` 请求中 `evidence_refs` 为空
- Expected:
  - 流程在 gate 阶段拒绝（verdict=`deny`）
  - gate 输出 `approval=deny` 且给出拒绝原因
  - 不进入 apply 阶段
- Evaluation Method: Exact Match
