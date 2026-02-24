# ANC v2 发布隔离策略（数据与资产）

最后更新：2026-02-24

## 1. 目标与问题

ANC v2 将作为公开项目发布，必须保证仓库默认仅包含“可公开、可复现、可审计”的通用资产。  
为测试/验证构造的数据、个人私有信息、运行时噪声输出，必须与标准资产和公共样例分离。

本策略解决三个风险：

1. 运行产物默认落盘到仓库导致误提交。
2. 测试/验证资产与标准发布资产混放，发布边界不清。
3. Agent 在执行流程时写入个人/私有上下文到可版本化路径。

## 2. 三层空间模型

1. 标准发布空间（可入库）
   - `agents/`、`skills/`、`processes/`、`shared/registry/`、`docs/`
   - 仅承载通用能力、协议、规范化案例模板。
2. 公共案例空间（可入库，白名单）
   - `docs/design/modules/evidence/` 当前仅保留目录说明；公开案例需按白名单逐条回填。
   - 不作为默认运行写入路径。
3. 私有运行空间（默认不入库）
   - `runtime_data/`（见 `runtime_data/README.md`）
   - 承接运行证据、业务数据、Agent 工作记忆、私有/实验资产。

## 3. 数据隔离规则（强制）

1. 所有流程 runner 的默认 evidence 输出目录必须位于 `runtime_data/execution/evidence/`。
2. 所有 Agent 的临时记忆/工作日志默认写入 `runtime_data/agent-memory/<agent-id>/`。
3. 任何真实业务数据、私有上下文、凭据、客户标识，禁止进入版本控制目录。
4. 如需发布案例，必须执行“脱敏 + 结构审查 + 人工确认”，再复制到 `docs/design/modules/evidence/`。

## 4. 资产隔离规则（强制）

1. 标准版 Agent/Skill/Process 资产仅放在 `agents/`、`skills/`、`processes/` 并纳入 registry。
2. 测试/验证/私有资产默认放在 `runtime_data/private-assets/{agents,skills,processes}/`。
3. `runtime_data/private-assets/` 下资产禁止写入：
   - `shared/registry/skill_registry.json`
   - `shared/registry/process_registry.json`
   - `shared/registry/agent_directory.json`
   - `config/openclaw.phase05*.fragment.json`
4. 只有经过评审并确认可公开复用的资产，才允许迁移到标准目录并进入 registry 生命周期。

## 5. 发布前最小校验

1. `git status --short` 不得出现 `runtime_data/` 产物。
2. `python3 shared/registry/registry_contract_tool.py verify` 必须通过。
3. `rg -n "runtime_data/private-assets" shared/registry config/openclaw.phase05*.fragment.json` 应为空结果。
4. 抽样检查流程默认值：`rg -n "runtime_data/execution/evidence" processes -g "*.py"`。
5. 发布白名单（严格）：`python3 tools/release/generate_release_whitelist.py --strict`。
6. 统一门禁：`python3 tools/release/release_isolation_gate.py`。
7. 发布前附加 OpenClaw 校验：`python3 tools/release/release_isolation_gate.py --verify-openclaw`。

## 5.1 OpenClaw 切换口径

1. 公开发布模式：`python3 tools/openclaw/switch_workspace.py --repo-root <repo> --scope public`
2. 开发模式：`python3 tools/openclaw/switch_workspace.py --repo-root <repo> --scope dev`
3. 开发模式加载私有资产：增加 `--enable-private-assets --private-overlay runtime_data/private-assets/openclaw.overlay.json`

## 6. 与其他协议关系

1. 本文补充 `AGENTS.md` 的协作与发布边界，不替代 SSOT。
2. 如与流程契约冲突，按 `Objective > Spec > Test > Implementation` 决策并回写文档。
3. 任何隔离策略变更，必须同步 `AGENTS.md` 与受影响 agent 协作规则。
