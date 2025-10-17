#!/usr/bin/env python3
"""
命令行接口模块
"""

import click
import sys
from pathlib import Path
from actmap.log import (
    set_debug, debug, info, success, error, warning, 
    progress, step, debug_plain, fatal
)
from actmap.core.actmap import ActMap


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


def handle_output_actmap(output_actmap, config, debug_mode):
    """处理 --output-actmap 选项"""
    if output_actmap and len(output_actmap) == 2:
        source_interface, target_interface = output_actmap
        _output_actmap_mappings(source_interface, target_interface, config, debug_mode)
        return True
    return False


def map_command(debug_mode, target, config, command_args):
    """处理 map 命令逻辑"""
    debug("🚀 开始命令映射")
    debug(f"接收到的参数: {command_args}")
    
    if not command_args:
        error("没有提供要映射的命令")
        return

    cmd_str = ' '.join(command_args)
    cmd_parts = list(command_args)

    try:
        # 使用 ActMap 进行实际映射
        if config:
            config_path = Path(config)
        else:
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)
        
        # 检测源包管理器类型
        first_part = cmd_parts[0]
        if first_part == 'apt':
            source_interface = "apt"
            args_to_parse = cmd_parts[1:]
        elif first_part == 'pacman':
            source_interface = "pacman"
            args_to_parse = cmd_parts[1:]
        else:
            if any(part in ['install', 'search', 'remove', 'update', 'upgrade'] for part in cmd_parts):
                source_interface = "apt"
                args_to_parse = cmd_parts
            else:
                source_interface = "pacman"
                args_to_parse = cmd_parts

        # 设置目标包管理器
        if target:
            target_interface = target.lower()
        else:
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_action', 'pacman')

        if debug_mode:
            progress("正在解析命令...")
            debug(f"源包管理器: {source_interface}")
            debug(f"目标包管理器: {target_interface}")

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


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='显示调试信息')
@click.option('-t', '--target', help='目标包管理器')
@click.option('--config', help='配置文件路径')
@click.option('--output-actmap', nargs=2, help='输出配置的映射关系，例如: --output-actmap pacman apt')
@click.argument('command_args', nargs=-1, type=click.UNPROCESSED)
def cli(debug_mode, target, config, output_actmap, command_args):
    """ActMap - 智能命令映射工具
    
    将一种包管理器的命令映射到另一种包管理器。
    
    示例:
        actmap --output-actmap pacman apt        # 输出映射配置
        actmap -- apt install vim git            # 映射命令
        actmap apt install vim git               # 简写形式
        actmap -t apt --debug -- pacman -Syu     # 指定目标和调试
    """
    set_debug(debug_mode)
    
    # 处理 --output-actmap
    if output_actmap:
        handle_output_actmap(output_actmap, config, debug_mode)
        return
    
    # 处理命令映射
    if command_args:
        # 如果第一个参数是 'map'，去掉它（为了向后兼容）
        if command_args[0] == 'map':
            command_args = command_args[1:]
        
        map_command(debug_mode, target, config, command_args)
    else:
        # 显示帮助
        click.echo("请使用 'actmap --help' 查看使用方法")


if __name__ == '__main__':
    cli()