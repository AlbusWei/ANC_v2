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
