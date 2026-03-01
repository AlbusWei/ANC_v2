# meta-skill-creator 别名策略

## 策略定义

1. 运行入口：`meta-skill-creator`（唯一允许）。
2. 历史别名：`skill-creator`（仅历史说明，不允许在仓库调用命令中使用）。
3. 稳定标识：`skill_id=meta.arch.skill-creator` 保持不变。

## 软禁用规则（仓库内）

1. 文档、脚本、流程示例中禁止出现 `openclaw skills info skill-creator` 作为调用指令。
2. 若需提及旧名，仅能在“历史别名说明”语境出现。
3. 新增资产一律使用 `meta-skill-creator`。

## 影响范围

1. 本策略仅作用于当前仓库。
2. 全局 OpenClaw managed skill 不做删除或硬禁用。
