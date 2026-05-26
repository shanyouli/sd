# `nh` 接入待办项

本清单依据 `NH_MIGRATION_PLAN.md` 执行，用于跟踪本次实现，不修改既有计划书。

## 当前批次

- [x] 确认 `nh` 本机可用，并核对 `os` / `darwin` / `home` 的 `build`、`switch`、`repl` 子命令。
- [x] 将 `src/sd/api/nix.py` 改为 `src/sd/api/nix/` 包。
- [x] 抽取 `common.py`，保存 `nh` 无法取代或多后端共用的逻辑。
- [x] 抽取原生后端 `nix.py`，保存可被 `nh` 替代的原生命令实现。
- [x] 新增 `nh.py`，保存 `nh` 可用性检测、namespace 映射和命令构造。
- [x] 在 `__init__.py` 中让 `build`、`switch`、`repl` 按后端分发。
- [x] 补充 `nh` 存在与不存在时的分发测试。
- [x] 运行系统优先的 lint / type / test 检查。

## 明确排除

- 暂不接入 `gc` / `clean` 到 `nh clean`。
- 暂不新增公开命令 `sd nh ...`。
- 暂不修改 `NH_MIGRATION_PLAN.md`。
