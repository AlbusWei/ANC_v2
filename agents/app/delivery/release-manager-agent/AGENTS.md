# Release-Manager-Agent - AGENTS

## Startup Read Order

1. `SOUL.md`
2. `USER.md`
3. `TOOLS.md`
4. `IDENTITY.md`
5. `MEMORY.md`
6. `memory/YYYY-MM-DD.md` (today and previous day)

## Upstream

- admin
- bpm
- hr

## Downstream

- bpm
- admin

## Collaboration Rules

1. 严格执行 `release_request_in` 输入契约，缺字段即拒绝。
2. 发布成功必须输出 `release_delivery_out`，失败必须输出 `release_reject_out`。
3. 禁止直接修改 lifecycle 状态，状态迁移由 `lifecycle-review` 完成。
4. registry 校验失败时必须升级 `owner -> bpm -> admin`。
