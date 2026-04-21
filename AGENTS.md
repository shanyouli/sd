# AGENTS.md - Agent Coding Guidelines for sd

## English / 中文

This is the `sd` CLI tool - a macOS/Nix darwin configuration management tool built with Python/Typer.
这是 `sd` CLI 工具 - 一个基于 Python/Typer 构建的 macOS/Nix darwin 配置管理工具。

---

## 1. Build/Lint/Test Commands / 构建/测试/代码检查命令

### Running Tests / 运行测试

```bash
# Run all tests / 运行所有测试
uv run pytest tests/ -v

# Run a single test file / 运行单个测试文件
uv run pytest tests/test_nix.py -v

# Run a single test / 运行单个测试
uv run pytest tests/test_nix.py::TestFlakePlatform::test_get_flake_platform_darwin -v

# Run tests with coverage / 运行带覆盖率的测试
uv run pytest tests/ --cov=src/sd
```

### Linting & Type Checking / 代码检查和类型检查

```bash
# Install dependencies first / 首先安装依赖
uv sync --all-extras

# Run ruff linter / 运行 ruff linter
uv run ruff check .

# Run ruff type checker / 运行 ruff 类型检查
uv run ruff check --select TYPE .
```

### Running the CLI / 运行 CLI

```bash
# Run CLI directly / 直接运行 CLI
python -m sd --help

# Or use the installed command / 或使用已安装的命令
sd --help
```

---

## 2. Code Style Guidelines / 代码风格指南

### Imports / 导入

- Standard library imports first, then third-party, then local / 标准库导入优先，然后是第三方库，最后是本地库
- Group imports: stdlib, third-party, local (separated by blank lines) / 分组导入：标准库、第三方库、本地库（用空行分隔）
- Use explicit relative imports from `sd` package: / 使用 `sd` 包的显式相对导入：

```python
# Correct / 正确
from sd.utils import cmd, fmt, path
from sd.utils.enums import ISMAC, REMOTE_FLAKE

# Avoid / 避免
from ..utils import cmd
```

### Formatting / 格式化

- Maximum line length: 100 characters (soft) / 最大行长度：100 字符（软限制）
- Use 4 spaces for indentation (not tabs) / 使用 4 空格缩进（不是制表符）
- Use blank lines to separate logical sections within functions / 用空行分隔函数内的逻辑部分
- Use type hints for function parameters and return types / 为函数参数和返回值使用类型提示
- No trailing whitespace / 不留尾部空白

### Naming Conventions / 命名约定

- **Variables/Functions**: `snake_case` (e.g., `get_flake`, `is_exist`) / **变量/函数**：`snake_case`（如 `get_flake`）
- **Classes**: `PascalCase` (e.g., `Generation`, `Gc`) / **类**：`PascalCase`（如 `Generation`）
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `ISMAC`, `SYSTEM_OS`) / **常量**：`UPPER_SNAKE_CASE`（如 `ISMAC`）
- **Private functions**: prefix with underscore (e.g., `_parse_value`) / **私有函数**：以下划线开头（如 `_parse_value`）
- **Files**: `snake_case.py` / **文件**：`snake_case.py`

### Type Hints / 类型提示

- Use Python 3.11+ type hints (e.g., `list[str]` instead of `List[str]`) / 使用 Python 3.11+ 类型提示（如用 `list[str]` 代替 `List[str]`）
- Use `| None` instead of `Optional[]` for simple cases / 简单情况下使用 `| None` 代替 `Optional[]`
- Use `Path` from `pathlib` for file paths / 使用 `pathlib` 的 `Path` 处理文件路径
- Use `Union` only when necessary / 仅在必要时使用 `Union`

```python
# Good examples / 好的示例
def get_flake(current_dir: bool = False) -> str:
    ...

def get_app_list_by_path(p: PathLink) -> dict[str, str]:
    ...

def get_re_compile(use_home: bool):
    return re.compile(...)  # Return type can be omitted for simple cases
```

### Error Handling / 错误处理

- Use `typer.Abort()` for CLI command failures / CLI 命令失败时使用 `typer.Abort()`
- Use `typer.secho()` with colors for user messages / 使用带颜色的 `typer.secho()` 显示用户消息
- Use `cmd.getout()` which raises `SubprocessError` on failure / 使用 `cmd.getout()` 在失败时抛出 `SubprocessError`
- Avoid bare `except:` - catch specific exceptions / 避免裸 `except:` - 捕获具体异常

