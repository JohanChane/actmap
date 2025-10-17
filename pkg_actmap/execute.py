#!/usr/bin/env python3
"""
执行映射后的命令
"""

import click
import subprocess
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from actmap.core.actmap import ActMap
from actmap.log import (
    set_debug, debug, info, success, error, warning,
    progress, step, debug_plain, fatal
)

def get_available_actions(ctx, param, incomplete):
    """获取可用的动作列表用于补全"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_EXECUTE_COMPLETE', '')
        if not comp_env.endswith('_complete'):
            return []

        import tomllib
        config_path = Path.home() / '.config' / 'actmap' / 'config.toml'
        if not config_path.exists():
            return []

        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        actions_config = config.get('actions', {})
        default_target = config.get('config', {}).get('default_target_action', 'pacman')
        completions = []
        
        for action_name, action_config in actions_config.items():
            if incomplete not in action_name:
                continue
                
            # 获取动作描述
            description = action_config.get('description', '动作')
            
            # 获取默认目标的命令格式
            target_config = action_config.get(default_target, {})
            cmd_format = target_config.get('cmd_format', '')
            
            # 构建帮助信息
            if cmd_format:
                help_text = f"{description} | {cmd_format}"
            else:
                help_text = f"{description} | 无 {default_target} 命令格式"
            
            # 创建补全项
            completions.append(
                CompletionItem(
                    action_name, 
                    help=help_text
                )
            )
        
        return completions
        
    except Exception:
        return []

def get_available_interfaces(ctx, param, incomplete):
    """获取可用的包管理器接口列表用于补全"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_EXECUTE_COMPLETE', '')
        if not comp_env.endswith('_complete'):
            return []

        import tomllib
        config_path = Path.home() / '.config' / 'actmap' / 'config.toml'
        if not config_path.exists():
            return []

        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        interfaces = list(config.get('action_interfaces', {}).keys())
        completions = []
        
        for interface in interfaces:
            if incomplete not in interface:
                continue
                
            # 获取该接口支持的动作数量
            action_count = 0
            for action_name, action_config in config.get('actions', {}).items():
                if interface in action_config:
                    action_count += 1
            
            # 为每个包管理器添加说明
            descriptions = {
                'pacman': 'Arch Linux 包管理器',
                'apt': 'Debian/Ubuntu 包管理器', 
                'dnf': 'Fedora 包管理器',
                'brew': 'macOS 包管理器',
                'zypper': 'openSUSE 包管理器',
                'chocolatey': 'Windows 包管理器',
                'scoop': 'Windows 包管理器',
                'winget': 'Windows 包管理器'
            }
            
            description = descriptions.get(interface, '包管理器')
            help_text = f"{description} | 支持 {action_count} 个动作"
            
            completions.append(
                CompletionItem(
                    interface, 
                    help=help_text
                )
            )
        
        return completions
        
    except Exception:
        return []

def _need_confirmation(action: str, interactive: bool, force: bool) -> bool:
    """判断是否需要确认执行"""
    # 强制模式：直接执行
    if force:
        return False

    # 交互模式：总是确认
    if interactive:
        return True

    # 安全操作：直接执行
    safe_actions = ['search', 'info', 'help', 'list_installed']
    if action in safe_actions:
        return False

    # 其他操作：需要确认
    return True

def _confirm_execution(command: str) -> bool:
    """确认是否执行命令"""
    click.echo(f"⚠️  即将执行: {command}")
    
    try:
        response = input("确认执行? [y/N]: ").strip().lower()
        return response == 'y'
    except KeyboardInterrupt:
        click.echo("\n取消执行")
        return False

@click.group(invoke_without_command=True)
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='显示调试信息')
@click.option('-t', '--target', help='目标包管理器', shell_complete=get_available_interfaces)
@click.option('--config', help='配置文件路径')
@click.option('-i', '--interactive', is_flag=True, help='交互模式，执行前确认')
@click.option('-f', '--force', is_flag=True, help='强制模式，直接执行不确认')
@click.pass_context
def execute(ctx, debug_mode, target, config, interactive, force):
    """执行映射后的命令"""
    # 确保子命令可以访问这些选项
    ctx.ensure_object(dict)
    ctx.obj['debug_mode'] = debug_mode
    ctx.obj['target'] = target
    ctx.obj['config'] = config
    ctx.obj['interactive'] = interactive
    ctx.obj['force'] = force

    # 如果没有子命令，显示帮助
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())

