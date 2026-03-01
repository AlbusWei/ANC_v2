# Engineering Standards Index

> 版本: v0.2.0 | 状态: active

本目录定义 ANC v2 的工程化标准，覆盖 Agent、Skill、Process 与递归流程设计方法。

## 文档清单

1. `docs/design/standards/agent-definition-standard.md`
2. `docs/design/standards/skill-definition-standard.md`
3. `docs/design/standards/process-definition-standard.md`
4. `docs/design/standards/process-decomposition-methodology.md`
5. `docs/design/standards/recursive-process-standard-p1-p6.md`
6. `docs/design/standards/reference-implementation-skill-creator.md`

## 使用顺序

1. 先读 Agent/Skill/Process 三份定义标准。
2. 再读 P1-P6 递归流程标准。
3. 最后读 `skill-creator` 参考实现，作为模板执行基线。

## 强制规则

1. 所有新增资产必须先满足本目录标准再进入 registry。
2. 标准变更属于元层修改，必须触发门禁流程。
3. 不满足标准的资产默认 Fail-Closed。
