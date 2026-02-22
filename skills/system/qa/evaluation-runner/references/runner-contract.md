# quality_eval_runner Contract

命令格式：

```bash
quality_eval_runner run \
  --preparation-bundle <ref> \
  --mode <objective|subjective|regression> \
  --actual-output <ref> \
  --module <M3|M4|M5|...> \
  --output-dir <path>
```

返回码：

1. `0`: pass
2. `20`: test_invalid
3. `30`: hold
4. `40`: fail
5. `50`: runtime exception

运行时约束：

1. 入口脚本会优先通过 `uv + Python3.11` 运行 OpenJudge（`py-openjudge`）。
2. `objective/regression` 使用 datapoint 的 `evaluation_method` 调度 OpenJudge grader。
3. `subjective` 必须提供两组输出（或每个 TC 的 baseline/candidate 引用）。
4. `LLM-Judge` 需要 `--judge-model`（默认 `gpt-5.3-codex`）、`OPENAI_API_KEY`，并支持 `OPENAI_BASE_URL`。
5. `LLM-Judge` 可读取测试计划中的 `grader_selection/grader_weights/min_score_per_grader/must_pass_graders` 做动态 grader 编排。
6. 若提供 `auto_rubric_task_description`，runner 会调用 OpenJudge `SimpleRubricsGenerator` 自动生成 rubric grader。
7. `subjective` 在 `LLM-Judge` 场景使用 listwise 比较（A/B 盲测），记录每轮 blind assignment 与 judge 证据。
8. LLM 错误分类：
   - 临时错误（timeout/429/503）-> `hold`
   - 模型不支持/鉴权/无效请求 -> `test_invalid`
   - 其他运行时异常 -> `fail`
