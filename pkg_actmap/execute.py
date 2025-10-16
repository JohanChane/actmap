#!/usr/bin/env python3
"""
执行映射后的命令
"""

import click
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from actmap.core.actmap import ActMap
from actmap.log import (
    set_debug, debug, info, success, error, warning, 
    progress, step, debug_plain, fatal
)


@click.command()
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='显示调试信息')
@click.option('-t', '--target', help='目标包管理器')
@click.option('--config', help='配置文件路径')
@click.option('-i', '--interactive', is_flag=True, help='交互模式，执行前确认')
@click.option('-f', '--force', is_flag=True, help='强制模式，直接执行不确认')
def execute(command, debug_mode, target, config, interactive, force):
    """执行映射后的命令
    
    示例:
        actmap-execute -- apt install vim git
        actmap-execute -i -- pacman -Syu
        actmap-execute -f -- apt remove vim
        actmap-execute -t apt -- pacman -S vim
    """
    # 设置调试模式
    set_debug(debug_mode)
    
    debug("🚀 开始执行命令映射")
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
    warning(f"即将执行命令: {command}")
    click.echo("⚠️  这是一个有影响的操作，确认执行吗？")
    
    try:
        response = input("请输入 'y' 确认执行，或任意键取消: ").strip().lower()
        return response == 'y'
    except KeyboardInterrupt:
        click.echo("\n取消执行")
        return False


if __name__ == '__main__':
    execute()