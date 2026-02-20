# ANC v2 测试方法论

最后更新：2026-02-20
版本：2.0.2-alpha

> 本文档定义 ANC 中测试的定位、执行方式、评估协议和报告规范。
> 测试在 ANC v2 中属于治理与门禁能力，不是产品主定位。

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

## 3. 双轨评估机制

### 3.1 客观评估（Objective Evaluation）

适用：新功能验收、回归验证。

输入建议：

```json
{
  "objective": "...",
  "spec": "...",
  "expected_conditions": ["..."],
  "actual_output": "..."
}
```

输出建议：

```json
{
  "pass": true,
  "confidence": 0.84,
  "remarks": "...",
  "suggestions": ["..."]
}
```

### 3.2 主观评估（Subjective Evaluation）

适用：版本迭代比较、质量优化。

执行规则：

1. A/B 输出盲测，隐藏来源。
2. 多轮评估（建议 N >= 9）。
3. 统计胜率后再做裁决。

裁决建议：

1. 新版本胜率 >= 2/3：接受。
2. 新版本胜率 < 1/2：拒绝。
3. 中间区间：人类介入。

## 4. LLM-as-Judge 协议

### 4.1 客观评估提示框架

1. 给出 Objective。
2. 给出 Spec 与验收条件。
3. 给出实际输出。
4. 要求返回 pass/confidence/reason/suggestions。

### 4.2 主观评估提示框架

1. 给出同一任务目标。
2. 给出随机化后的输出 X/Y。
3. 要求选择优者并解释理由。

### 4.3 多视角评估（可选）

支持以不同视角评审同一输出：

1. 终端用户：可理解性与可操作性。
2. 技术评审：准确性与完整性。
3. 产品视角：目标对齐度。

### 4.4 Scenario 执行协议（Phase 1 默认）

ANC 将 Scenario 作为测试执行底座，默认后端为 `scenario_python`。

输入建议（v0.2）：

```json
{
  "objective": "...",
  "spec_ref": "/abs/path/spec.md",
  "expected_conditions": ["..."],
  "actual_output_ref": "/abs/path/output.md",
  "test_case_ref": "/abs/path/TEST.md",
  "evaluation_mode": "objective",
  "backend": "scenario_python",
  "timeout_seconds": 600,
  "evidence_root": "/abs/path/process_instances/<id>/evidence/p4"
}
```

约束：

1. Scenario 原始结果不得直接作为 BPM 门禁输入。
2. 必须先经 `llm-judge` 归一化为 ANC 标准 verdict 后再流转。
3. 外部事件上报失败不影响门禁判定，门禁证据以本地落盘为准。

### 4.5 归一化规则（Scenario -> ANC Verdict）

固定映射：

1. `pass = success && unmet_criteria.length == 0`
2. `remarks = reasoning`
3. `suggestions = unmet_criteria -> actionable fixes`
4. `confidence = ANC confidence calculator`（非 Scenario 原生字段）
5. `evidence_refs = [transcript, raw_result, normalized_verdict, guard_log]`（绝对路径）

## 5. 测试报告规范

测试报告必须包含可执行改进建议，不得只给 pass/fail。

建议结构：

1. 摘要：测试类型、总体结论。
2. 用例结果：每个 TC 的 verdict、confidence、reason。
3. 汇总分析：共性问题与风险。
4. 改进行动：可执行的下一步修复建议。
5. 发布建议：accept/rework/human-review。

测试模板基线：

1. 统一模板路径：`/Users/albus/MyProjects/ANC_v2/tests/template/TEST.md`。
2. `TEST.md` 与 `SKILL.md` 分离存放，避免“能力定义模板”和“验收模板”耦合。

## 6. 执行策略

### 6.1 并发策略

1. 无依赖测试可并发。
2. 多轮主观评估可并发。
3. 各并发任务使用隔离会话，避免上下文污染。

### 6.2 轮询与超时

1. 评测任务应有轮询机制。
2. 超时任务标记 `TIMEOUT` 并进入失败分析。
3. 不允许静默丢弃超时结果。

### 6.3 分级测试

| 级别 | 触发 | 范围 | 深度 |
|---|---|---|---|
| 冒烟 | 日常迭代后 | P0 用例 | 单轮客观评估 |
| 标准 | 发布前 | 全量用例 | 多轮客观评估 |
| 深度 | 重大变更 | 全量 + A/B | 多轮 + 多视角 |

### 6.4 主观 A/B 多轮编排（Scenario 模式）

`subjective_ab` 模式执行规则：

1. 同任务输出 A/B 必须随机映射为 X/Y 并隐藏来源。
2. 默认执行 `N=9` 轮，允许并发但必须会话隔离。
3. 统计胜率后按阈值裁决：
   1. 新版本胜率 `>= 2/3`：接受
   2. 新版本胜率 `< 1/2`：拒绝
   3. 中间区间：`human-review`
4. 任一轮触发 Fail-Closed，则整组裁决直接 Fail-Closed。

## 7. Fail-Closed 条件

以下情况默认测试失败：

1. 判定结果不可解析。
2. 关键输入缺失（Objective/Spec/Output）。
3. 证据缺失或不可追溯。
4. 评估超时且无替代证据。
5. Scenario 返回结构不可解析或归一化失败。
6. `evidence_root` 缺失关键证据文件（`raw_result`/`normalized_verdict`/`guard_log`）。
