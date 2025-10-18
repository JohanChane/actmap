# actmap 配置说明

## 动作定义

```toml
# === action 接口配置 ===
[actions.install]
description = "安装软件包"
args = ["pkgs"]

# ## list_files (列出包文件)
[actions.list_files]
description = "列出包的文件"
args = ["pkgs"]

# === action 的定义 ===
[actions.install.pacman]
cmd_format = "pacman -S {pkgs}"

[actions.install.apt]
cmd_format = "apt install {pkgs}"

[actions.search_remote.pacman]
cmd_format = "pacman -Ss {pkgs}"

[actions.search_local.pacman]
cmd_format = "pacman -Qs {pkgs}"
```

## 命令参数解析

```toml
[action_interfaces.pacman.args.pacman_command]
cmd_name = "pacman"
arg_parser = "getopt"       # 参数解析的标准 (getopt 或 argparse)

# 全局参数 -h
[[action_interfaces.pacman.args.pacman_command.arg_parse]]
name = "help"
short_opt = "-h"
arg = "help"
is_flag = true

[[action_interfaces.pacman.args.pacman_command.arg_parse]]
name = "cmd_arg"
is_cmd_arg = true       # `pacman -S vim git` 表示 vim git 是属于 pacman 的参数而不是 `-S` 的参数
arg = "targets"         # targets 代表 vim git
nargs = "*"

[[action_interfaces.pacman.args.pacman_command.arg_parse]]
name = "S"
short_opt = "-S"
is_flag = true

[[action_interfaces.pacman.args.pacman_command.arg_parse.sub_args]]     # sub_args: 表示 `-S` 是一个组, 用于区分 `-Ss` 和 `-Qs` 相同的 `-s`。
name = "s"
short_opt = "-s"
arg = "search_flag"
is_flag = true

[[action_interfaces.pacman.args.pacman_command.arg_parse]]
name = "Q"
short_opt = "-Q"
is_flag = true

[[action_interfaces.pacman.args.pacman_command.arg_parse.sub_args]]
name = "s"
short_opt = "-s"
arg = "query_search_flag"
is_flag = true
```

## 命令参数触发规则

```toml
# === pacman 动作触发规则 ===
[action_interfaces.pacman.triggers.pacman_command]
cmd_name = "pacman"

# 全局帮助触发规则
[[action_interfaces.pacman.triggers.pacman_command.rules]]
name = "help_operations"
condition = { params = [{ name = "help" }] }
trigger = [
    { params = [], action = "help" }
]

# Sync 操作组 (-S 相关)
[[action_interfaces.pacman.triggers.pacman_command.rules]]
name = "sync_operations"
condition = { params = [{ name = "S" }] }
trigger = [
    { params = [{ name = "s" }], action = "search_remote", arg_map = { targets = "pkgs" } },    # 表示 `pacman -Ss` 会触发 search action, 并将 pacman 命令的 targets 传给 search action 的 pkgs
    { params = [], action = "install", arg_map = { targets = "pkgs" } }                         # 表示 `pacman -S` 会触发 install action。e.g. `pacman -S vim git`
]

# Query 操作组 (-Q 相关)
[[action_interfaces.pacman.triggers.pacman_command.rules]]
name = "query_operations"
condition = { params = [{ name = "Q" }] }
trigger = [
    { params = [{ name = "s" }], action = "search_local", arg_map = { targets = "pkgs" } },     # 表示 `pacman -Qs` 会触发 search_local action
    { params = [], action = "list_installed" }                                                  # 表示 `pacman -Q` 会触发 list_installed action
]
```