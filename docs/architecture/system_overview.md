# ANC v2 系统架构总览（SSOT）

最后更新：2026-02-18  
版本：2.0.1-alpha

> 本文档是 ANC v2 的架构唯一信源（SSOT）。
> 任何架构级变更必须先修改本文件，再修改实现与资产。

## 1. 执行摘要

ANC v2 的核心目标是构建一个可反身自开发、可自进化、可审计回放的 Agentic 组织系统。

1. 反身自开发（Reflexive Self-Development）：系统既开发自己，也被自己开发。
2. 自进化（Self-Evolution）：系统基于运行反馈持续识别问题并触发改进。
3. 人机协同渐进移交：Phase 0 由人类主导塑形，后续逐步移交给系统内 Agent。

## 2. 本版补强（反思结论）

本次补强用于修复上一版文档的信息缺口，重点新增：

1. 元层与对象层的明确分离与反身性边界。
2. L0-L5 六层架构和层间依赖方向。
3. M1-M6 模块分解与建设顺序。
4. 元层自修改门禁链路（提案到回滚）。
5. Phase 路线、里程碑和“当前明确不做”边界。

## 3. 因果驱动链与冲突裁决

ANC v2 保留“三驱动”术语，但执行上采用因果链：

`Objective -> Spec -> Test -> Development`

冲突优先级固定为：

`Objective > Spec > Test > Implementation`

执行规则：

1. Objective 定义“为什么做、做到什么程度”。
2. Spec 形式化 Objective，定义边界、约束、输入输出。
3. Test 可验证化 Spec，并覆盖 Objective 的核心意图。
4. 实现层不得反向改变 Objective（即不得“因为难做而降目标”）。

## 4. 三类一等对象（内部产品）

1. Agent：角色化执行体，具备身份、职责、权限与协作边界。
2. Skill：最小能力单元，具备输入输出契约与行为规范。
3. Process：多 Actor 协作编排（可视作特殊 Skill，但独立治理）。

统一生命周期：

`Draft -> Review -> Active -> Deprecated -> Retired`

每次状态迁移必须绑定：

1. 输入约束
2. 验证动作
3. 证据产物
4. 负责人
5. 回滚路径

## 5. 元层与对象层

| 层级 | 定义 | 示例 |
|---|---|---|
| Meta Layer（元层） | 用来创建、测试、管理其他内部产品的能力 | `skill-creator`、`development-process`、`qa-agent` |
| Object Layer（对象层） | 对外交付业务价值的能力 | 业务技能、业务流程、业务 Agent |

反身性规则：

1. 元层本身也是内部产品，受同一生命周期治理。
2. 元层允许自修改，但必须经过门禁链路。
3. 未通过门禁的元层修改禁止进入 Active。

## 6. 系统分层（L0-L5）

```text
L5 Business Delivery Layer
L4 Self-Evolution Layer
L3 Self-Development Layer
L2 Orchestration & Governance Layer
L1 Capability Layer
L0 Infrastructure Layer
```

各层职责：

1. L0：OpenClaw runtime、CLI、session、文件系统、模型接口。
2. L1：Skill/Agent/Process 定义与模板资产。
3. L2：BPM、Registry、权限治理、生命周期治理。
4. L3：需求 -> Spec -> Test -> Dev -> Verify -> Release 的开发闭环。
5. L4：监控 -> 分析 -> 规划 -> 触发开发的运营闭环。
6. L5：业务交付与外部价值实现。

依赖方向：上层依赖下层，下层不依赖上层。

## 7. 模块分解（M1-M6）

| 模块 | 职责 | 当前优先级 |
|---|---|---|
| M1 测试体系 | 目标达成判定、报告与改进建议生成 | P0 |
| M2 BPM 引擎 | 流程编排、实例治理、督办恢复 | P0 |
| M3 反身自开发 | 系统开发系统的流程与能力 | P1 |
| M4 生命周期管理 | 注册表、版本、健康度与上下架治理 | P1 |
| M5 自进化体系 | 监控驱动改进回路 | P2 |
| M6 施工平面 | 跨人类/Agent 的共享协作平面 | P0 |

建设顺序建议：

`M6 -> M2 -> M1 -> M3 -> M4 -> M5`

## 8. BPM 作为控制中枢

BPM 是 Control 层专职 Agent，不是业务 Agent。

必须职责：

1. 受理流程请求并做契约校验。
2. 按 Phase 调度 Actor 和 Skill。
3. 管理流程实例状态与父子引用。
4. 维护证据链与归档。
5. 处理超时、死锁、重试、升级和终止。
6. 在流程间传递文档化上下文摘要。

## 9. 元层自修改门禁（Gated Self-Modification）

当 meta-skill/meta-process 需要修改自身时，强制执行：

1. 变更提案（改什么、为何改、预期收益）。
2. 影响分析（下游依赖与兼容性）。
3. 版本快照（可回滚基线）。
4. 沙箱验证（隔离环境验证）。
5. 审批策略（高风险需人类审批断路器）。
6. 灰度发布（受控范围先行）。
7. 回滚预案（失败自动回退）。

