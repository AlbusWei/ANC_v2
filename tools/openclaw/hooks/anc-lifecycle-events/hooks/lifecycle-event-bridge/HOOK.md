---
name: lifecycle-event-bridge
description: "Bridge OpenClaw platform events to ANC M5 trigger-event-runtime ingress"
homepage: https://docs.openclaw.ai/hooks
metadata:
  {
    "openclaw":
      {
        "emoji": "🧭",
        "events": ["command:new", "command:reset", "command:stop", "agent:bootstrap", "gateway:startup"],
      },
  }
---

# Lifecycle Event Bridge

## 目标

1. 把 OpenClaw 平台事件桥接为 ANC v2 标准事件 ingress 包。
2. 只做桥接与异步分发，不在 Hook 内执行重计算。
3. 任何异常仅本地记录，不外抛，避免影响其他 Hook。

## 运行输出

1. ingress: `runtime_data/evolution/hooks/ingress/`
2. dispatch 记录: `runtime_data/evolution/hooks/dispatch/`
3. 日志: `runtime_data/evolution/hooks/logs/lifecycle-event-bridge.jsonl`

## Fail-Closed

1. 找不到仓库根目录或 runner 时，写日志并跳过。
2. 触发事件映射失败时，写日志并跳过。
3. 子进程分发失败时，写日志并跳过，不阻断 OpenClaw 主流程。
