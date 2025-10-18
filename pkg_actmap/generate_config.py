#!/usr/bin/env python3
"""
Tool to generate complete configuration files
"""

import tomllib
import tomli_w
from pathlib import Path
import click
import shutil


@click.command()
@click.option('-o', '--output', required=False, help='Output configuration file path')
@click.option('--use-actmaps', help='Create or update configuration with specified package managers (comma separated)')
@click.option('--add-actmaps', help='Add package managers to existing configuration (comma separated)')
@click.option('--actmap-config', 'pkg_config_dir',
              default=str(Path.home() / '.config' / 'actmap' / 'actmap_config'),
              show_default='~/.config/actmap/actmap_config',
              help='Package manager configuration directory path')
@click.option('--list-actmaps', is_flag=True, help='List all available package managers')
@click.option('--init-config', is_flag=True, help='Initialize user configuration directory')
def generate_config(output, use_actmaps, add_actmaps, pkg_config_dir, list_actmaps, init_config):
    """Generate complete configuration with multiple package managers

    \b
    Examples:
        actmap-generate --use-actmaps pacman,apt,dnf        # Create configuration with multiple package managers
        actmap-generate --use-actmaps pacman,apt,brew,scoop,winget  # Create cross-platform configuration
        actmap-generate --add-actmaps brew,zypper           # Add package managers to existing configuration
        actmap-generate --list-actmaps                      # List available package managers
        actmap-generate --init-config                       # Initialize configuration directory
    """

    if init_config:
        init_user_config()
        return

    if list_actmaps:
        available_packages = get_available_packages(pkg_config_dir)
        print("📦 Available package managers:")
        for pkg in available_packages:
            print(f"  - {pkg}")
        return

    # If no output path specified, use default config path
    if not output:
        output = str(Path.home() / '.config' / 'actmap' / 'config.toml')

    # Parse package manager list
    actmaps_to_process = []
    operation = "create"  # Operation type: create or add

    if use_actmaps:
        actmaps_to_process = [pkg.strip() for pkg in use_actmaps.split(',') if pkg.strip()]
        operation = "create"
    elif add_actmaps:
        actmaps_to_process = [pkg.strip() for pkg in add_actmaps.split(',') if pkg.strip()]
        operation = "add"
    else:
        raise click.ClickException("Must specify --use-actmaps or --add-actmaps option")

    # Check if package managers are provided
    if not actmaps_to_process:
        raise click.ClickException("Must specify at least one package manager")

    # Validate package managers exist
    available_packages = get_available_packages(pkg_config_dir)
    invalid_packages = [pkg for pkg in actmaps_to_process if pkg not in available_packages]
    if invalid_packages:
        raise click.ClickException(f"Package manager does not exist: {', '.join(invalid_packages)}\nAvailable package managers: {', '.join(available_packages)}")

    output_path = Path(output)
    pkg_config_path = Path(pkg_config_dir)

    # Load base configuration
    base_path = Path(__file__).parent / "base.toml"
    with open(base_path, 'rb') as f:
        config = tomllib.load(f)

    # Ensure action_interfaces exists
    if 'action_interfaces' not in config:
        config['action_interfaces'] = {}

    # Record initial interface count
    initial_interface_count = len(config.get('action_interfaces', {}))

    # If add operation, load existing configuration first
    if operation == "add" and output_path.exists():
        try:
            with open(output_path, 'rb') as f:
                existing_config = tomllib.load(f)
                # Merge existing configuration
                config = existing_config
                initial_interface_count = len(config.get('action_interfaces', {}))
        except Exception as e:
            click.echo(f"⚠️  Cannot read existing configuration, will create new one: {e}")

    # Record actually added package managers (for deduplication)
    actually_added_packages = []

    # Merge all specified package manager configurations
    for package in actmaps_to_process:
        package_path = pkg_config_path / f"{package}.toml"
        if not package_path.exists():
            raise click.ClickException(f"Package manager configuration file does not exist: {package_path}")

        with open(package_path, 'rb') as f:
            package_config = tomllib.load(f)

        # Check if this package manager already exists
        package_interface_name = package  # Package manager name is usually the interface name
        if package_interface_name in config.get('action_interfaces', {}):
            if operation == "add":
                click.echo(f"⚠️  Package manager {package} already exists, skipping duplicate addition")
                continue
            else:
                # For create operation, overwrite existing configuration
                click.echo(f"🔄  Updating configuration for package manager {package}")

        # Merge actions
        for action, action_config in package_config.get('actions', {}).items():
            if action in config['actions']:
                # Only add new package manager's configuration, avoid overwriting existing
                for pkg_name, pkg_config in action_config.items():
                    if pkg_name not in config['actions'][action]:
                        config['actions'][action][pkg_name] = pkg_config
            else:
                config['actions'][action] = action_config

        # Merge action_interfaces
        if 'action_interfaces' in package_config:
            for iface_name, iface_config in package_config['action_interfaces'].items():
                if iface_name not in config['action_interfaces']:
                    config['action_interfaces'][iface_name] = iface_config
                elif operation == "create":
                    # For create operation, update existing interface configuration
                    config['action_interfaces'][iface_name] = iface_config

        actually_added_packages.append(package)

    # If no package managers actually added, show warning
    if not actually_added_packages and operation == "add":
        click.echo("⚠️  No new package managers added (all specified package managers already exist)")
        return

    # Set default target (use first package manager)
    if actually_added_packages:
        # For add operation, keep original default target
        if operation == "create":
            config['config'] = {
                'default_target_actmap': actually_added_packages[0]
            }
        elif operation == "add" and 'config' not in config:
            # If add operation and no default configuration, set first package manager as default
            config['config'] = {
                'default_target_actmap': actually_added_packages[0]
            }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output file
    with open(output_path, 'wb') as f:
        tomli_w.dump(config, f)

    # Calculate interface count change
    final_interface_count = len(config.get('action_interfaces', {}))
    interface_count_change = final_interface_count - initial_interface_count

    if operation == "create":
        click.echo(f"✅ Created configuration file: {output_path}")
    else:
        click.echo(f"✅ Updated configuration file: {output_path}")
        
    click.echo(f"   Included package managers: {', '.join(actually_added_packages)}")
    
    # Show default target
    default_target = config.get('config', {}).get('default_target_actmap', 'Not set')
    click.echo(f"   Default target package manager: {default_target}")
    
    click.echo(f"   Supported actions: {len(config.get('actions', {}))}")
    click.echo(f"   Supported interfaces: {final_interface_count}")
    
    if operation == "add" and interface_count_change > 0:
        click.echo(f"   New interfaces: {interface_count_change}")

