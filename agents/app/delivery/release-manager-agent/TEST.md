# release-manager-agent - Test Plan

## 覆盖目标

1. 主链路：输入契约完整且前置证据可达时，产出 `release_delivery_out`。
2. Fail-Closed：输入缺字段或关键前置证据不可达时，产出 `release_reject_out`。
3. 分支完备：成功/拒绝双分支均可稳定复现且可追溯。

## 最小用例

1. TC-RMA-001: Happy path，返回 `0`，输出 `release_delivery_out`。
2. TC-RMA-002: 输入缺失 `release_request_in` 必填字段，返回 `2`，输出 `release_reject_out`。
3. TC-RMA-003: `final_gate_verdict_ref` 不可达，返回 `2`，输出 `release_reject_out`。
4. TC-RMA-004: `registry_sync_ref` 指向失败证据，返回 `2`，输出 `release_reject_out`。

## Runner 执行与返回码约定

### 成功分支示例

```bash
python3 agents/app/delivery/release-manager-agent/scripts/release_manager_agent_runner.py \
  --input tmp/session5/release_manager_agent_input_success.json \
  --output tmp/session5/release_manager_agent_output_success.json \
  --evidence-dir tmp/session5/release_manager_agent_evidence_success
```

### 拒绝分支示例

```bash
python3 agents/app/delivery/release-manager-agent/scripts/release_manager_agent_runner.py \
  --input tmp/session5/release_manager_agent_input_reject.json \
  --output tmp/session5/release_manager_agent_output_reject.json \
  --evidence-dir tmp/session5/release_manager_agent_evidence_reject
```

返回码语义：

1. `0`：交付成功，输出 `release_delivery_out`。
2. `2`：拒绝分支（Fail-Closed），输出 `release_reject_out`。
3. `1`：运行异常。
