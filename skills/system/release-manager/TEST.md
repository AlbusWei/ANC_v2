# release-manager - Test Cases

## Objective Alignment

验证发布治理在门禁完整时可产出发布包，并在 registry 或回滚约束异常时 Fail-Closed。

## Test Cases

### TC-RELEASE-HP: 门禁完整发布通过

- Type: Objective
- Priority: P0
- Input: gate/lifecycle/registry 证据齐备且 rollback bundle 可用
- Expected: 输出 `release_package_ref/changelog_ref/release_decision=approved/rollback_bundle_ref`
- Evaluation Method: Exact Match

### TC-RELEASE-FC: registry 失败或 rollback 不可用

- Type: Objective
- Priority: P0
- Input: registry 校验失败，或 rollback bundle 不可达
- Expected: Fail-Closed，`release_decision=blocked|rejected`
- Evaluation Method: Exact Match
