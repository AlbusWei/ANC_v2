# Self-Development Skills 设计包

> 版本: v0.5.0 | 分类: Meta Skills | 模块: M3 Self-Development | 最后更新: 2026-02-24

## 目标

定义 M3 反身自开发能力域的 8 个核心技能，统一升级到执行级资产标准，并完成 `skill-creator` 同名冲突治理。

关联文档：

1. `docs/design/modules/M3-self-development.md`
2. `docs/design/processes/full-development-process.md`
3. `docs/design/processes/hotfix-process.md`
4. `docs/design/processes/refactor-process.md`
5. `docs/design/standards/skill-definition-standard.md`

## 技能定义卡（Phase4 联动复核）

### 1. `meta.arch.objective-writer`

- 运行名：`objective-writer`
- 定位：将原始需求归一为可执行 Objective 契约。
- 输入契约：`objective_context`, `stakeholders`, `constraints`, `success_criteria`
- 输出契约：`objective_ref`, `objective_statement`, `success_criteria`, `scope_baseline`, `superpower_ref`, `non_goals`
- Fail-Closed：缺少可测成功标准、边界缺失、与 SSOT 冲突。
- 运行方式：文档化技能（无独立 runner）
- test_mount：`skills/meta/objective-writer/TEST.md`

### 2. `meta.arch.agent-creator`

- 运行名：`agent-creator`
- 定位：创建 Agent 设计资产并输出 registry patch 计划。
- 输入契约：`agent_id`, `role_scope`, `interfaces`, `owner`
- 输出契约：`agent_doc_path`, `tools_doc_path`, `registry_patch_plan`
- Fail-Closed：必填字段缺失、协议引用不可解析、owner 不合法。
- 运行方式：`python3 skills/meta/agent-creator/scripts/agent_creator_runner.py --input <json> --output <json> [--report <json>]`
- test_mount：`skills/meta/agent-creator/TEST.md`

### 3. `meta.arch.process-creator`

- 运行名：`process-creator`
- 定位：创建流程资产并强制 canonical schema、phase 闭合与 inline_ap 映射约束。
- 输入契约：`process_id`, `version`, `process_level`, `phases`, `control_flow`, `fail_policy`, `evidence_policy`, `lineage_policy`
- 输出契约：`process_manifest_path`, `process_skill_path`, `process_guide_path`, `registry_patch_plan`
- Fail-Closed：跨非连续生命周期段、phase 无映射、inline_ap 非法、`requires_spec=true` 且缺 `spec_ref`、`P4/P5/P6` 协作策略约束不满足、legacy 字段残留。
- 运行方式：`python3 skills/meta/process-creator/scripts/process_creator_runner.py --input <json> --output <json> [--report <json>]`
- test_mount：`skills/meta/process-creator/TEST.md`

### 4. `meta.arch.spec-writer`

- 运行名：`spec-writer`
- 定位：把 Objective 固化为可执行 Spec，明确验收与回退策略。
- 输入契约：`objective_ref`, `problem_statement`, `constraints`
- 输出契约：`scope`, `input_contract`, `output_contract`, `acceptance_criteria`, `risks`, `rollback_strategy`
- Fail-Closed：必填字段缺失、验收条款不可测试、与 SSOT 冲突。
- 运行方式：文档化技能（无独立 runner）
- test_mount：`skills/meta/spec-writer/TEST.md`

### 5. `meta.arch.template-validator`

- 运行名：`template-validator`
- 定位：在 lifecycle/registry handoff 前执行模板契约校验。
- 输入契约：`template_ref`, `schema_ref`, `target_asset_ref`, `validation_profile`
- 输出契约：`validation_report_ref`, `gate_decision`, `blocking_issues`
- Fail-Closed：关键引用缺失、schema 不匹配且不可安全修复、高风险问题未关闭。
- 运行方式：`python3 skills/meta/template-validator/scripts/template_validator_runner.py --input <json> --output <json> [--report <json>]`
- test_mount：`skills/meta/template-validator/TEST.md`

### 6. `meta.qa.test-designer`

- 运行名：`test-designer`
- 定位：在开发前产出可执行测试设计，覆盖主链路与异常链路。
- 输入契约：`objective_ref`, `spec_ref`, `risk_focus`
- 输出契约：`objective_alignment`, `test_cases`, `evaluation_config`, `traceability_map`
- Fail-Closed：关键引用缺失、P0 场景缺失、追溯图断裂。
- 运行方式：文档化技能（无独立 runner）
- test_mount：`skills/meta/test-designer/TEST.md`

### 7. `meta.qa.llm-judge`

- 运行名：`llm-judge`
- 定位：输出结构化判定结果并给出可执行整改建议。
- 输入契约：`objective`, `spec_ref`, `expected_conditions`, `actual_output_ref`
- 输出契约：`pass`, `confidence`, `remarks`, `suggestions`, `traceability`
- Fail-Closed：关键输入缺失、证据不可读、判定结果不可解析。
- 运行方式：文档化技能（无独立 runner）
- test_mount：`skills/meta/llm-judge/TEST.md`

### 8. `meta.arch.skill-creator`

- 运行名：`meta-skill-creator`
- 历史别名：`skill-creator`（仅历史说明，仓库内禁止调用）
- 定位：创建或重构 Skill 资产并输出 review 门禁可消费的产物。
- 输入契约：`skill_name`, `layer`, `namespace`, `objective_ref`
- 输出契约：`skill_md_path`, `test_doc_path`, `registry_patch_plan`, `review_evidence_ref`
- Fail-Closed：关键输入缺失、命名违规、生成物不满足 review 基线。
- 运行方式：`python3 skills/skill-creator/scripts/meta_skill_creator_runner.py --input <json> --output <json> [--report <json>]`
- test_mount：`tests/skill-creator/TEST.md`

## 生命周期与落盘状态

1. 本轮状态：8 个目标技能统一推进到 `review`。
2. 运行标准：4 个 creator/validator 技能具备统一 runner 契约（返回码 `0/2/1`）。
3. 冲突治理：`meta.arch.skill-creator` 完成运行名切换（`meta-skill-creator`）并落地仓库内软禁用策略。
4. 本轮上限：不推进任何目标技能到 `active`。
5. `shared/registry/skill_registry.json` 已完成联动复核，本回合字段无增量（no-delta）。
