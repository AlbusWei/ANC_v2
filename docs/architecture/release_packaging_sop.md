# ANC v2 发布打包 SOP（标准化执行）

最后更新：2026-02-24

## 1. 目标

将 ANC v2 的发布动作收敛为单一标准命令，确保每次打包都自动执行隔离门禁并输出可审计工件，避免人工遗漏导致私有数据或运行噪声进入发布包。

## 2. 适用范围

1. 对外发布前的标准打包。
2. 发布候选版本（Release Candidate）构建与复核。
3. 需要复现“同一提交、同一规则”打包结果的审计场景。

## 3. 前置条件（Fail-Closed）

1. 当前目录位于仓库根或其子目录。
2. 默认要求工作区干净（`git status --short` 为空）；若需例外必须显式加 `--allow-dirty`。
3. 已完成发布隔离策略要求的联动更新（见 `docs/architecture/release_isolation_policy.md`）。
4. 需要发布前 OpenClaw 口径校验时，必须附加 `--verify-openclaw`。

## 4. 标准命令

```bash
python3 tools/release/build_release_bundle.py --verify-openclaw
```

脚本执行链路固定为：

1. 执行 `tools/release/release_isolation_gate.py`（可选附加 OpenClaw 校验）。
2. 执行 `tools/release/generate_release_whitelist.py --strict` 并冻结白名单。
3. 按白名单生成发布归档包（`tar.gz`）。
4. 生成 SHA256 校验文件与 `bundle_manifest.json`。

## 5. 输出工件

默认输出目录：`runtime_data/exports/release-bundles/<bundle-id>/`

每次打包至少包含：

1. `<bundle-id>.tar.gz`：发布归档包。
2. `<bundle-id>.tar.gz.sha256`：归档包校验和。
3. `bundle_manifest.json`：打包上下文、输入命令、门禁结果、白名单摘要。
4. `whitelist/release_whitelist.{json,txt}`：本次打包冻结白名单。

## 6. 结果判定

1. 命令返回码为 `0` 且输出 `ok=true` 才可视为打包成功。
2. 任一步失败均视为打包失败，不得继续发布。
3. 若失败，先修复门禁问题，再重新执行完整命令，不允许跳步手工补包。

## 7. 常用选项

```bash
# 指定输出根目录
python3 tools/release/build_release_bundle.py \
  --verify-openclaw \
  --output-dir runtime_data/exports/release-bundles

# 指定归档名前缀
python3 tools/release/build_release_bundle.py \
  --verify-openclaw \
  --bundle-prefix anc-v2-rc
```

`--allow-dirty` 仅用于调试，不可用于正式发布。
