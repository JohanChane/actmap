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
@click.pass_context
def map(ctx, command, debug_mode, target, config):
    """映射命令到对应的操作
    
    使用示例:
        actmap map -- apt install vim git
        actmap map apt install vim git
        actmap -t apt --debug map -- pacman -Syu
        actmap -t pacman map apt search python
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
        config_path = Path(config) if config else Path("config.toml")
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