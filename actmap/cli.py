#!/usr/bin/env python3
"""
命令行接口模块
"""

import click
import sys, os
from pathlib import Path
from actmap.log import (
    set_debug, debug, info, success, error, warning, 
    progress, step, debug_plain, fatal
)
from actmap.core.actmap import ActMap

def get_available_actions(ctx, param, incomplete):
    """完全自包含的补全函数 - 显示完整命令格式"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_COMPLETE', '')
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


def _output_actmap_mappings(source_interface, target_interface, config_path, debug_mode):
    """输出配置的映射关系"""
    try:
        # 使用 ActMap 加载配置
        if config_path:
            config_path = Path(config_path)
        else:
            # 默认使用 XDG 配置目录
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        
        # 获取支持的动作
        actions = actmap.get_supported_actions()
        
        info(f"📋 映射配置: {source_interface} → {target_interface}")
        print("=" * 80)
        
        # 表头
        print(f"{'状态':<4} {'动作':<15} {'源命令':<25} {'目标命令':<30}")
        print("-" * 80)
        
        supported_count = 0
        
        for action in actions:
            # 检查源接口是否支持该动作
            action_config = actmap.config.get('actions', {}).get(action, {})
            source_supported = source_interface in action_config
            target_supported = target_interface in action_config
            
            # 获取源命令格式
            if source_supported:
                source_cmd = action_config.get(source_interface, {}).get('cmd_format', '不支持')
            else:
                source_cmd = "不支持"
            
            # 获取目标命令格式
            if target_supported:
                target_cmd = action_config.get(target_interface, {}).get('cmd_format', '不支持')
                status = "✅"
                supported_count += 1
            else:
                target_cmd = "不支持"
                status = "❌"
            
            print(f"{status:<4} {action:<15} {source_cmd:<25} {target_cmd:<30}")
            
            # 如果是调试模式，显示触发规则
            if debug_mode:
                source_config = actmap.config.get('action_interfaces', {}).get(source_interface, {})
                triggers = source_config.get('triggers', {}).get('rules', [])
                for rule in triggers:
                    triggers_list = rule.get('trigger', [])
                    for trigger in triggers_list:
                        if trigger.get('action') == action:
                            condition = rule.get('condition', {})
                            params = condition.get('params', [])
                            if params:
                                param_names = [p.get('name', '?') for p in params]
                                print(f"   触发条件: {param_names}")
        
        print("=" * 80)
        success(f"共找到 {supported_count}/{len(actions)} 个支持的映射")
        
    except Exception as e:
        error(f"输出映射配置失败: {e}")
        if debug_mode:
            import traceback
            debug_plain("堆栈跟踪:")
            debug_plain(traceback.format_exc())

def get_source_interfaces(ctx, param, incomplete):
    """获取可用的源包管理器接口列表"""
    return get_available_interfaces(ctx, param, incomplete)

def get_target_interfaces(ctx, param, incomplete):
    """获取可用的目标包管理器接口列表"""
    return get_available_interfaces(ctx, param, incomplete)

@click.group(invoke_without_command=True)
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='显示调试信息')
@click.option('-t', '--target', help='目标包管理器', shell_complete=get_target_interfaces)
@click.option('-s', '--source', help='源包管理器（当自动检测有歧义时使用）', shell_complete=get_source_interfaces)
@click.option('--config', help='配置文件路径')
@click.option('--output-actmap', nargs=2, help='输出配置的映射关系，例如: --output-actmap pacman apt')
@click.option('--list-actmaps', is_flag=True, help='显示当前配置文件中已有的包管理器')
@click.pass_context
def cli(ctx, debug_mode, target, config, source, output_actmap, list_actmaps):
    """ActMap - 智能命令映射工具
    
    将一种包管理器的命令映射到另一种包管理器。
    
    \b
    示例:
        actmap --output-actmap pacman apt        # 输出映射配置
        actmap --list-actmaps                    # 显示已有包管理器
        actmap map -- apt install vim git        # 映射命令
        actmap map apt install vim git           # 简写形式
        actmap -t apt --debug map -- pacman -Syu # 指定目标和调试
    """
    # 确保子命令可以访问这些选项
    ctx.ensure_object(dict)
    ctx.obj['debug_mode'] = debug_mode
    ctx.obj['target'] = target
    ctx.obj['config'] = config
    
    # 处理 --list-actmaps 选项
    if list_actmaps and not ctx.invoked_subcommand:
        _list_actmaps_in_config(config, debug_mode)
        return
    
    # 处理 --output-actmap 选项（如果没有子命令）
    if output_actmap and not ctx.invoked_subcommand:
        source_interface, target_interface = output_actmap
        _output_actmap_mappings(source_interface, target_interface, config, debug_mode)
        return
    
    # 如果没有子命令也没有选项，显示帮助
    if not ctx.invoked_subcommand and not any([output_actmap, list_actmaps]):
        click.echo(ctx.get_help())


def get_available_interfaces(ctx, param, incomplete):
    """获取可用的包管理器接口列表用于补全"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_COMPLETE', '')
        if not comp_env.endswith('_complete'):
            return []

        import tomllib
        config_path = Path.home() / '.config' / 'actmap' / 'config.toml'
        if not config_path.exists():
            return []

        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        interfaces = list(config.get('action_interfaces', {}).keys())
        return [
            CompletionItem(interface)
            for interface in interfaces
            if incomplete in interface
        ]
        
    except Exception:
        return []
    

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('command', nargs=-1, type=click.UNPROCESSED, shell_complete=get_available_interfaces)
@click.pass_context
def map(ctx, command):
    """映射命令
    """

    # 从上下文获取选项
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    source = ctx.obj.get('source')  # 新增：获取源选项
    
    # 设置调试模式
    set_debug(debug_mode)
    
    debug("🚀 开始命令映射")
    debug(f"接收到的参数: {command}")
    debug(f"调试模式: {debug_mode}")
    debug(f"目标包管理器: {target}")
    debug(f"源包管理器: {source}")  # 新增调试信息
    debug(f"配置文件: {config}")
    
    try:
        # 主要业务逻辑
        if not command:
            error("没有提供要映射的命令")
            fatal("命令参数为空")
        
        cmd_str = ' '.join(command)
        cmd_parts = list(command)
        
        if debug_mode:
            info(f"处理命令: {cmd_str}")
        
        # 使用 ActMap 进行实际映射
        if config:
            config_path = Path(config)
        else:
            # 默认使用 XDG 配置目录
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)
        
        # 检测源包管理器：优先使用用户指定的源
        if source:
            source_interface = source
            if debug_mode:
                progress(f"使用用户指定的源包管理器: {source_interface}")
        else:
            source_interface = actmap.detect_source_interface(cmd_parts)
            if not source_interface:
                fatal("无法自动检测源包管理器，请使用 -s/--source 选项明确指定")
        
        # 使用完整参数进行解析（不移除命令名）
        args_to_parse = cmd_parts

        if debug_mode:
            debug(f"完整解析参数: {args_to_parse}")
        
        # 设置目标包管理器：优先级：CLI选项 > 配置文件默认值 > 默认值pacman
        if target:
            target_interface = target.lower()
        else:
            # 从配置文件中读取默认目标
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_action', 'pacman')
        
        available_interfaces = actmap.get_supported_interfaces()
        if target_interface not in available_interfaces:
            error(f"不支持的目标包管理器: {target_interface}")
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
                info("执行普通命令")
        
        # 执行映射
        if debug_mode:
            step("执行命令映射...")
        
        mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)
        
        if mapped_command:
            # 只输出映射后的命令
            print(mapped_command)
            if debug_mode:
                success("操作执行成功")
        else:
            if debug_mode:
                error("无法映射命令")
                fatal("映射失败")
            else:
                # 在非调试模式下，如果映射失败，静默退出
                return
        
    except Exception as e:
        error(f"命令映射失败: {e}")
        debug("详细错误信息:", str(e))
        if debug_mode:
            import traceback
            debug_plain("堆栈跟踪:")
            debug_plain(traceback.format_exc())
        fatal("程序异常退出")

