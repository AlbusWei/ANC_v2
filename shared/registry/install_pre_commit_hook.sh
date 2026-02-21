#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_PATH="$(git rev-parse --git-path hooks)/pre-commit"

cat > "$HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
python3 "$REPO_ROOT/shared/registry/registry_contract_tool.py" verify
HOOK

chmod +x "$HOOK_PATH"
echo "Installed pre-commit hook: $HOOK_PATH"
