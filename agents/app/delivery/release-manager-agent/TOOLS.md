# Release-Manager-Agent - TOOLS

## Bound Skills

1. `sys.admin.release-manager`（核心）
2. `sys.qa.registry-validator`（发布前合规复核）

## Participating Processes

1. `full-development`（release-packaging）
2. `hotfix`（release-packaging）
3. `delivery-iterations`（外部交付复用场景）

## Fail-Closed

1. 任一前置证据缺失 -> 直接拒绝。
2. registry 校验失败 -> 直接拒绝并升级。
3. rollback bundle 不可用 -> 直接拒绝。
4. 输出结构不完整 -> 禁止向下游交付。

## 运行入口

```bash
# 成功分支（release_delivery_out）
python3 agents/app/delivery/release-manager-agent/scripts/release_manager_agent_runner.py \
  --input tmp/session5/release_manager_agent_input_success.json \
  --output tmp/session5/release_manager_agent_output_success.json \
  --evidence-dir tmp/session5/release_manager_agent_evidence_success

# 拒绝分支（release_reject_out）
python3 agents/app/delivery/release-manager-agent/scripts/release_manager_agent_runner.py \
  --input tmp/session5/release_manager_agent_input_reject.json \
  --output tmp/session5/release_manager_agent_output_reject.json \
  --evidence-dir tmp/session5/release_manager_agent_evidence_reject
```

## 返回码语义

1. `0`：交付成功，输出 `release_delivery_out`。
2. `2`：Fail-Closed/拒绝，输出 `release_reject_out`。
3. `1`：运行异常（非业务拒绝）。