@execute.command()
@click.argument('action_name', shell_complete=get_available_actions)
@click.argument('params', nargs=-1)
@click.pass_context
def act(ctx, action_name, params):
    """直接执行指定的动作
    
    \b
    示例:
        actmap-execute act install vim git              # 安装包
        actmap-execute act search python == editor      # 搜索包 (使用 == 分隔参数)
        actmap-execute act update                       # 更新数据库  
        actmap-execute act list_installed               # 列出已安装包
    """
    # 从上下文中获取选项
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    interactive = ctx.obj.get('interactive', False)
    force = ctx.obj.get('force', False)
    
    set_debug(debug_mode)
    
    debug("🚀 开始直接动作执行")
    debug(f"动作名称: {action_name}")
    debug(f"参数: {params}")
    debug(f"目标包管理器: {target}")
    debug(f"配置文件: {config}")
    debug(f"交互模式: {interactive}")
    debug(f"强制模式: {force}")
    
    try:
        # 使用 ActMap 执行动作
        if config:
            config_path = Path(config)
        else:
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)
        
        # 设置目标包管理器
        if target:
            target_interface = target.lower()
        else:
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_action', 'pacman')
        
        # 检查动作是否支持
        supported_actions = actmap.get_supported_actions()
        if action_name not in supported_actions:
            error(f"不支持的动作: {action_name}")
            error(f"支持的动作: {', '.join(supported_actions)}")
            fatal("请使用支持的动作名称")
        
        # 构建解析结果
        parse_result = {
            'parsed_kwargs': {},
            'present_params': {},
            'detected_command': None
        }
        
        # 根据动作类型处理参数
        action_config = actmap.config.get('actions', {}).get(action_name, {})
        action_args = action_config.get('args', [])
        
        if debug_mode:
            debug(f"动作参数定义: {action_args}")
        
        # 参数解析逻辑：按顺序分配，遇到 == 切换到下一个参数
        remaining_params = list(params)
        parse_result['parsed_kwargs'] = {}
        
        for i, arg_name in enumerate(action_args):
            current_arg_values = []
            
            # 从剩余参数中取，直到遇到 == 或没有更多参数
            while remaining_params:
                param = remaining_params[0]
                if param == '==':
                    # 遇到分隔符，移除它并切换到下一个参数
                    remaining_params.pop(0)
                    break
                else:
                    # 普通参数，添加到当前参数值
                    current_arg_values.append(remaining_params.pop(0))
            
            parse_result['parsed_kwargs'][arg_name] = current_arg_values
        
        if debug_mode:
            debug(f"参数解析结果: {parse_result['parsed_kwargs']}")
            debug(f"剩余未处理的参数: {remaining_params}")
        
        # 检查必需参数是否都有值
        missing_args = []
        for arg_name in action_args:
            if not parse_result['parsed_kwargs'][arg_name]:
                missing_args.append(arg_name)
        
        if missing_args:
            error(f"缺少必需参数: {', '.join(missing_args)}")
            error(f"使用方法: actmap-execute act {action_name} [参数1] == [参数2] == ...")
            fatal("请提供所有必需的参数")
        
        # 如果有剩余参数且没有更多的配置参数，警告用户
        if remaining_params and debug_mode:
            warning(f"有未使用的参数: {remaining_params}")
        
        # 执行映射
        mapped_command = actmap.map_command_direct(action_name, target_interface, parse_result)
        
        if mapped_command:
            info(f"映射后的命令: {mapped_command}")
            
            # 判断是否需要确认
            need_confirmation = _need_confirmation(action_name, interactive, force)
            
            if need_confirmation:
                if not _confirm_execution(mapped_command):
                    info("用户取消执行")
                    return
            
            # 执行命令
            step("执行命令...")
            try:
                result = subprocess.run(mapped_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)
            except KeyboardInterrupt:
                sys.exit(130)
        else:
            error("无法映射命令")
            fatal("映射失败")
        
    except Exception as e:
        error(f"动作执行失败: {e}")
        if debug_mode:
            import traceback
            debug_plain("堆栈跟踪:")
            debug_plain(traceback.format_exc())
        fatal("程序异常退出")

def get_available_package_managers(ctx, param, incomplete):
    """获取可用的包管理器列表用于补全"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_EXECUTE_COMPLETE', '')
        if not comp_env.endswith('_complete'):
            return []

        import tomllib
        config_path = Path.home() / '.config' / 'actmap' / 'config.toml'
        if not config_path.exists():
            return []

        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        interfaces = list(config.get('action_interfaces', {}).keys())
        completions = []
        
        for interface in interfaces:
            if incomplete not in interface:
                continue
                
            # 为每个包管理器添加说明
            descriptions = {
                'pacman': 'Arch Linux 包管理器',
                'apt': 'Debian/Ubuntu 包管理器', 
                'dnf': 'Fedora 包管理器',
                'brew': 'macOS 包管理器',
                'zypper': 'openSUSE 包管理器',
                'chocolatey': 'Windows 包管理器',
                'scoop': 'Windows 包管理器',
                'winget': 'Windows 包管理器'
            }
            
            description = descriptions.get(interface, '包管理器')
            help_text = f"{description}"
            
            completions.append(
                CompletionItem(
                    interface, 
                    help=help_text
                )
            )
        
        return completions
        
    except Exception:
        return []

def get_command_completion(ctx, param, incomplete):
    """获取命令补全建议"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_EXECUTE_COMPLETE', '')
        if not comp_env.endswith('_complete'):
            return []

        # 获取已输入的参数
        params = ctx.params.copy()
        command_parts = params.get('command', [])
        
        # 如果还没有输入包管理器名称，提供包管理器补全
        if not command_parts:
            return get_available_package_managers(ctx, param, incomplete)
        
        # 已经输入了包管理器名称，提供该包管理器的命令补全
        package_manager = command_parts[0]
        
        import tomllib
        config_path = Path.home() / '.config' / 'actmap' / 'config.toml'
        if not config_path.exists():
            return []

        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        # 获取该包管理器支持的命令
        interface_config = config.get('action_interfaces', {}).get(package_manager, {})
        args_config = interface_config.get('args', {})
        
        completions = []
        
        # 查找该包管理器支持的命令
        for cmd_key, cmd_config in args_config.items():
            if cmd_key.endswith('_command'):
                cmd_name = cmd_config.get('cmd_name')
                if cmd_name and incomplete in cmd_name:
                    # 获取命令描述
                    description = f"{package_manager} 命令"
                    
                    completions.append(
                        CompletionItem(
                            cmd_name, 
                            help=description
                        )
                    )
        
        return completions
        
    except Exception:
        return []
    
