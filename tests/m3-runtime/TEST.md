# M3 Runtime Skill Contract Validation

## Scope

本测试入口用于 Session3 运行资产最小契约验证，覆盖：

1. `sys.arch.impact-analyzer` happy path + fail-closed path
2. `sys.admin.release-manager` happy path + fail-closed path

## Entrypoint

- Runner: `tests/m3-runtime/run_skill_contract_validation.py`

## Cases

1. `TC-IMPACT-HP`
2. `TC-IMPACT-FC`
3. `TC-RELEASE-HP`
4. `TC-RELEASE-FC-REG`
5. `TC-RELEASE-FC-RB`

## Fail-Closed Policy

1. 任一用例失败即整体返回非零。
2. runner 缺失契约字段或证据路径不可达即判失败。
3. 报告必须写入 evidence 目录并可追溯。
