---
name: "entire-codex-sync"
description: "Synchronize Codex development turns into Entire checkpoints by bridging Gemini lifecycle hooks; use when Codex tasks require Entire-Checkpoint linkage and session evidence."
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.1.0"
---

# entire-codex-sync

## Objective

为 Codex 场景提供 Entire 可追踪会话桥接能力，确保开发变更可生成 `Entire-Checkpoint` 并可回溯。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-phase1-entire-codex-sync
input_contract:
  format: command_invocation
  required:
    - prompt
    - summary
    - files
  validation:
    - current directory must be a git repository
    - entire status must be enabled
    - sync command must include prompt and summary
output_contract:
  format: git_trailer_and_local_artifacts
  required:
    - entire_checkpoint_trailer
    - bridge_session_state
    - bridge_transcript
  machine_judgement:
    - git log includes Entire-Checkpoint trailer after commit
    - .entire/codex-bridge/session.json exists
    - .entire/codex-bridge/transcript.json exists
fail_closed_rules:
  - entire command unavailable or not enabled
  - repository preconditions fail
  - bridge script returns non-zero exit
test_mount:
  test_doc: /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/TEST.md
  methodology_ref: /Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md
references:
  bridge_contract: /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/references/bridge-contract.md
```

## Input Contract

- Format: command invocation
- Required fields:
  - prompt
  - summary
  - files (recommended)
- Validation:
  - 当前目录必须是 Git 仓库
  - `entire status` 必须为 enabled

## Output Contract

- Format: git trailer + local evidence files
- Required fields:
  - commit trailer: `Entire-Checkpoint: <id>`
  - bridge state: `.entire/codex-bridge/session.json`
  - bridge transcript: `.entire/codex-bridge/transcript.json`

## Runtime Rules

1. Fail-Closed：`entire` 不可用、repo 不合法、hook 失败时立即失败。
2. 每个有意义开发回合都执行一次 `sync`，不要只在最终提交前执行。
3. 每次提交后必须校验 trailer 是否存在。
4. 完整任务结束后执行 `end` 关闭桥接会话。

## Execution Steps

1. 启动/复用会话：
   - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
2. 同步开发回合：
   - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "<需求>" --summary "<实现摘要>" --files <file1> <file2>`
3. 提交并验证：
   - `git commit ...`
   - `git log -1 --pretty=raw`（检查 `Entire-Checkpoint`）
4. 结束会话：
   - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py end`

## Observability

- Status command:
  - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py status`
- Contract reference:
  - `/Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/references/bridge-contract.md`
