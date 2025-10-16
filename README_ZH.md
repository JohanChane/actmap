# ActMap - 智能命令映射工具

一个强大的命令行工具，用于在不同包管理器之间智能映射命令。让你在任意系统上使用熟悉的包管理器语法！

## 项目状态

当前处于开发状态, 是个半成品, 很多东西还没有确定下来, 随后可能会更改较多的东西。

## 🌟 特性

- **多包管理器支持**: pacman, apt, dnf, brew, zypper
- **智能命令解析**: 自动识别命令意图（安装、搜索、更新等）
- **灵活映射**: 将任何包管理器命令映射到目标包管理器
- **安全执行**: 交互式确认和强制执行模式
- **易于扩展**: 基于配置文件的模块化设计 (用配置实现命令映射)
- **详细调试**: 丰富的日志输出和调试信息

## 🚀 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/your-username/actmap.git
cd actmap
pip install -e .
```

### 基本使用

```bash
# 初始化用户配置（首次使用）
actmap-generate --init-config

# 配置 ~/.config/actmap/config.toml
default_target_action = "<你系统的包管理器>"  # 默认目标包管理器

# 将 apt 命令映射到默认目标（配置文件中的 default_target_action）
actmap map -- apt install vim git
# 如果 default_target_action = "pacman"，输出: pacman -S vim git

# 将 pacman 命令映射到默认目标
actmap map -- pacman -Syu
# 如果 default_target_action = "apt"，输出: apt update && apt upgrade

# 直接执行映射后的命令（使用默认目标）
actmap-execute -- apt search python

# 查看映射配置
actmap map --output-actmap pacman apt
```

## 📖 详细用法

### 命令映射

```bash
# 基本语法
actmap map [选项] -- <源命令>

# 使用默认目标映射（从配置文件读取）
actmap map -- apt install vim
actmap map -- pacman -S vim
actmap map --debug -- apt remove python3

# 指定目标包管理器（覆盖默认配置）
actmap map -t apt -- pacman -S vim
# 输出: apt install vim

actmap map -t dnf -- apt update
# 输出: dnf check-update

actmap map -t brew -- pacman -Ss editor
# 输出: brew search editor

# 指定配置文件
actmap map --config my_config.toml -t apt -- pacman -S vim
```

### 直接执行

```bash
# 使用默认目标执行
actmap-execute -- apt install vim

# 交互式执行（推荐用于危险操作）
actmap-execute -i -- pacman -Rns vim

# 强制执行（跳过确认）
actmap-execute -f -- apt remove python3

# 调试模式
actmap-execute -d -- apt search python

# 指定目标包管理器
actmap-execute -t pacman -- apt update
actmap-execute -t dnf -- brew install git
```

### 配置管理

```bash
# 初始化用户配置（创建 ~/.config/actmap/）
actmap-generate --init-config

# 生成自定义配置文件
actmap-generate -o custom.toml -m pacman -m apt -m dnf

# 查看支持的包管理器
actmap-generate --list-actmaps
```

## 🔧 配置说明

ActMap 使用 TOML 配置文件定义包管理器行为。默认配置文件位于 `~/.config/actmap/config.toml`。

### 默认目标配置
```toml
[config]
default_target_action = "pacman"  # 默认目标包管理器
```

### 动作定义示例
```toml
[actions.install]
description = "安装软件包"
args = ["pkgs"]

[actions.install.pacman]
cmd_format = "pacman -S {pkgs}"

[actions.install.apt]
cmd_format = "apt install {pkgs}"

[actions.install.dnf]
cmd_format = "dnf install {pkgs}"
```

### 配置优先级
1. 命令行 `-t/--target` 选项（最高优先级）
2. 配置文件中的 `default_target_action`
3. 默认值 `pacman`（最低优先级）

## 🎯 使用示例

### 场景1：在 Arch Linux 上使用 apt 习惯
```bash
# 配置 default_target_action = "pacman"
actmap map -- apt install vim git
# 输出: pacman -S vim git

actmap map -- apt search python
# 输出: pacman -Ss python

actmap map -- apt update
# 输出: pacman -Sy
```

### 场景2：在 Ubuntu 上使用 pacman 习惯  
```bash
# 配置 default_target_action = "apt"
actmap map -- pacman -S vim
# 输出: apt install vim

actmap map -- pacman -Syu
# 输出: apt update && apt upgrade

actmap map -- pacman -Ss editor
# 输出: apt search editor
```

### 场景3：临时切换目标
```bash
# 临时映射到不同目标
actmap map -t dnf -- apt install vim
# 输出: dnf install vim

actmap map -t brew -- pacman -S git
# 输出: brew install git
```

## 🗂️ 项目结构

```
actmap/
├── actmap/                 # 核心模块
│   ├── core/              # 核心引擎
│   │   ├── actmap.py      # 主映射类
│   │   ├── factory.py     # 解析器工厂
│   │   └── parsers/       # 参数解析器
│   ├── config/            # 配置加载
│   └── cli.py             # 命令行接口
├── pkg_actmap/            # 包管理器配置
│   ├── actmap_config/     # 各包管理器配置
│   │   ├── pacman.toml
│   │   ├── apt.toml
│   │   └── ...
│   └── generate_config.py # 配置生成工具
├── test/                  # 测试套件
│   ├── test_basic/        # 基础功能测试
│   ├── test_actions/      # 动作测试
│   └── test_repeats/      # 重复选项测试
└── config.toml           # 主配置文件
```

## 🔍 目前已经配置的包管理器

| 包管理器 | 系统 | 状态 |
|---------|------|------|
| Pacman | Arch Linux | ✅ 完全支持 |
| APT | Debian/Ubuntu | ✅ 完全支持 |
| DNF | Fedora | ✅ 完全支持 |
| Brew | macOS | ✅ 完全支持 |
| Zypper | openSUSE | ✅ 完全支持 |

根据配置来实现命令映射, 如果了解 actmap 的命令映射配置, 理论上可以支持任意的包的管理器。

## 🛠️ 开发

### 添加新的包管理器

1. 在 `pkg_actmap/actmap_config/` 创建新的 `.toml` 文件
2. 定义命令格式和解析规则
3. 添加触发规则
4. 测试新配置

### 运行测试

```bash
# 运行所有测试
python test/test_basic/test.py
python test/test_actions/test.py  
python test/test_repeats/test.py

# 调试模式
python -m actmap.cli -d map -- apt install vim
```

### 调试技巧

```bash
# 启用调试输出
actmap -d map -- apt install vim

# 查看详细解析过程
actmap -d map -- pacman -Syyu

# 查看映射关系
actmap map --output-actmap apt pacman
```