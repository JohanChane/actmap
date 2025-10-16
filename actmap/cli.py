#!/usr/bin/env python3
"""
命令行接口模块
"""

import click
from actmap.log import (
    set_debug, debug, info, success, error, warning, 
    progress, step, debug_plain, fatal
)
from actmap.core.actmap import ActMap
from pathlib import Path


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='显示调试信息')
@click.option('-t', '--target', help='目标包管理器 (apt/pacman)')
@click.option('--config', help='配置文件路径')
@click.option('--output-actmap', nargs=2, help='输出配置的映射关系，例如: --output-actmap pacman apt')
@click.pass_context
def map(ctx, command, debug_mode, target, config, output_actmap):
    """映射命令到对应的操作
    
    使用示例:
        actmap map -- apt install vim git
        actmap map apt install vim git
        actmap -t apt --debug map -- pacman -Syu
        actmap -t pacman map apt search python
        actmap map --output-actmap pacman apt  # 输出映射配置
    """
    # 从上下文获取选项，优先级：子命令选项 > 全局选项
    debug_mode = debug_mode or ctx.obj.get('debug_mode', False)
    target = target or ctx.obj.get('target')  # 这里不设置默认值
    config = config or ctx.obj.get('config')
    
    # 设置调试模式
    set_debug(debug_mode)
    
    debug("🚀 开始命令映射")
    debug(f"接收到的参数: {command}")
    debug(f"调试模式: {debug_mode}")
    debug(f"目标包管理器: {target}")
    debug(f"配置文件: {config}")
    debug(f"输出映射: {output_actmap}")
    
    # 处理 --output-actmap 选项
    if output_actmap:
        source_interface, target_interface = output_actmap
        _output_actmap_mappings(source_interface, target_interface, config, debug_mode)
        return
    
    try:
        # 主要业务逻辑
        if not command:
            error("没有提供要映射的命令")
            fatal("命令参数为空")
        
        cmd_str = ' '.join(command)
        cmd_parts = list(command)
        
        if debug_mode:
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
        
        # 检测源包管理器类型（根据第一个参数）
        first_part = cmd_parts[0]
        if first_part == 'apt':
            source_interface = "apt"
            # 移除 'apt' 命令本身，只保留参数
            args_to_parse = cmd_parts[1:]
        elif first_part == 'pacman':
            source_interface = "pacman" 
            # 移除 'pacman' 命令本身，只保留参数
            args_to_parse = cmd_parts[1:]
        else:
            # 如果第一个参数不是已知命令，尝试推断
            if any(part in ['install', 'search', 'remove', 'update', 'upgrade'] for part in cmd_parts):
                source_interface = "apt"
                args_to_parse = cmd_parts
            else:
                source_interface = "pacman"
                args_to_parse = cmd_parts
        
        # 设置目标包管理器：优先级：CLI选项 > 配置文件默认值 > 默认值pacman
        if target:
            target_interface = target.lower()
        else:
            # 从配置文件中读取默认目标
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_action', 'pacman')
        
        if target_interface not in ['apt', 'pacman']:
            error(f"不支持的目标包管理器: {target_interface}")
            fatal("目标包管理器必须是 'apt' 或 'pacman'")
        
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


@click.group()
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='显示调试信息')
@click.option('-t', '--target', help='目标包管理器 (apt/pacman)')
@click.option('--config', help='配置文件路径')
@click.pass_context
def cli(ctx, debug_mode, target, config):
    """ActMap - 智能命令映射工具
    
    将一种包管理器的命令映射到另一种包管理器。
    
    示例:
        actmap map -- apt install vim git
        actmap map apt install vim git
        actmap -t apt --debug map -- pacman -Syu
        actmap -t pacman map apt search python
        actmap map --output-actmap pacman apt  # 输出映射配置
    """
    # 确保子命令可以访问这些选项
    ctx.ensure_object(dict)
    ctx.obj['debug_mode'] = debug_mode
    ctx.obj['target'] = target
    ctx.obj['config'] = config


# 添加子命令
cli.add_command(map)


if __name__ == '__main__':
    cli()