# m1-real-service-semantic - Test Cases

## Objective Alignment

验证真实用户服务场景下，QA 能对 mock 交付执行语义评审并发现关键问题。

## Test Cases

### TC-001: 产品需求交付语义校验

- Type: Objective
- Priority: P0
- Input: mock 开发交付结果
- Expected: 能识别关键能力缺失并拒绝放行
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: 验证员工请假审批能力在提交、审批、审计、权限与限流均满足要求且具备关键/异常可执行证据时才可通过发布门禁。
  - expected_conditions: [员工可成功提交请假申请，且必填字段包含开始时间、结束时间、原因、附件；成功后返回唯一申请ID与待审批状态。, 直属主管可对本团队成员申请执行通过/拒绝，并且审批请求必须包含审批理由。, 系统对提交、审批、状态变化三类动作均生成审计日志，日志至少包含actor、action、target_id、timestamp、request_id。, 员工仅可查询本人申请；访问他人申请被拒绝（403/等效拒绝码）。, 主管仅可查询或审批本团队申请；跨团队访问/审批被拒绝（403/等效拒绝码）。, 接口级限流生效：超过阈值触发429（或等效限流码），并返回可重试信息（如Retry-After）。, 关键路径测试证据可执行且完整覆盖“提交->审批->状态变更->审计记录”。, 异常路径测试证据可执行且覆盖“越权访问”“无审批理由”“限流触发”至少三类异常。, 若权限、审计、限流、关键测试证据任一能力缺失或证据不可复现，门禁判定必须为FAIL并阻断发布。]
  - reference_response: 输出必须覆盖核心需求功能、异常处理策略与测试证据，否则视为未完成交付
  - grader_selection: [relevance, correctness]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
