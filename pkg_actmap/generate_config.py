#!/usr/bin/env python3
"""
生成完整配置文件的工具
"""

import tomllib
import tomli_w
from pathlib import Path
import click


@click.command()
@click.option('-o', '--output', required=False, help='输出配置文件路径')
@click.option('-m', '--actmap', 'actmaps', multiple=True,
              help='要包含的包管理器名称（可多次使用）')
@click.option('--actmap-config', 'pkg_config_dir', default='actmap_config',
              show_default=True, help='包管理器配置目录路径')
@click.option('--list-actmaps', is_flag=True, help='列出所有可用的包管理器')
def generate_config(output, actmaps, pkg_config_dir, list_actmaps):
    """生成包含多个包管理器的完整配置
    
    示例:
        actmap-generate -o config.toml -m pacman -m apt
        actmap-generate -o my_config.toml -m pacman -m apt -m dnf
        actmap-generate --actmap-config /custom/path -o config.toml -m pacman
        actmap-generate --list-actmaps
    """
    
    if list_actmaps:
        available_packages = get_available_packages(pkg_config_dir)
        print("📦 可用的包管理器:")
        for pkg in available_packages:
            print(f"  - {pkg}")
        return
    
    # 如果没有指定输出路径，报错
    if not output:
        raise click.ClickException("必须指定输出配置文件路径，使用 -o/--output 选项")
    
    # 如果没有指定包管理器，报错
    if not actmaps:
        raise click.ClickException("必须指定至少一个包管理器，使用 -m/--actmap 选项")
    
    # 验证包管理器是否存在
    available_packages = get_available_packages(pkg_config_dir)
    invalid_packages = [pkg for pkg in actmaps if pkg not in available_packages]
    if invalid_packages:
        raise click.ClickException(f"包管理器不存在: {', '.join(invalid_packages)}\n可用的包管理器: {', '.join(available_packages)}")
    
    output_path = Path(output)
    
    # 处理 pkg_config_dir 路径
    pkg_config_path = Path(pkg_config_dir)
    if not pkg_config_path.is_absolute():
        # 如果是相对路径，相对于当前脚本的目录
        pkg_config_path = Path(__file__).parent / pkg_config_dir
    
    # 加载基础配置
    base_path = Path(__file__).parent / "base.toml"
    with open(base_path, 'rb') as f:
        config = tomllib.load(f)
    
    # 确保 action_interfaces 存在
    if 'action_interfaces' not in config:
        config['action_interfaces'] = {}
    
    # 合并所有指定的包管理器配置
    for package in actmaps:
        package_path = pkg_config_path / f"{package}.toml"
        if not package_path.exists():
            raise click.ClickException(f"包管理器配置文件不存在: {package_path}")
        
        with open(package_path, 'rb') as f:
            package_config = tomllib.load(f)
        
        # 合并 actions
        for action, action_config in package_config.get('actions', {}).items():
            if action in config['actions']:
                config['actions'][action].update(action_config)
            else:
                config['actions'][action] = action_config
        
        # 合并 action_interfaces
        if 'action_interfaces' in package_config:
            config['action_interfaces'].update(package_config['action_interfaces'])
    
    # 设置默认目标（使用第一个包管理器）
    config['config'] = {
        'default_target_action': actmaps[0]
    }
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入输出文件
    with open(output_path, 'wb') as f:
        tomli_w.dump(config, f)
    
    click.echo(f"✅ 已生成配置文件: {output_path}")
    click.echo(f"   包含的包管理器: {', '.join(actmaps)}")
    click.echo(f"   默认目标包管理器: {actmaps[0]}")
    click.echo(f"   支持的动作: {len(config.get('actions', {}))} 个")
    click.echo(f"   支持的接口: {len(config.get('action_interfaces', {}))} 个")
    click.echo(f"   配置目录: {pkg_config_path}")


def get_available_packages(pkg_config_dir: str) -> list:
    """获取可用的包管理器列表"""
    pkg_config_path = Path(pkg_config_dir)
    
    if not pkg_config_path.exists():
        return []
    
    packages = []
    for f in pkg_config_path.glob("*.toml"):
        packages.append(f.stem)
    
    return sorted(packages)


if __name__ == '__main__':
    generate_config()