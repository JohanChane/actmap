# ActMap - 智能命令映射工具

一个强大的命令行工具，用于在不同包管理器之间智能映射命令。让你在任意系统上使用熟悉的包管理器语法！

## 🌟 特性

- **多包管理器支持**: pacman, apt, dnf, brew, zypper
- **智能命令解析**: 自动识别命令意图（安装、搜索、更新等）
- **灵活映射**: 将任何包管理器命令映射到目标包管理器
- **安全执行**: 交互式确认和强制执行模式
- **易于扩展**: 基于配置文件的模块化设计 (用配置实现命令映射)
- **详细调试**: 丰富的日志输出和调试信息

## 🚀 快速开始

### 安装

```sh
# 从源码安装
git clone https://github.com/your-username/actmap.git
cd actmap
pipx install .
```

命令补全:

```sh
# ## zsh
if command -v actmap &>/dev/null; then
  eval "$(_ACTMAP_COMPLETE=zsh_source actmap)"
fi

if command -v actmap-execute &>/dev/null; then
  eval "$(_ACTMAP_EXECUTE_COMPLETE=zsh_source actmap-execute)"
fi
```

Alias (optional):

```sh
alias am="actmap"
alias ame="actmap-execute"
```

### 基本使用

init-config and set default target actmap:

```sh
# 初始化用户配置（首次使用）
actmap-generate --init-config

# 编辑 ~/.config/actmap/config.toml, 配置默认的
default_target_actmap = "<your default target>"  # `actmap -t, --target` 会覆盖这个选项
```

actmap map (自动检测 map 之后的命令来映射到 target actmap):

```sh
# 将 apt 命令映射到 target actmap
actmap map apt install vim git
# 如果 target_actmap 是 "pacman"，则映射为: pacman -S vim git

# 将 pacman 命令映射到 apt actmap
actmap -t apt map pacman -S vim git  # 映射为: apt install vim git

# 查看 pacman actman 到 apt actmap 的映射
actmap --output-actmap pacman apt
```

actmap act (根据指定的 action 来映射命令):

```sh
actmap act install vim git
# 如果 target_actmap 是 "pacman"，则执行: pacman -S vim git
```

actmap-execute (执行映射之后的命令) map :

```sh
actmap-execute map pacman -S vim git

# 交互式执行（推荐用于危险操作）
actmap-execute -i map pacman -Rns vim

# 强制执行（跳过确认）
actmap-execute -f map apt remove python3
```

actmap-execute act:

```sh
actmap-execute install vim git

# 如果有动作 grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
actmap-execute act grep_log foo.log bar.log == ERROR == write
# 会执行 cat foo.log bar.log | grep -i 'ERROR' | grep -i 'write'
```

## 使用 actmap-generate 管理 actmap 配置

```sh
# 初始化用户配置（创建 ~/.config/actmap/）
actmap-generate --init-config

# 使用 actmaps
actmap-generate --use-actmaps pacman,apt,dnf,brew,zypper,scoop,winget,chocolatey

# 新增 actmaps
actmap-generate --add-actmaps brew,scoop,winget

# 查看支持的 actmaps
actmap-generate --list-actmaps
```

## 🎯 使用示例

### 使用你熟悉的包管理来安装 vim git

```sh
# debian
actmap map apt install vim git
# arch
actmap map pacman -S search vim git
```

### 使用你熟悉的动作来安装 vim git

```sh
# use `install` action
actmap act install vim git
```

### 临时切换目标

```sh
# 如果你忘记了 pip 显示包的信息的命令, 则可以使用任意一种你熟悉的方式来执行
actmap-execute -t pip map pacman -Si <pkg>   # 会映射为: pip show <pkg>
# OR
actmap-execute -t pip map brew info <pkg>
```

## `actmap-generate` 的 actmap 配置

### 已经配置的 actmaps

```sh
actmap --list-actmaps
```

```
ℹ️ INFO: 📦 Package managers in current configuration:
  ✅ apt - supports 15 actions
  ✅ brew - supports 15 actions
  ✅ cargo - supports 8 actions
  ✅ chocolatey - supports 15 actions
  ✅ dnf - supports 15 actions
  ✅ npm - supports 8 actions
  ✅ pacman - supports 15 actions
  ✅ pip - supports 10 actions
  ✅ scoop - supports 15 actions
  ✅ winget - supports 15 actions
  ✅ zypper - supports 15 actions
```

### output-actmap examples

pacman -> apt:

```sh
actmap --output-actmap pacman apt
```

```
================================================================================
Status Action          Source Command            Target Command
--------------------------------------------------------------------------------
✅    install         pacman -S {pkgs}          apt install {pkgs}
✅    remove          pacman -R {pkgs}          apt remove {pkgs}
✅    search          pacman -Ss {pkgs}         apt search {pkgs}
✅    update          pacman -Sy                apt update
✅    upgrade         pacman -Syu               apt upgrade
✅    force_update    pacman -Syy               apt update --refresh-all
✅    force_upgrade   pacman -Syyu              apt update --refresh-all && apt upgrade
✅    info            pacman -Si {pkgs}         apt show {pkgs}
✅    list_installed  pacman -Q                 apt list --installed
✅    clean           pacman -Sc                apt autoclean
✅    help            pacman -h                 apt --help
✅    list_files      pacman -Ql {pkgs}         dpkg -L {pkgs}
✅    find_file_owner pacman -Qo {files}        dpkg -S {files}
✅    find_file_owner_remote pacman -F {files}         apt-file search {files}
✅    download_source asp export {pkgs}         apt source {pkgs}
================================================================================
```

pacman -> pip:

```sh
actmap --output-actmap pacman pip
```

```
================================================================================
Status Action          Source Command            Target Command
--------------------------------------------------------------------------------
✅    install         pacman -S {pkgs}          pip install {pkgs}
✅    remove          pacman -R {pkgs}          pip uninstall {pkgs}
✅    search          pacman -Ss {pkgs}         pip search {pkgs}
✅    update          pacman -Sy                pip install --upgrade pip
✅    upgrade         pacman -Syu               pip install --upgrade {pkgs}
❌    force_update    pacman -Syy               Not supported
❌    force_upgrade   pacman -Syyu              Not supported
✅    info            pacman -Si {pkgs}         pip show {pkgs}
✅    list_installed  pacman -Q                 pip list
✅    clean           pacman -Sc                pip cache purge
✅    help            pacman -h                 pip --help
❌    list_files      pacman -Ql {pkgs}         Not supported
❌    find_file_owner pacman -Qo {files}        Not supported
❌    find_file_owner_remote pacman -F {files}         Not supported
✅    download_source asp export {pkgs}         pip download {pkgs}
================================================================================
```

## actmap 配置格式说明

See [ref](./doc/actmap_config_zh.md)