# trigger-matcher-dedupe - Test Cases

## Objective Alignment

验证触发匹配和幂等去重策略在主键与回退键场景下均能稳定决策。

## Test Cases

### TC-001: 命中规则且允许调度

- Type: Objective
- Priority: P0
- Input: 首次事件，规则命中，`source+event_id` 唯一
- Expected: `match_result=hit` 且 `dedupe_decision=allow`
- Evaluation Method: Exact Match

### TC-002: 重复事件被去重拒绝

- Type: Objective
- Priority: P0
- Input: 同 `source+event_id` 二次投递
- Expected: `dedupe_decision=reject` 且生成 `dedupe_key_ref`
- Evaluation Method: Exact Match

### TC-003: 无 event_id 时按回退键去重

- Type: Objective
- Priority: P0
- Input: 缺 `event_id` 但具备回退键字段
- Expected: 仍可给出明确 `allow/reject` 决策
- Evaluation Method: Exact Match
