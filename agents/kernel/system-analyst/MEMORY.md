# System Analyst - MEMORY

## Memory Policy

1. 仅持久化可审计摘要，不持久化敏感原始数据。
2. 跨会话传递通过 `architecture_feedback_digest_ref` 与 reject 记录。
3. 若上游证据补齐，需生成新 digest，不覆盖历史判定记录。

## Storage

- Working memory: `runtime_data/agent-memory/system-analyst/`
- Evidence linkouts: `runtime_data/execution/evidence/bpm-runtime/`