def _list_actmaps_in_config(config_path, debug_mode):
    """显示当前配置文件中已有的包管理器"""
    try:
        # 使用 ActMap 加载配置
        if config_path:
            config_path = Path(config_path)
        else:
            # 默认使用 XDG 配置目录
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        
        # 获取配置文件中定义的包管理器
        action_interfaces = actmap.config.get('action_interfaces', {})
        available_actmaps = list(action_interfaces.keys())
        
        if not available_actmaps:
            info("当前配置文件中没有定义包管理器")
            return
        
        info("📦 当前配置文件中的包管理器:")
        for actmap_name in sorted(available_actmaps):
            # 检查是否有对应的动作定义
            actions_with_this_actmap = []
            for action_name, action_config in actmap.config.get('actions', {}).items():
                if actmap_name in action_config:
                    actions_with_this_actmap.append(action_name)
            
            if actions_with_this_actmap:
                print(f"  ✅ {actmap_name} - 支持 {len(actions_with_this_actmap)} 个动作")
            else:
                print(f"  ⚠️  {actmap_name} - 无动作定义")
        
        # 显示默认目标
        default_target = actmap.config.get('config', {}).get('default_target_action')
        if default_target:
            print(f"\n🎯 默认目标包管理器: {default_target}")
        
        print(f"\n💡 使用 'actmap --output-actmap <源> <目标>' 查看具体映射关系")
        
    except Exception as e:
        error(f"读取配置文件失败: {e}")
        if debug_mode:
            import traceback
            debug_plain("堆栈跟踪:")
            debug_plain(traceback.format_exc())

@click.command()
@click.argument('action_name', shell_complete=get_available_actions)
@click.argument('params', nargs=-1)
@click.pass_context
def act(ctx, action_name, params):
    """根据动作来映射命令
    
    \b
    示例:
        actmap act install vim git              # 安装包
        actmap act search python == editor      # 搜索包 (使用 == 分隔参数)
        actmap act update                       # 更新数据库  
        actmap act list_installed               # 列出已安装包
    """
    # 现有的 act 函数实现保持不变
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    
    set_debug(debug_mode)
    
    debug("🚀 开始直接动作执行")
    debug(f"动作名称: {action_name}")
    debug(f"参数: {params}")
    debug(f"目标包管理器: {target}")
    debug(f"配置文件: {config}")
        
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
            error(f"使用方法: actmap act {action_name} [参数1] == [参数2] == ...")
            fatal("请提供所有必需的参数")
        
        # 如果有剩余参数且没有更多的配置参数，警告用户
        if remaining_params and debug_mode:
            warning(f"有未使用的参数: {remaining_params}")
        
        # 执行映射
        mapped_command = actmap.map_command_direct(action_name, target_interface, parse_result)
        
        if mapped_command:
            print(mapped_command)
            if debug_mode:
                success("动作执行成功")
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
        
# 添加子命令
cli.add_command(map)
cli.add_command(act)


if __name__ == '__main__':
    cli()