@execute.command()
@click.argument('command', nargs=-1, type=click.UNPROCESSED, shell_complete=get_command_completion)
@click.pass_context
def map(ctx, command):
    """执行映射后的命令（传统 map 方式）

    \b
    示例:
        actmap-execute map -- apt install vim git
        actmap-execute -i map -- pacman -Syu
        actmap-execute -f map -- apt remove vim
        actmap-execute -t apt map -- pacman -S vim
    """
    # 从上下文中获取选项
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    interactive = ctx.obj.get('interactive', False)
    force = ctx.obj.get('force', False)
    
    # 设置调试模式
    set_debug(debug_mode)

    debug("🚀 开始命令映射")
    debug(f"接收到的参数: {command}")
    debug(f"调试模式: {debug_mode}")
    debug(f"目标包管理器: {target}")
    debug(f"配置文件: {config}")
    debug(f"交互模式: {interactive}")
    debug(f"强制模式: {force}")

    try:
        # 主要业务逻辑
        if not command:
            error("没有提供要映射的命令")
            fatal("命令参数为空")

        cmd_str = ' '.join(command)
        cmd_parts = list(command)

        info(f"处理命令: {cmd_str}")

        # 使用 ActMap 进行实际映射 - 默认使用 XDG 配置
        if config:
            config_path = Path(config)
        else:
            # 默认使用 XDG 配置目录
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)

        # 🔧 修复：使用与 actmap 相同的自动检测逻辑
        source_interface = actmap.detect_source_interface(cmd_parts)
        if not source_interface:
            error("无法自动检测源包管理器")
            fatal("请确保命令格式正确，如: apt install vim 或 pacman -S vim")

        # 🔧 修复：使用完整参数进行解析（不移除命令名）
        args_to_parse = cmd_parts

        # 设置目标包管理器：优先级：CLI选项 > 配置文件默认值 > 默认值pacman
        if target:
            target_interface = target.lower()
        else:
            # 从配置文件中读取默认目标
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_action', 'pacman')

        # 检查目标包管理器是否在配置文件中定义
        available_interfaces = list(actmap.config.get('action_interfaces', {}).keys())
        if target_interface not in available_interfaces:
            error(f"目标包管理器 '{target_interface}' 在配置文件中未定义")
            error(f"配置文件中定义的包管理器: {', '.join(available_interfaces)}")
            fatal("请使用配置文件中定义的包管理器")

        if debug_mode:
            progress("正在解析命令...")
            debug(f"源包管理器: {source_interface}")
            debug(f"目标包管理器: {target_interface}")
            debug("命令分词:", cmd_parts)
            debug("解析参数:", args_to_parse)
            step("正在查找映射规则...")

        # 解析参数
        parse_result = actmap.parse_arguments(source_interface, args_to_parse)

        # 检测动作
        action = actmap.detect_action(source_interface, parse_result)

        if debug_mode:
            if action:
                success(f"找到 {action} 操作")
            else:
                warning("未找到匹配的操作")

        # 执行映射
        if debug_mode:
            step("执行命令映射...")

        mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)

        if not mapped_command:
            error("无法映射命令")
            fatal("映射失败")

        info(f"映射后的命令: {mapped_command}")

        # 判断是否需要确认
        need_confirmation = _need_confirmation(action, interactive, force)

        if need_confirmation:
            if not _confirm_execution(mapped_command):
                info("用户取消执行")
                return

        # 执行命令
        step("执行命令...")
        try:
            result = subprocess.run(mapped_command, shell=True, check=True)
            success("命令执行成功")
        except subprocess.CalledProcessError as e:
            error(f"命令执行失败，退出码: {e.returncode}")
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            error("命令被用户中断")
            sys.exit(130)

    except Exception as e:
        error(f"命令执行失败: {e}")
        debug("详细错误信息:", str(e))
        if debug_mode:
            import traceback
            debug_plain("堆栈跟踪:")
            debug_plain(traceback.format_exc())
        fatal("程序异常退出")
if __name__ == '__main__':
    execute()