任一环缺失，默认 Fail-Closed。

## 10. 资产治理与注册表

注册表是可发现性入口：

1. `/Users/albus/MyProjects/ANC_v2/shared/registry/agent_directory.json`
2. `/Users/albus/MyProjects/ANC_v2/shared/registry/skill_registry.json`
3. `/Users/albus/MyProjects/ANC_v2/shared/registry/process_registry.json`

治理规则：

1. 修改架构：更新 `system_overview.md`。
2. 修改流程规范：更新 `process_architecture.md`。
3. 修改资产：更新对应 registry。
4. 阶段进展：更新 `construction_plane.md`。
5. Active 资产变更必须记录 `CHANGELOG.md` 与 SemVer。
6. registry 字段与格式约束以 `registry_contracts.md` 为准。

### 10.1 OpenClaw 配置咬合（强制）

为保证架构与运行时一致，以下约束必须满足：

1. Gateway 配置验证开启：`gateway.config.validation.strict=true`。
2. 配置热更新模式使用 `manual` 或 `watch`，生产环境优先 `manual`。
3. 变更优先使用 `config.patch`（最小变更），避免无差别 `config.apply`。
4. `skills.entries` 必须显式声明 ANC 技能入口，禁止仅依赖隐式扫描。
5. 运行时执行和运维命令必须通过 OpenClaw CLI 统一入口。

详见：`/Users/albus/MyProjects/ANC_v2/docs/architecture/openclaw_interface.md`。

### 10.2 Skill/Process 规范咬合（强制）

1. 每个 Skill 目录必须包含 Agent Skills 兼容的 `SKILL.md`。
2. 每个 Process 目录必须包含：
   1. `SKILL.md`（供 OpenClaw 技能系统识别）
   2. `process.json` 或 `process.yaml`（供 BPM 结构化执行）
3. `SKILL.md` frontmatter 至少包含：`name`, `description`, `license`, `compatibility`。
4. registry 必须镜像 frontmatter 核心字段，确保文档与运行时一致。
5. 模板职责分离（避免目录语义歧义）：
   1. `/Users/albus/MyProjects/ANC_v2/skills/template`：只放 Skill 模板（`SKILL.md`）。
   2. `/Users/albus/MyProjects/ANC_v2/processes/template`：放 Process 模板包（`SKILL.md` + `process.json` + 可选 `PROCESS.md`）。
   3. `/Users/albus/MyProjects/ANC_v2/tests/template`：放测试模板（`TEST.md`）。
6. `template` 目录仅用于脚手架，不直接注册到 registry。

## 11. Phase 路线与里程碑

阶段路线：

1. Phase 0：手动自举（目录、SSOT、模板、registry 空壳）。
2. Phase 1：最小能力（BPM + llm-judge + spec/test 核心技能）。
3. Phase 2：自开发闭环可跑通。
4. Phase 3：产品化治理（版本、健康度、退役机制）。
5. Phase 4：自进化启动。
6. Phase 5：反身性成熟（元层可安全自改）。

关键里程碑：

1. M0 骨架就绪。
2. M1 第一次 LLM 评估可稳定执行。
3. M2 第一次 TDD 闭环跑通。
4. M3 BPM 调度 3+ Phase 流程。
5. M4 系统首次使用自身流程开发新 Skill 并上线。

实施提醒（来自本轮反思）：  
1. 不一次性生成所有文档，核心文档先行，允许保留 `[TODO]` 后续补齐。  
2. Skill 先于 Process：先让单个 Skill 可运行可测试，再扩展为流程编排。  
3. 测试能力优先级高于“快速产能”，先建立可判定机制再扩展开发规模。

## 12. 当前明确不做（Phase 0 边界）

1. 业务层 Agent 与复杂业务流程。
2. 自动触发机制与复杂调度优化。
3. 多层递归与大规模并发策略。
4. 过重权限细化与跨系统耦合集成。

## 13. 风险与对策

| 风险 | 描述 | 对策 |
|---|---|---|
| 无限自指递归 | 元层自改可能陷入循环 | 递归深度限制 + 门禁 + 审批断路器 |
| 测试偏差 | LLM Judge 存在主观偏差 | 双轨评估 + 多轮统计 + 抽检 |
| 流程爆炸 | 过早复杂编排造成维护失控 | 最小闭环优先，逐层扩展 |
| 文档漂移 | 文档与实现不一致 | SSOT 先行和变更回写硬规则 |
| 冷启动悖论 | 系统尚未成熟就要求自开发 | 手动自举，分阶段移交 |

## 14. 外部参考

1. OpenClaw 文档：https://docs.openclaw.ai/
2. OpenClaw Gateway Configuration：https://docs.openclaw.ai/gateway/configuration
3. OpenClaw CLI：https://docs.openclaw.ai/cli/index
4. OpenClaw AGENTS 模板：https://docs.openclaw.ai/reference/templates/AGENTS
5. Agent Skills 规范：https://agentskills.io/specification
6. SIPOC 概述：https://en.wikipedia.org/wiki/SIPOC
