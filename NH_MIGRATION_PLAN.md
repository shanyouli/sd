# `sd` 的 `nh` 迁移计划书

## 背景

`sd` 当前在 [src/sd/api/nix.py](/Users/lyeli/Code/Git/sd/src/sd/api/nix.py) 中封装了
`nix`、`darwin-rebuild`、`home-manager` 以及部分项目自定义逻辑。

本次调整的目标，不是先新增一个对外的 `sd nh ...` 命令，而是在保持现有 `sd` CLI
接口稳定的前提下，在系统存在 `nh` 且 `nh` 能安全覆盖当前行为时，优先使用 `nh`
作为后端。

当前本机核对结果：

- 系统已安装 `nh`
- 本机 `nh` 版本为 `4.2.0`
- `nh` 顶层命令包含：
  - `nh os`
  - `nh home`
  - `nh darwin`
  - `nh clean`
- `nh darwin` 当前支持：
  - `build`
  - `switch`
  - `repl`
- `nh home` 当前支持：
  - `build`
  - `switch`
  - `repl`

这说明 `nh` 很适合替换 `sd.api.nix` 中一部分“命令执行后端”逻辑，但不能直接覆盖整个
模块。

## 目标

将 `src/sd/api/nix.py` 重构为一个包，并在 `nh` 明确支持的命令路径上优先使用 `nh`
后端，同时保留当前 `sd` CLI 的对外接口和 `nh` 不存在时的完整回退行为。

## 非目标

- 第一阶段不新增新的公开命令 `sd nh ...`
- 第一阶段不尝试用 `nh` 替换 `nix.py` 中所有函数
- 第一阶段不强行把 `gc`、`bootstrap`、`update`、`cache`、`pull`、`init` 接到 `nh`
- 不把 `nh` 后端接入与无关的大范围重构混在一起

## 计划中的目录结构

将当前单文件模块：

```text
src/sd/api/nix.py
```

重构为：

```text
src/sd/api/nix/
├── __init__.py
├── common.py
├── nix.py
└── nh.py
```

### `__init__.py`

职责：

- 保持 `from sd.api import nix` 的兼容性
- 持有 `app = typer.Typer(...)`
- 持有 completion 相关命令
- 暴露并注册对外 CLI 命令
- 在支持的命令路径上做后端分发：
  - 系统存在 `nh` 时优先走 `nh.py`
  - 否则回退到原生后端 `nix.py`

### `common.py`

职责：

- 放置 `nh` 在第一阶段无法替代的功能
- 放置 `nh.py` 和 `nix.py` 共用的辅助逻辑

建议放入的内容：

- `get_flake`
- `get_flake_inputs_by_lock`
- `get_flake_inputs_by_nix`
- `get_flake_platform`
- `get_default_host`
- `change_workdir`
- `select`
- `Generation`
- `get_generations`
- `get_current_generation`
- `format_generation`
- `nix_diff`
- `Gc`
- `shell_backup`
- `nix_install_profiles`

第一阶段建议继续保留在 `common.py` 或由 `__init__.py` 直接调用的命令：

- `update`
- `bootstrap`
- `diff`
- `clean`
- `pull`
- `cache`
- `gc`
- `init`

原因是这些逻辑要么明显超出 `nh` 当前能力边界，要么带有项目自身的语义，不适合第一批
迁移。

### `nix.py`

职责：

- 存放“可以被 `nh` 替代”的原生后端实现
- 第一阶段只保留那些会被 `nh` 替换的命令执行逻辑

建议内容：

- `build_with_nix(...)`
- `switch_with_nix(...)`
- `repl_with_nix(...)`
- 以上三个命令对应的原生命令拼装辅助函数

### `nh.py`

职责：

- 检测系统是否存在 `nh`
- 为支持的流程构造并执行 `nh` 命令
- 将 `sd` 的参数语义翻译为 `nh` 的参数语义

建议内容：

- `has_nh() -> bool`
- `get_nh_namespace(cfg: FlakeOutputs) -> str`
- `build_with_nh(...)`
- `switch_with_nh(...)`
- `repl_with_nh(...)`
- `sd` 参数到 `nh` 参数的映射辅助函数

