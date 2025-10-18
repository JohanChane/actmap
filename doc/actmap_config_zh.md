# actmap 配置说明

## 目前参数解析的效果

会区分有没有传入包名:

```sh
actmap -t pacman map apt list --installed            # pacman -Q
actmap -t pacman map apt list --installed vim git    # pacman -Qs vim git
```

能识别 python 的 optget 和 argpase 的写法标准:

```sh
actmap -t pacman map pacman -s vim git -S    # `pacman -Ss vim git`. 我的配置里表示 `S/-s` 只是一个 flag, 但 `-S` 是一个 `group flag`。`vim git` 属于 pacman param。
```

## 动作接口定义

See [base.toml](./base.toml)

## 动作定义

参考 [pacman.toml](./pacman.toml) 和 [apt.toml](./apt.toml) 的 "action 的定义"

## 命令参数解析

参考 [pacman.toml](./pacman.toml) 和 [apt.toml](./apt.toml) 的 "参数解析"

## 命令参数触发规则

参考 [pacman.toml](./pacman.toml) 和 [apt.toml](./apt.toml) 的 "动作触发规则"