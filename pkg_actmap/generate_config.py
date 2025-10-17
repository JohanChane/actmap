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
@click.option('--use-actmaps', help='使用指定的包管理器创建或更新配置（逗号分隔）')
@click.option('--add-actmaps', help='添加包管理器到现有配置（逗号分隔）')
@click.option('--actmap-config', 'pkg_config_dir',
              default=str(Path.home() / '.config' / 'actmap' / 'actmap_config'),
              show_default='~/.config/actmap/actmap_config',
              help='包管理器配置目录路径')
@click.option('--list-actmaps', is_flag=True, help='列出所有可用的包管理器')
@click.option('--init-config', is_flag=True, help='初始化用户配置目录')
def generate_config(output, use_actmaps, add_actmaps, pkg_config_dir, list_actmaps, init_config):
    """生成包含多个包管理器的完整配置

    \b
    示例:
        actmap-generate --use-actmaps pacman,apt,dnf        # 创建包含多个包管理器的配置
        actmap-generate --use-actmaps pacman,apt,brew,scoop,winget  # 创建跨平台配置
        actmap-generate --add-actmaps brew,zypper           # 添加包管理器到现有配置
        actmap-generate --list-actmaps                      # 列出可用包管理器
        actmap-generate --init-config                       # 初始化配置目录
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

    # 如果没有指定输出路径，使用默认配置路径
    if not output:
        output = str(Path.home() / '.config' / 'actmap' / 'config.toml')

    # 解析包管理器列表
    actmaps_to_process = []
    operation = "create"  # 操作类型: create 或 add

    if use_actmaps:
        actmaps_to_process = [pkg.strip() for pkg in use_actmaps.split(',') if pkg.strip()]
        operation = "create"
    elif add_actmaps:
        actmaps_to_process = [pkg.strip() for pkg in add_actmaps.split(',') if pkg.strip()]
        operation = "add"
    else:
        raise click.ClickException("必须指定 --use-actmaps 或 --add-actmaps 选项")

    # 检查是否提供了包管理器
    if not actmaps_to_process:
        raise click.ClickException("必须指定至少一个包管理器")

    # 验证包管理器是否存在
    available_packages = get_available_packages(pkg_config_dir)
    invalid_packages = [pkg for pkg in actmaps_to_process if pkg not in available_packages]
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

    # 记录初始的接口数量
    initial_interface_count = len(config.get('action_interfaces', {}))

    # 如果是添加操作，先加载现有配置
    if operation == "add" and output_path.exists():
        try:
            with open(output_path, 'rb') as f:
                existing_config = tomllib.load(f)
                # 合并现有配置
                config = existing_config
                initial_interface_count = len(config.get('action_interfaces', {}))
        except Exception as e:
            click.echo(f"⚠️  无法读取现有配置，将创建新配置: {e}")

    # 记录实际添加的包管理器（用于去重）
    actually_added_packages = []

    # 合并所有指定的包管理器配置
    for package in actmaps_to_process:
        package_path = pkg_config_path / f"{package}.toml"
        if not package_path.exists():
            raise click.ClickException(f"包管理器配置文件不存在: {package_path}")

        with open(package_path, 'rb') as f:
            package_config = tomllib.load(f)

        # 检查这个包管理器是否已经存在
        package_interface_name = package  # 包管理器名称通常就是接口名称
        if package_interface_name in config.get('action_interfaces', {}):
            if operation == "add":
                click.echo(f"⚠️  包管理器 {package} 已存在，跳过重复添加")
                continue
            else:
                # 对于创建操作，覆盖现有配置
                click.echo(f"🔄  更新包管理器 {package} 的配置")

        # 合并 actions
        for action, action_config in package_config.get('actions', {}).items():
            if action in config['actions']:
                # 只添加新包管理器的配置，避免覆盖现有配置
                for pkg_name, pkg_config in action_config.items():
                    if pkg_name not in config['actions'][action]:
                        config['actions'][action][pkg_name] = pkg_config
            else:
                config['actions'][action] = action_config

        # 合并 action_interfaces
        if 'action_interfaces' in package_config:
            for iface_name, iface_config in package_config['action_interfaces'].items():
                if iface_name not in config['action_interfaces']:
                    config['action_interfaces'][iface_name] = iface_config
                elif operation == "create":
                    # 对于创建操作，更新现有接口配置
                    config['action_interfaces'][iface_name] = iface_config

        actually_added_packages.append(package)

    # 如果没有实际添加任何包管理器，显示警告
    if not actually_added_packages and operation == "add":
        click.echo("⚠️  没有添加新的包管理器（所有指定的包管理器都已存在）")
        return

    # 设置默认目标（使用第一个包管理器）
    if actually_added_packages:
        # 对于添加操作，保持原有的默认目标
        if operation == "create":
            config['config'] = {
                'default_target_action': actually_added_packages[0]
            }
        elif operation == "add" and 'config' not in config:
            # 如果添加操作且没有默认配置，设置第一个包管理器为默认
            config['config'] = {
                'default_target_action': actually_added_packages[0]
            }

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入输出文件
    with open(output_path, 'wb') as f:
        tomli_w.dump(config, f)

    # 计算接口数量变化
    final_interface_count = len(config.get('action_interfaces', {}))
    interface_count_change = final_interface_count - initial_interface_count

    if operation == "create":
        click.echo(f"✅ 已创建配置文件: {output_path}")
    else:
        click.echo(f"✅ 已更新配置文件: {output_path}")
        
    click.echo(f"   包含的包管理器: {', '.join(actually_added_packages)}")
    
    # 显示默认目标
    default_target = config.get('config', {}).get('default_target_action', '未设置')
    click.echo(f"   默认目标包管理器: {default_target}")
    
    click.echo(f"   支持的动作: {len(config.get('actions', {}))} 个")
    click.echo(f"   支持的接口: {final_interface_count} 个")
    
    if operation == "add" and interface_count_change > 0:
        click.echo(f"   新增接口: {interface_count_change} 个")

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

    def backup_if_exists(file_path):
        """如果文件已存在，则创建备份"""
        if file_path.exists():
            backup_count = 1
            backup_path = file_path.with_suffix(f'{file_path.suffix}_{backup_count}')
            
            # 找到可用的备份文件名（避免覆盖现有备份）
            while backup_path.exists():
                backup_count += 1
                backup_path = file_path.with_suffix(f'{file_path.suffix}_{backup_count}')
            
            shutil.copy2(file_path, backup_path)
            click.echo(f"📦 已备份: {file_path.name} -> {backup_path.name}")
            return backup_path
        return None

    # 复制 base.toml
    if source_base.exists():
        target_base = actmap_config_dir / 'base.toml'
        backup_if_exists(target_base)
        shutil.copy2(source_base, target_base)
        click.echo(f"✅ 已复制: base.toml -> {target_base}")
    else:
        click.echo(f"❌ 源文件不存在: {source_base}")

    # 复制所有包管理器配置
    if source_config_dir.exists():
        config_files = list(source_config_dir.glob("*.toml"))
        copied_count = 0
        
        for config_file in config_files:
            target_config = actmap_pkg_config_dir / config_file.name
            
            # 备份已存在的文件
            backup_if_exists(target_config)
            
            shutil.copy2(config_file, target_config)
            click.echo(f"✅ 已复制: {config_file.name} -> {actmap_pkg_config_dir / config_file.name}")
            copied_count += 1

        click.echo(f"📦 共复制了 {copied_count} 个包管理器配置")
    else:
        click.echo(f"❌ 源目录不存在: {source_config_dir}")

    # 生成默认配置文件
    default_config_path = actmap_config_dir / 'config.toml'
    try:
        # 备份已存在的配置文件
        backup_if_exists(default_config_path)
        
        # 生成包含常用包管理器的默认配置
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

    click.echo("🎉 用户配置初始化完成！")
    click.echo(f"   配置目录: {actmap_config_dir}")
    click.echo(f"   包管理器配置: {actmap_pkg_config_dir}")
    click.echo(f"   默认配置文件: {default_config_path}")
    
    # 显示备份信息
    click.echo(f"💾 已存在的文件已自动备份（后缀为 _1, _2 等）")
    
    click.echo("")
    click.echo("现在你可以直接使用:")
    click.echo("  actmap map -- apt install vim")
    click.echo("  actmap-execute -- apt search python")
    click.echo("")
    click.echo("📦 可用包管理器:")
    click.echo("  使用 'actmap-generate --list-actmaps' 查看完整列表")
    
    click.echo("\n🎯 下一步操作:")
    click.echo("  1. 查看可用包管理器: actmap-generate --list-actmaps")
    click.echo("  2. 创建完整配置: actmap-generate --use-actmaps pacman,apt,dnf,brew,zypper,scoop,winget,chocolatey")
    click.echo("  3. 添加特定包管理器: actmap-generate --add-actmaps brew,scoop,winget")
    click.echo("  4. 测试命令映射: actmap map -- apt install vim")
    click.echo("  5. 直接执行命令: actmap-execute -i -- pacman -S git")


if __name__ == '__main__':
    generate_config()
