# System Analyst - TOOLS

## Allowed Skills

- sys.arch.system-feedback-digest

## Related Skills (Cross-Agent)

- system.ops.manual-task (owner: bpm)
- sys.arch.construction-audit (owner: architect)

## Responsibilities

1. 校验 role-handoff 输入契约与证据可达性。
2. 输出 `architecture_feedback_digest_ref` 或 `reject_ref`。
3. 在 runtime-policy-calibration 中为 architect/admin/bpm 提供决策输入。

## Usage Notes

1. `to_role` 必须是 `system-analyst`。
2. `evidence_ref` 索引为空或不可达时必须拒绝。
3. 拒绝输出必须包含 `reason_code` 与可审计引用。
