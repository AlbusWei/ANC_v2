# Tests Directory

## Layout

1. `tests/template/TEST.md`：测试模板。
2. `tests/skill-creator/TEST.md`：`skill-creator` 测试用例。
3. `tests/development-process/TEST.md`：`development-process` 测试用例。
4. `tests/qa-skills/TEST.md`：`sys.qa.*` 技能补测用例（Round 5）。
5. `tests/qa-skills/run_round5_validation.py`：QA 技能可执行补测脚本。
<<<<<<< HEAD
6. `tests/git-worktree-sync/TEST.md`：`system.ops.git-worktree-sync` 运行级测试用例（Round 1）。
7. `tests/git-worktree-sync/run_runtime_validation.py`：git-worktree-sync 运行级验证脚本。
8. `tests/m6-governance/TEST.md`：M6 开发成果补测计划（Round 6）。
9. `tests/m6-governance/run_post_dev_regression.py`：M6 可执行补测脚本。

## Rule

- 测试与 skill/process 分离存放。
- 非模板测试应在 registry 的 `tests` 字段有可追溯路径。
