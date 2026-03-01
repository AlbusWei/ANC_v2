# software-vendor-e2e-flow - Test Plan

## 覆盖目标

1. 外部主线 Happy：`lead-intake -> ... -> support-and-feedback` 全链可执行。
2. 复用约束：`delivery-iterations` 必须复用 `full-development` canonical。
3. 旁路阻断：绕过 `delivery-iterations` 的尝试必须被 Fail-Closed。
4. 生命周期上限：结论不得超过 `review`。

## 最小用例

1. `TC-SVEF-001`：外部主线 Happy（含 `delivery-iterations` 复用）。
2. `TC-SVEF-002`：Fail-Closed -> Debug -> 修复 -> 重跑通过。
3. `TC-SVEF-003`：旁路阻断（跳过 `delivery-iterations`）。
4. `TC-SVEF-004`：生命周期越级阻断（`review -> active` 尝试）。

## Runner 执行

```bash
python3 tests/m3-self-development/session6_external_runner.py \
  --evidence-root tmp/runtime_data/execution/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/session6 \
  --report session6_report.json \
  --cases M3-EXT-001,M3-EXT-002,M3-EXT-003,M3-FC-101,M3-FC-102,M3-FC-103
```

## 返回码语义

1. `0`：全用例通过。
2. `2`：Fail-Closed（任一用例失败或前置不满足）。
3. `1`：运行异常。
