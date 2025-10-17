#!/usr/bin/env python3
"""
生成完整配置文件的工具
"""

import tomllib
import tomli_w
from pathlib import Path
import click
import shutil


@click.command()
@click.option('-o', '--output', required=False, help='输出配置文件路径')
@click.option('-m', '--actmap', 'actmaps', multiple=True,
              help='要包含的包管理器名称（可多次使用）')
@click.option('--actmap-config', 'pkg_config_dir',
              default=str(Path.home() / '.config' / 'actmap' / 'actmap_config'),
              show_default='~/.config/actmap/actmap_config',
              help='包管理器配置目录路径')
@click.option('--list-actmaps', is_flag=True, help='列出所有可用的包管理器')
@click.option('--init-config', is_flag=True, help='初始化用户配置目录')
def generate_config(output, actmaps, pkg_config_dir, list_actmaps, init_config):
    """生成包含多个包管理器的完整配置

    \b
    示例:
        actmap-generate -o config.toml -m pacman -m apt
        actmap-generate -o my_config.toml -m pacman -m apt -m dnf
        actmap-generate --actmap-config /custom/path -o config.toml -m pacman
        actmap-generate --list-actmaps
        actmap-generate --init-config
    """

    if init_config:
        init_user_config()
        return

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
    pkg_config_path = Path(pkg_config_dir)

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


def init_user_config():
    """初始化用户配置目录"""
    # 获取 XDG 配置目录
    xdg_config_home = Path.home() / '.config'
    actmap_config_dir = xdg_config_home / 'actmap'
    actmap_pkg_config_dir = actmap_config_dir / 'actmap_config'

    # 创建目录
    actmap_config_dir.mkdir(parents=True, exist_ok=True)
    actmap_pkg_config_dir.mkdir(parents=True, exist_ok=True)

    # 源目录
    source_base = Path(__file__).parent / 'base.toml'
    source_config_dir = Path(__file__).parent / 'actmap_config'

    # 复制 base.toml
    if source_base.exists():
        shutil.copy2(source_base, actmap_config_dir / 'base.toml')
        click.echo(f"✅ 已复制: base.toml -> {actmap_config_dir / 'base.toml'}")
    else:
        click.echo(f"❌ 源文件不存在: {source_base}")

    # 复制所有包管理器配置
    if source_config_dir.exists():
        config_files = list(source_config_dir.glob("*.toml"))
        for config_file in config_files:
            shutil.copy2(config_file, actmap_pkg_config_dir / config_file.name)
            click.echo(f"✅ 已复制: {config_file.name} -> {actmap_pkg_config_dir / config_file.name}")

        click.echo(f"📦 共复制了 {len(config_files)} 个包管理器配置")
    else:
        click.echo(f"❌ 源目录不存在: {source_config_dir}")

    # 生成默认配置文件
    default_config_path = actmap_config_dir / 'config.toml'
    try:
        # 生成包含常用包管理器的默认配置
        from .generate_config import get_available_packages
        available_packages = get_available_packages(str(actmap_pkg_config_dir))

        # 选择常用的包管理器
        common_packages = [pkg for pkg in available_packages if pkg in ['pacman', 'apt', 'dnf']]
        if not common_packages and available_packages:
            common_packages = available_packages[:2]  # 取前两个

        if common_packages:
            # 调用 generate_config 逻辑生成默认配置
            config = {}

            # 加载基础配置
            with open(actmap_config_dir / 'base.toml', 'rb') as f:
                config = tomllib.load(f)

            # 合并所有指定的包管理器配置
            for package in common_packages:
                package_path = actmap_pkg_config_dir / f"{package}.toml"
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

            # 设置默认目标
            config['config'] = {
                'default_target_action': common_packages[0]
            }

            # 写入默认配置文件
            with open(default_config_path, 'wb') as f:
                tomli_w.dump(config, f)

            click.echo(f"✅ 已生成默认配置文件: {default_config_path}")
            click.echo(f"   包含的包管理器: {', '.join(common_packages)}")

    except Exception as e:
        click.echo(f"⚠️  生成默认配置文件失败: {e}")

    click.echo(f"🎉 用户配置初始化完成！")
    click.echo(f"   配置目录: {actmap_config_dir}")
    click.echo(f"   包管理器配置: {actmap_pkg_config_dir}")
    click.echo(f"   默认配置文件: {default_config_path}")
    click.echo("")
    click.echo("现在你可以直接使用:")
    click.echo("  actmap map -- apt install vim")
    click.echo("  actmap-execute -- apt search python")
    click.echo("")
    click.echo("\n📦 可用包管理器:")
    click.echo("  使用 'actmap-generate --list-actmaps' 查看完整列表")
    
    click.echo("\n🎯 下一步操作:")
    click.echo("  1. 查看可用包管理器: actmap-generate --list-actmaps")
    click.echo("  2. 添加更多包管理器: actmap-generate -o custom.toml -m apt -m pacman -m brew")
    click.echo("  3. 测试命令映射: actmap map -- apt install vim")
    click.echo("  4. 直接执行命令: actmap-execute -y -- pacman -S git")
    
    click.echo("\n💡 示例:")
    click.echo("  # 查看所有包管理器")
    click.echo("  actmap-generate --list-actmaps")
    click.echo("  # 创建自定义配置")
    click.echo("  actmap-generate -o my.toml -m apt -m pacman -m brew")
    click.echo("  # 使用自定义配置")
    click.echo("  actmap map --config my.toml -- apt update")


if __name__ == '__main__':
    generate_config()