## 第一阶段的命令归属

### 改成“后端分发”的命令

以下命令对外接口保留在 `__init__.py`，但内部改为按后端分发：

- `build`
- `switch`
- `repl`

推荐分发规则：

1. 先通过现有 `select(...)` 解析目标配置类型
2. 如果系统存在 `nh`，且当前配置类型能映射到 `nh` 支持的 namespace，则走 `nh.py`
3. 否则完整回退到 `nix.py`

### 第一阶段保持不动的命令

这些命令第一阶段继续保留当前实现，不接入 `nh`：

- `update`
- `bootstrap`
- `diff`
- `clean`
- `pull`
- `cache`
- `gc`
- `init`

原因如下：

- `update`：当前依赖项目自定义的 flake lock 更新行为
- `bootstrap`：darwin / home-manager 初始化流程带有项目定制步骤
- `clean`：当前语义是清理本地 `result` 等符号链接，不等同于 `nh clean`
- `gc`：当前除了垃圾回收外，还带有项目自定义 profile/gcroot 清理逻辑
- `init`：依赖自定义的 nix profile 修复与 bootstrap 流程

## 分阶段实施计划

### Phase 0：冻结基线并准备评审材料

任务：

- 在功能实施前打出当前基线 tag
- 将项目版本号提升到下一补丁版本
- 将本计划书写入仓库供评审

完成标准：

- 仓库中存在可审阅的计划书
- 基线 tag 已创建
- 版本元数据已同步更新

### Phase 1：将 `nix.py` 从单文件重构为包

任务：

- 创建 `src/sd/api/nix/`
- 先将当前 `src/sd/api/nix.py` 迁入包结构，但不改变行为
- 确保 `from sd.api import nix` 仍然可用
- 在引入 `nh` 前先保证结构调整本身测试通过

实施建议：

- 初始阶段可以先把大部分内容原样放进 `__init__.py`
- 等结构稳定后再继续拆分到 `common.py` / `nix.py` / `nh.py`

完成标准：

- CLI 对外行为无变化
- 导入路径兼容
- 现有测试保持通过

### Phase 2：抽出 `common.py`

任务：

- 将共享状态、共享工具函数、非 `nh` 命令逻辑迁入 `common.py`
- `__init__.py` 仅保留 CLI 入口与调度职责

完成标准：

- 共享逻辑集中
- `__init__.py` 变薄，职责更清晰

### Phase 3：抽出原生后端 `nix.py`

任务：

- 将当前 `build`、`switch`、`repl` 的原生实现迁入 `nix.py`
- CLI 命令注册仍保留在 `__init__.py`

完成标准：

- 原生后端逻辑可独立调用
- 在 `nh` 不存在时行为与当前保持一致

### Phase 4：新增 `nh.py`

任务：

- 增加 `has_nh()`
- 增加平台映射：
  - `FlakeOutputs.NIXOS -> "os"`
  - `FlakeOutputs.DARWIN -> "darwin"`
  - `FlakeOutputs.HOME_MANAGER -> "home"`
- 增加：
  - `build_with_nh(...)`
  - `switch_with_nh(...)`
  - `repl_with_nh(...)`

重点核对项：

- flake 路径与 host 目标的传递方式
- `--dry-run` 是否可忠实表达
- `debug` / `--show-trace` 是否可映射
- `extra_args` 是否可以安全透传
- `nh` 自身提权逻辑与当前 `sudo` 行为是否冲突
- 接入后 `nix_diff` 的触发条件是否需要调整

完成标准：

- `nh` 后端函数存在
- 参数映射明确
- 可以独立测试

### Phase 5：在 `__init__.py` 中引入后端分发

任务：

- 让 `build`、`switch`、`repl` 在 `nh` 存在时优先走 `nh`
- `nh` 不存在时回退到原生后端
- 对用户保持稳定接口

建议行为：

- 可以增加一条简洁日志，说明当前使用了 `nh` 后端
- 对无法由 `nh` 完整表达的参数组合，不要静默降级
- 推荐策略：
  - 能安全回退时，回退到原生后端
  - 无法安全回退时，显式报错

完成标准：

