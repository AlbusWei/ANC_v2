# Self-Development Skills 设计包

> 版本: v0.3.0 | 分类: Meta Skills | 模块: M3 Self-Development | 最后更新: 2026-02-23

## 目标

定义 M3 反身自开发能力域的技能集合，覆盖 objective 定义、资产创建与模板契约校验。

关联文档：

1. `docs/design/modules/M3-self-development.md`
2. `docs/design/processes/full-development-process.md`
3. `docs/design/processes/hotfix-process.md`
4. `docs/design/processes/refactor-process.md`
5. `docs/design/standards/skill-definition-standard.md`

## 技能定义卡

### 1. meta.arch.objective-writer

- 定位：将原始需求归一为可执行 Objective 契约。
- 输入契约：`objective_context`, `stakeholders`, `constraints`, `success_criteria`
- 输出契约：`objective_ref`, `objective_statement`, `scope_baseline`, `non_goals`
- Fail-Closed：缺少可测成功标准、缺少范围边界、与系统约束冲突。
- test_mount：`skills/meta/objective-writer/TEST.md`

### 2. skill-creator

- 定位：创建/更新 Skill 资产并给出 registry patch 计划。
- 输入契约：`skill_name`, `objective_ref`, `scope`, `constraints`
- 输出契约：`skill_md_path`, `test_doc_path`, `registry_patch_plan`
- Fail-Closed：关键输入缺失、frontmatter 不可解析、test path 缺失。
- test_mount：`tests/skill-creator/TEST.md`

### 3. meta.arch.agent-creator

- 定位：创建 Agent 设计资产并生成可审计 registry patch 计划。
- 输入契约：`agent_id`, `role_scope`, `interfaces`, `owner`
- 输出契约：`agent_doc_path`, `tools_doc_path`, `registry_patch_plan`
- Fail-Closed：身份/owner 缺失、协议引用无效、registry patch 字段不完整。
- test_mount：`skills/meta/agent-creator/TEST.md`

### 4. meta.arch.process-creator

- 定位：创建流程资产并落实连续性与 phase 闭合约束。
- 输入契约：`process_id`, `process_level`, `phases`, `control_flow`, `fail_policy`
- 输出契约：`process_manifest_path`, `process_skill_path`, `process_guide_path`
- Fail-Closed：生命周期段硬拼、phase 未闭合、fail_policy 缺失。
- test_mount：`skills/meta/process-creator/TEST.md`

### 5. meta.arch.template-validator

- 定位：在 lifecycle/registry handoff 前执行模板与契约校验。
- 输入契约：`template_ref`, `schema_ref`, `target_asset_ref`, `validation_profile`
- 输出契约：`validation_report_ref`, `gate_decision`, `blocking_issues`
- Fail-Closed：schema 缺失、必填字段不匹配、阻断问题未解。
- test_mount：`skills/meta/template-validator/TEST.md`

## 系统治理依赖技能（Session3 运行落地）

> 本节契约与运行资产已对齐，生命周期继续保持 `draft`，不越级到 `active`。

### 6. sys.arch.impact-analyzer（依赖）

- 引用来源：`docs/design/skills/system-skills.md`
- 在 M3 中的使用点：
  1. `full-development` 的变更前影响评估。
  2. `refactor` 的风险/回滚边界判定。
  3. 元层自修改链路的 Step 2 影响分析。
- 输入接口（固定）：
  - `change_proposal_ref`
  - `affected_scope_ref`
  - `risk_constraints_ref`
- 输出接口（固定）：
  - `impact_report_ref`
  - `risk_level`
  - `rollback_requirements`
  - `gating_recommendation`
- Fail-Closed：影响范围不可达或风险冲突未裁决时拒绝放行。
- test_mount（运行入口）：`skills/system/impact-analyzer/TEST.md` + `tests/m3-runtime/run_skill_contract_validation.py`
- 生命周期预期：`draft`

### 7. sys.admin.release-manager（依赖）

- 引用来源：`docs/design/skills/system-skills.md`
- 在 M3 中的使用点：
  1. `full-development/hotfix` 的 `release-packaging` 阶段。
  2. `release-manager-agent` 的默认核心能力。
- 输入接口（固定）：
  - `candidate_artifacts_ref`
  - `final_gate_verdict_ref`
  - `lifecycle_transition_ref`
  - `registry_sync_ref`
- 输出接口（固定）：
  - `release_package_ref`
  - `changelog_ref`
  - `release_decision`
  - `rollback_bundle_ref`
- Fail-Closed：门禁证据缺失或回滚包不可用时拒绝发布。
- test_mount（运行入口）：`skills/system/release-manager/TEST.md` + `tests/m3-runtime/run_skill_contract_validation.py`
- 生命周期预期：`draft`

## 生命周期与落盘状态

1. 本轮状态：M3 5 个关键技能已形成资产并接入 registry（状态 `draft`）。
2. 激活前置：
   - 对应 `SKILL.md/TEST.md` 资产通过 capability contract 校验
   - `registry_contract_tool.py verify` 通过
   - 与 `full-development/hotfix/refactor` I/O 契约一致
3. Session3 实现闭合：
   - `sys.arch.impact-analyzer`、`sys.admin.release-manager` 已落地运行目录与最小可执行 runner，并纳入 `tests/m3-runtime` 统一验证入口。