def get_available_packages(pkg_config_dir: str) -> list:
    """Get available package manager list"""
    pkg_config_path = Path(pkg_config_dir)

    if not pkg_config_path.exists():
        return []

    packages = []
    for f in pkg_config_path.glob("*.toml"):
        packages.append(f.stem)

    return sorted(packages)


def init_user_config():
    """Initialize user configuration directory"""
    # Get XDG configuration directory
    xdg_config_home = Path.home() / '.config'
    actmap_config_dir = xdg_config_home / 'actmap'
    actmap_pkg_config_dir = actmap_config_dir / 'actmap_config'

    # Create directories
    actmap_config_dir.mkdir(parents=True, exist_ok=True)
    actmap_pkg_config_dir.mkdir(parents=True, exist_ok=True)

    # Source directories
    source_base = Path(__file__).parent / 'base.toml'
    source_config_dir = Path(__file__).parent / 'actmap_config'

    def backup_if_exists(file_path):
        """Create backup if file already exists"""
        if file_path.exists():
            backup_count = 1
            backup_path = file_path.with_suffix(f'{file_path.suffix}_{backup_count}')
            
            # Find available backup filename (avoid overwriting existing backups)
            while backup_path.exists():
                backup_count += 1
                backup_path = file_path.with_suffix(f'{file_path.suffix}_{backup_count}')
            
            shutil.copy2(file_path, backup_path)
            click.echo(f"📦 Backed up: {file_path.name} -> {backup_path.name}")
            return backup_path
        return None

    # Copy base.toml
    if source_base.exists():
        target_base = actmap_config_dir / 'base.toml'
        backup_if_exists(target_base)
        shutil.copy2(source_base, target_base)
        click.echo(f"✅ Copied: base.toml -> {target_base}")
    else:
        click.echo(f"❌ Source file does not exist: {source_base}")

    # Copy all package manager configurations
    if source_config_dir.exists():
        config_files = list(source_config_dir.glob("*.toml"))
        copied_count = 0
        
        for config_file in config_files:
            target_config = actmap_pkg_config_dir / config_file.name
            
            # Backup existing files
            backup_if_exists(target_config)
            
            shutil.copy2(config_file, target_config)
            click.echo(f"✅ Copied: {config_file.name} -> {actmap_pkg_config_dir / config_file.name}")
            copied_count += 1

        click.echo(f"📦 Copied {copied_count} package manager configurations")
    else:
        click.echo(f"❌ Source directory does not exist: {source_config_dir}")

    # Generate default configuration file
    default_config_path = actmap_config_dir / 'config.toml'
    try:
        # Backup existing configuration file
        backup_if_exists(default_config_path)
        
        # Generate default configuration with common package managers
        available_packages = get_available_packages(str(actmap_pkg_config_dir))

        # Select common package managers
        common_packages = [pkg for pkg in available_packages if pkg in ['pacman', 'apt', 'dnf']]
        if not common_packages and available_packages:
            common_packages = available_packages[:2]  # Take first two

        if common_packages:
            # Call generate_config logic to generate default configuration
            config = {}

            # Load base configuration
            with open(actmap_config_dir / 'base.toml', 'rb') as f:
                config = tomllib.load(f)

            # Merge all specified package manager configurations
            for package in common_packages:
                package_path = actmap_pkg_config_dir / f"{package}.toml"
                with open(package_path, 'rb') as f:
                    package_config = tomllib.load(f)

                # Merge actions
                for action, action_config in package_config.get('actions', {}).items():
                    if action in config['actions']:
                        config['actions'][action].update(action_config)
                    else:
                        config['actions'][action] = action_config

                # Merge action_interfaces
                if 'action_interfaces' in package_config:
                    config['action_interfaces'].update(package_config['action_interfaces'])

            # Set default target
            config['config'] = {
                'default_target_actmap': common_packages[0]
            }

            # Write default configuration file
            with open(default_config_path, 'wb') as f:
                tomli_w.dump(config, f)

            click.echo(f"✅ Generated default configuration file: {default_config_path}")
            click.echo(f"   Included package managers: {', '.join(common_packages)}")

    except Exception as e:
        click.echo(f"⚠️  Failed to generate default configuration file: {e}")

    click.echo("🎉 User configuration initialization completed!")
    click.echo(f"   Configuration directory: {actmap_config_dir}")
    click.echo(f"   Package manager configurations: {actmap_pkg_config_dir}")
    click.echo(f"   Default configuration file: {default_config_path}")
    
    # Show backup information
    click.echo(f"💾 Existing files have been automatically backed up (suffix _1, _2, etc.)")
    
    click.echo("")
    click.echo("Now you can directly use:")
    click.echo("  actmap map apt install vim")
    click.echo("  actmap-execute map apt search python")
    click.echo("")
    click.echo("📦 Available package managers:")
    click.echo("  Use 'actmap-generate --list-actmaps' to view complete list")
    
    click.echo("\n🎯 Next steps:")
    click.echo("  1. View available package managers: actmap-generate --list-actmaps")
    click.echo("  2. Create complete configuration: actmap-generate --use-actmaps pacman,apt,dnf,brew,zypper,scoop,winget,chocolatey")
    click.echo("  3. Add specific package managers: actmap-generate --add-actmaps brew,scoop,winget")
    click.echo("  4. Test command mapping: actmap map apt install vim")
    click.echo("  5. Direct command execution: actmap-execute -i map pacman -S git")


if __name__ == '__main__':
    generate_config()