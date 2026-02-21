# 元流程清单与设计

> 版本: v0.2.0 | 分类: Meta Processes

## 已有元流程

### development-process

- process_id: development-process
- canonical_path: `processes/meta/development-process/`
- level: P4
- phases: write-spec -> design-tests -> implement -> verify
- loop: p4 fail 回到 p3，max 2

## 规划元流程

1. full-development
2. hotfix
3. refactor

## 递归组合规则

1. 元流程可组合 P5/P6 子流程。
2. 同层级组合允许，但必须声明终止条件。
3. 组合关系必须落盘到 `composed_processes[]`。