- `sd build` / `sd switch` / `sd repl` 在支持条件下优先使用 `nh`
- 回退路径稳定可靠

### Phase 6：补充测试

必须覆盖：

- `nh` 存在时 `build` 走 `nh`
- `nh` 不存在时 `build` 走原生后端
- `nh` 存在时 `switch` 走 `nh`
- `nh` 不存在时 `switch` 走原生后端
- `nh` 存在时 `repl` 走 `nh`
- `nh` 不存在时 `repl` 走原生后端
- host / flake / 配置类型的参数映射
- `nh` 无法处理参数时的回退或报错行为

建议增加：

- `nix_diff` 在 `build` / `switch` 后仍按原条件触发
- `bootstrap` 相关流程不受影响
- `update --all` 与当前 flake 更新行为保持不变

完成标准：

- 后端选择与回退行为都有测试覆盖

### Phase 7：单独评估 `gc` 与 `nh clean`

这一阶段应当在前面稳定后独立评估，不建议和 Phase 1~6 混做。

需要先回答的问题：

- `nh clean` 是否真的能覆盖当前 `Gc` 的任一子集？
- `sd clean` 是否仍应坚持“清理本地 result 链接”的当前语义？
- `sd gc` 应该维持项目定制逻辑，还是引入混合模式？

当前建议：

- 第一阶段完全不要把 `nh clean` 接入 `sd gc`

## 参数兼容性检查清单

在每个命令接入 `nh` 前，至少确认：

- host 目标语法与 `sd` 当前预期一致
- flake 解析仍然遵循 `remote` 与 `get_flake()`
- `dry_run` 的语义不失真
- `debug` 行为要么保留，要么明确说明退化
- `extra_args` 要么安全透传，要么显式拒绝
- 提权行为不会出现重复 `sudo`

## 风险

### 风险 1：后端语义漂移

`nh` 可能带有比当前手写命令更强的默认行为。

缓解方式：

- 保留原生回退
- 第一阶段只接少量命令
- 为参数映射和后端选择补足测试

### 风险 2：参数不完全兼容

当前 `sd` 参数不一定能与 `nh` 一一对应。

缓解方式：

- 在实现前先产出兼容性对照表
- 优先选择“显式回退”，而不是“静默部分支持”

### 风险 3：结构重构与行为改动相互污染

如果目录重构与后端切换同时大改，回归来源会不清晰。

缓解方式：

- 先完成包结构重构
- 再接 `nh`
- 每一阶段单独可测试、可评审

### 风险 4：清理类命令语义混淆

`sd clean` / `sd gc` 与 `nh clean` 并不是同一语义。

缓解方式：

- 清理逻辑不进入第一阶段范围

## 推荐实施顺序

1. 建立 `src/sd/api/nix/` 包结构
2. 将当前单文件逻辑迁入包中，确保无行为变化
3. 抽出 `common.py`
4. 抽出原生后端 `nix.py`
5. 新增 `nh.py`
6. 让 `build` / `switch` / `repl` 走后端分发
7. 补齐测试
8. 之后再独立评估 `gc` / `clean`

## 评审前需要确认的问题

在正式开始实现前，建议你先确认以下决策：

1. 第一阶段是否只覆盖 `build`、`switch`、`repl`
2. 当 `sd` 选择了 `nh` 后端时，是否需要对用户显示提示
3. 当参数组合无法被 `nh` 安全表达时，应优先：
   - 回退到原生后端
   - 还是直接报错
4. `gc` / `clean` 是否明确排除在第一阶段范围外
5. 包结构重构与 `nh` 接入是否拆成两个 PR：
   - PR 1：`nix.py` -> `nix/` 包
   - PR 2：`nh` 后端接入

## 当前推荐结论

推荐的第一阶段实施范围是：

- 将 `src/sd/api/nix.py` 重构为 `src/sd/api/nix/`
- 引入 `common.py`、`nix.py`、`nh.py`
- 只让以下命令优先使用 `nh`：
  - `build`
  - `switch`
  - `repl`
- 其他命令全部保持现状

这是当前最小、最稳、同时又能满足“系统存在 `nh` 时优先使用它”的方案。