```python
# Raising errors in CLI commands / 在 CLI 命令中抛出错误
if not host:
    fmt.error("Error: host configuration not specified.")
    raise typer.Abort()

# Handling subprocess errors / 处理子进程错误
try:
    result = cmd.getout(["git", "rev-parse", "--show-toplevel"])
except subprocess.SubprocessError:
    fmt.warn("The current directory is not a git project!")
```

### CLI Commands (Typer) / CLI 命令 (Typer)

- Use `@app.command()` decorator for commands / 使用 `@app.command()` 装饰器定义命令
- Use `typer.Option()` for optional arguments / 使用 `typer.Option()` 定义可选参数
- Use `typer.Argument()` for required arguments / 使用 `typer.Argument()` 定义必需参数
- Use `help` parameter for documentation / 使用 `help` 参数提供文档
- Set `hidden=True` for platform-specific commands / 为平台特定命令设置 `hidden=True`

```python
@app.command(help="Builds an initial Configuration")
@change_workdir
def bootstrap(
    host: str = typer.Argument(DEFAULT_HOST, help="The hostname"),
    nixos: bool = False,
    darwin: bool = False,
    home: bool = False,
    remote: bool = typer.Option(default=False, help="Fetch from remote"),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    ...
```

### Project Structure / 项目结构

```
src/sd/
├── __main__.py      # CLI entry point / CLI 入口点
├── api/             # Command modules (nix.py, macbid.py, macos.py, etc.) / 命令模块
├── utils/           # Utility modules (cmd.py, fmt.py, path.py, enums.py) / 工具模块
```

### Testing Guidelines / 测试指南

- Place tests in `tests/` directory / 将测试放在 `tests/` 目录
- Use `pytest` with `unittest.mock` for mocking / 使用 `pytest` 和 `unittest.mock` 进行模拟
- Test file naming: `test_<module_name>.py` / 测试文件命名：`test_<模块名>.py`
- Use `tmp_path` fixture for file operations / 使用 `tmp_path` fixture 进行文件操作

```python
# Example test / 示例测试
class TestFlakePlatform:
    @patch("sd.api.nix.cmd")
    def test_get_flake_platform_darwin(self, mock_cmd):
        from sd.api.nix import get_flake_platform, FlakeOutputs
        
        mock_cmd.exists.side_effect = lambda x: x == "darwin-rebuild"
        result = get_flake_platform()
        assert result == FlakeOutputs.DARWIN
```

### Constants and Configuration / 常量和配置

- Use `enums.py` for constants and enum-like classes / 使用 `enums.py` 定义常量和枚举类
- Use `Dotfiles` class for detecting configuration directories / 使用 `Dotfiles` 类检测配置目录
- Environment variables accessed via `os.getenv()` or `os.environ` / 通过 `os.getenv()` 或 `os.environ` 访问环境变量

### Decorators / 装饰器

- Use `@wraps(func)` when creating decorators to preserve function metadata / 创建装饰器时使用 `@wraps(func)` 保留函数元数据
- Use `@change_workdir` decorator from `nix.py` to change working directory for flake operations / 使用 `nix.py` 中的 `@change_workdir` 装饰器更改 flake 操作的工作目录

```python
def change_workdir(func):
    @wraps(func)
    def wrapper(*args, **kw):
        # ... implementation / 实现
        return result
    return wrapper
```

### MacOS-Specific Code / macOS 特定代码

- Wrap macOS-only imports/functionality with `if ISMAC:` checks / 用 `if ISMAC:` 检查包装 macOS 专用的导入/功能
- Use platform detection from `sd.utils.enums`: / 使用 `sd.utils.enums` 中的平台检测：
  - `ISMAC` - True on macOS / macOS 上为 True
  - `ISLINUX` - True on Linux / Linux 上为 True
  - `SYSTEM_OS` - "darwin" or "linux" / "darwin" 或 "linux"
  - `SYSTEM_ARCH` - "aarch64" or "x86_64" / "aarch64" 或 "x86_64"

### Pre-commit Hooks / Pre-commit 钩子

The project uses pre-commit (configured in `.pre-commit-config.yaml`). Run:
项目使用 pre-commit（配置在 `.pre-commit-config.yaml`）。运行：

```bash
uv run pre-commit install
```
