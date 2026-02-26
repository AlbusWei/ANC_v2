# ANC v2 测试方法论

最后更新：2026-02-26  
版本：2.2.0-alpha

> 本文档定义 ANC 中测试的定位、执行方式、评估协议、门禁规则与证据规范。

## 1. 测试在因果链中的位置

`Objective -> Spec -> Test -> Development`

测试规则：

1. Test 是 Spec 的可验证镜像。
2. Test 必须覆盖 Objective 的核心意图，而不只验证格式。
3. Test 必须先于 Development 设计。

## 2. 核心原则

### 2.1 运行时验证优先

禁止以纯静态字符串匹配作为最终验收依据。

应执行：

1. 在真实运行环境执行被测对象。
2. 观察中间行为与最终输出。
3. 基于 Objective 判断“是否达成目标”。

### 2.2 测试不可跳过

1. BPM 不允许跳过测试阶段直接发布。
2. 任何“先上线后补测”默认视为治理违规。

### 2.3 门禁优先于报告格式

1. 首要目标是门禁真实生效并可阻断推进。
2. verdict 允许非严格 JSON，只要可稳定解析为统一输出契约。
3. 输出可读性和格式完整性服从于门禁可用性。

## 3. 双轨评估机制

### 3.1 客观评估（Objective Evaluation）

适用：新功能验收、回归验证。

输入建议：

```json
{
  "objective": "...",
  "spec_ref": "...",
  "expected_conditions": ["..."],
  "actual_output_ref": "..."
}
```

统一输出（M1 verdict）：

```json
{
  "gate_decision": "pass|fail|test_invalid",
  "runtime_gate_state": "pass|fail|hold|test_invalid",
  "evidence_ref": "path/to/evidence/package",
  "reasons": ["..."],
  "raw_eval_ref": "optional",
  "retry_hint": "optional",
  "profile_id": "optional",
  "parser_notes": "optional"
}
```

### 3.2 主观评估（Subjective Evaluation）

适用：版本迭代比较、质量优化。

执行规则：

1. A/B 输出盲测，隐藏来源并随机化 X/Y。
2. 轮次按任务复杂度由测试计划定义，`9` 轮仅作为推荐基线。
3. 必须记录随机种子，保证可复现。
4. 统计胜率后再做裁决。
5. 主观评测优先使用 OpenJudge listwise grader（或 rubric 生成的 listwise grader）进行盲测比较。

测试计划强制要素（由 QA 动态设计，不允许硬编码固定模板）：

1. `grader_selection`（按任务语义选择内置或自定义 grader）。
2. `grader_weights` 与 `min_score_per_grader`（明确每维门槛）。
3. `rounds/seed/retry_policy`（按复杂度动态配置，并保证可复现）。
4. 若内置 grader 不满足场景，使用 rubric 生成或自定义 grader 并落盘评审依据。

裁决建议：

1. 新版本胜率 `>= 2/3`：接受。
2. 新版本胜率 `< 1/2`：拒绝。
3. 中间区间：进入 `architect + admin` 审查。

## 4. LLM-as-Judge 协议

### 4.1 客观评估提示框架

1. 给出 Objective。
2. 给出 Spec 与验收条件。
3. 给出实际输出引用。
4. 要求返回可解析判定依据（由适配层归一为统一 verdict）。

### 4.2 主观评估提示框架

1. 给出同一任务目标。
2. 给出随机化后的输出 X/Y。
3. 要求选择优者并解释理由。
4. 输出中必须带可复现元数据（seed、轮次、样本标识）。

### 4.3 多视角评估（可选）

支持以不同视角评审同一输出：

1. 终端用户：可理解性与可操作性。
2. 技术评审：准确性与完整性。
3. 产品视角：目标对齐度。

## 5. 测试报告规范

测试报告必须包含可执行改进建议，不得只给 pass/fail。

建议结构：

1. 摘要：测试类型、总体结论。
2. 用例结果：每个 TC 的 gate_decision、reasons、evidence_ref。
3. 汇总分析：共性问题与风险。
4. 改进行动：可执行的下一步修复建议。
5. 发布建议：pass/fail/test_invalid。
6. `hold` 仅作为运行时治理状态（`runtime_gate_state`），不作为对外发布门禁结论枚举。

测试模板基线：

1. 统一模板路径：`tests/template/TEST.md`。
2. `TEST.md` 与 `SKILL.md` 分离存放，避免“能力定义模板”和“验收模板”耦合。
3. `TEST.md` 是唯一测试定义源，`1 TC -> 1 datapoint`。

## 6. 执行策略

### 6.1 并发策略

1. 无依赖测试可并发。
2. 多轮主观评估可并发。
3. 各并发任务使用隔离会话，避免上下文污染。

### 6.2 活性检测与 HOLD 治理（替代硬超时）

1. 评测任务应有轮询机制与运行活性检测。
2. 禁止以固定时长作为失败判据。
3. 最小进展信号：
   - 日志增量
   - 阶段状态推进
   - 输出流心跳
4. `hold` 由 `qa` 负责 triage，必要时升级 `bpm -> admin`；`hold` 不得直接作为对外放行结论。
5. triage 决策：`continue/retry/debug/fail`。
6. 默认无进展观察窗口不得低于 `900s`，并要求基于 `liveness_policy_ref` 记录终止判据。

### 6.3 分级测试

| 级别 | 触发 | 范围 | 深度 |
|---|---|---|---|
| 冒烟 | 日常迭代后 | P0 用例 | 单轮客观评估 |
| 标准 | 发布前 | 全量用例 | 客观评估 + 必要重试 |
| 深度 | 重大变更 | 全量 + A/B | 动态轮次 + 多视角 |

## 7. Fail-Closed 条件

以下情况默认失败：

1. 判定结果不可解析。
2. 关键输入缺失（Objective/Spec/Output）。
3. 证据缺失或不可追溯。
4. judge 模型/凭据/请求配置不可用（含 unsupported model）导致无法执行有效判定。

补充：

1. 编译期/运行前契约错误返回 `test_invalid` 并阻断。
2. `hold -> fail` 仅在确认异常或无进展证据时触发。
3. 长时运行本身不构成失败。
4. 若 `runtime_gate_state=hold`，对外 `gate_decision` 必须为 `fail`，直到补测链路重新产出 `pass`。
