#!/usr/bin/env python3
"""
Execute mapped commands
"""

import click
import subprocess
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from actmap.core.actmap import ActMap
from actmap.log import (
    set_debug, debug, info, success, error, warning,
    progress, step, debug_plain, fatal
)

def get_available_actions(ctx, param, incomplete):
    """Get available action list for completion"""
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
        default_target = config.get('config', {}).get('default_target_actmap', 'pacman')
        completions = []
        
        for action_name, action_config in actions_config.items():
            if incomplete not in action_name:
                continue
                
            # Get action description
            description = action_config.get('description', 'Action')
            
            # Get command format for default target
            target_config = action_config.get(default_target, {})
            cmd_format = target_config.get('cmd_format', '')
            
            # Build help information
            if cmd_format:
                help_text = f"{description} | {cmd_format}"
            else:
                help_text = f"{description} | No {default_target} command format"
            
            # Create completion item
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
    """Get available package manager interface list for completion"""
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
                
            # Get number of actions supported by this interface
            action_count = 0
            for action_name, action_config in config.get('actions', {}).items():
                if interface in action_config:
                    action_count += 1
            
            # Add description for each package manager
            descriptions = {
                'pacman': 'Arch Linux package manager',
                'apt': 'Debian/Ubuntu package manager', 
                'dnf': 'Fedora package manager',
                'brew': 'macOS package manager',
                'zypper': 'openSUSE package manager',
                'chocolatey': 'Windows package manager',
                'scoop': 'Windows package manager',
                'winget': 'Windows package manager'
            }
            
            description = descriptions.get(interface, 'Package manager')
            help_text = f"{description} | Supports {action_count} actions"
            
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
    """Determine if confirmation is needed for execution"""
    # Force mode: execute directly
    if force:
        return False

    # Interactive mode: always confirm
    if interactive:
        return True

    # Safe operations: execute directly
    safe_actions = ['search', 'info', 'help', 'list_installed']
    if action in safe_actions:
        return False

    # Other operations: need confirmation
    return True

def _confirm_execution(command: str) -> bool:
    """Confirm whether to execute command"""
    click.echo(f"⚠️  About to execute: {command}")
    
    try:
        response = input("Confirm execution? [y/N]: ").strip().lower()
        return response == 'y'
    except KeyboardInterrupt:
        click.echo("\nExecution cancelled")
        return False

@click.group(invoke_without_command=True)
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='Show debug information')
@click.option('-t', '--target', help='Target package manager', shell_complete=get_available_interfaces)
@click.option('--config', help='Configuration file path')
@click.option('-i', '--interactive', is_flag=True, help='Interactive mode, confirm before execution')
@click.option('-f', '--force', is_flag=True, help='Force mode, execute without confirmation')
@click.pass_context
def execute(ctx, debug_mode, target, config, interactive, force):
    """Execute mapped commands"""
    # Ensure subcommands can access these options
    ctx.ensure_object(dict)
    ctx.obj['debug_mode'] = debug_mode
    ctx.obj['target'] = target
    ctx.obj['config'] = config
    ctx.obj['interactive'] = interactive
    ctx.obj['force'] = force

    # If no subcommand, show help
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())

@execute.command()
@click.argument('action_name', shell_complete=get_available_actions)
@click.argument('params', nargs=-1)
@click.pass_context
def act(ctx, action_name, params):
    """Directly execute specified action
    
    \b
    Examples:
        actmap-execute act install vim git              # Install packages
        actmap-execute act search python == editor      # Search packages (use == to separate parameters)
        actmap-execute act update                       # Update database  
        actmap-execute act list_installed               # List installed packages
    """
    # Get options from context
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    interactive = ctx.obj.get('interactive', False)
    force = ctx.obj.get('force', False)
    
    set_debug(debug_mode)
    
    debug("🚀 Starting direct action execution")
    debug(f"Action name: {action_name}")
    debug(f"Parameters: {params}")
    debug(f"Target package manager: {target}")
    debug(f"Configuration file: {config}")
    debug(f"Interactive mode: {interactive}")
    debug(f"Force mode: {force}")
    
    try:
        # Use ActMap to execute action
        if config:
            config_path = Path(config)
        else:
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)
        
        # Set target package manager
        if target:
            target_interface = target.lower()
        else:
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_actmap', 'pacman')
        
        # Check if action is supported
        supported_actions = actmap.get_supported_actions()
        if action_name not in supported_actions:
            error(f"Unsupported action: {action_name}")
            error(f"Supported actions: {', '.join(supported_actions)}")
            fatal("Please use supported action names")
        
        # Build parse result
        parse_result = {
            'parsed_kwargs': {},
            'present_params': {},
            'detected_command': None
        }
        
        # Process parameters based on action type
        action_config = actmap.config.get('actions', {}).get(action_name, {})
        action_args = action_config.get('args', [])
        
        if debug_mode:
            debug(f"Action parameter definitions: {action_args}")
        
        # Parameter parsing logic: assign in order, switch to next parameter when encountering ==
        remaining_params = list(params)
        parse_result['parsed_kwargs'] = {}
        
        for i, arg_name in enumerate(action_args):
            current_arg_values = []
            
            # Take from remaining parameters until encountering == or no more parameters
            while remaining_params:
                param = remaining_params[0]
                if param == '==':
                    # Encountered separator, remove it and switch to next parameter
                    remaining_params.pop(0)
                    break
                else:
                    # Normal parameter, add to current parameter value
                    current_arg_values.append(remaining_params.pop(0))
            
            parse_result['parsed_kwargs'][arg_name] = current_arg_values
        
        if debug_mode:
            debug(f"Parameter parsing result: {parse_result['parsed_kwargs']}")
            debug(f"Remaining unprocessed parameters: {remaining_params}")
        
        # Check if all required parameters have values
        missing_args = []
        for arg_name in action_args:
            if not parse_result['parsed_kwargs'][arg_name]:
                missing_args.append(arg_name)
        
        if missing_args:
            error(f"Missing required parameters: {', '.join(missing_args)}")
            error(f"Usage: actmap-execute act {action_name} [parameter1] == [parameter2] == ...")
            fatal("Please provide all required parameters")
        
        # If there are remaining parameters and no more configuration parameters, warn user
        if remaining_params and debug_mode:
            warning(f"Unused parameters: {remaining_params}")
        
        # Execute mapping
        mapped_command = actmap.map_command_direct(action_name, target_interface, parse_result)
        
        if mapped_command:
            info(f"Mapped command: {mapped_command}")
            
            # Determine if confirmation is needed
            need_confirmation = _need_confirmation(action_name, interactive, force)
            
            if need_confirmation:
                if not _confirm_execution(mapped_command):
                    info("Execution cancelled by user")
                    return
            
            # Execute command
            step("Executing command...")
            try:
                result = subprocess.run(mapped_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)
            except KeyboardInterrupt:
                sys.exit(130)
        else:
            error("Cannot map command")
            fatal("Mapping failed")
        
    except Exception as e:
        error(f"Action execution failed: {e}")
        if debug_mode:
            import traceback
            debug_plain("Stack trace:")
            debug_plain(traceback.format_exc())
        fatal("Program exited abnormally")

def get_available_package_managers(ctx, param, incomplete):
    """Get available package manager list for completion"""
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
                
            # Add description for each package manager
            descriptions = {
                'pacman': 'Arch Linux package manager',
                'apt': 'Debian/Ubuntu package manager', 
                'dnf': 'Fedora package manager',
                'brew': 'macOS package manager',
                'zypper': 'openSUSE package manager',
                'chocolatey': 'Windows package manager',
                'scoop': 'Windows package manager',
                'winget': 'Windows package manager'
            }
            
            description = descriptions.get(interface, 'Package manager')
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
    """Get command completion suggestions"""
    from click.shell_completion import CompletionItem
    try:
        comp_env = os.environ.get('_ACTMAP_EXECUTE_COMPLETE', '')
        if not comp_env.endswith('_complete'):
            return []

        # Get already entered parameters
        params = ctx.params.copy()
        command_parts = params.get('command', [])
        
        # If no package manager name entered yet, provide package manager completion
        if not command_parts:
            return get_available_package_managers(ctx, param, incomplete)
        
        # Already entered package manager name, provide command completion for that package manager
        package_manager = command_parts[0]
        
        import tomllib
        config_path = Path.home() / '.config' / 'actmap' / 'config.toml'
        if not config_path.exists():
            return []

        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        # Get commands supported by this package manager
        interface_config = config.get('action_interfaces', {}).get(package_manager, {})
        args_config = interface_config.get('args', {})
        
        completions = []
        
        # Find commands supported by this package manager
        for cmd_key, cmd_config in args_config.items():
            if cmd_key.endswith('_command'):
                cmd_name = cmd_config.get('cmd_name')
                if cmd_name and incomplete in cmd_name:
                    # Get command description
                    description = f"{package_manager} command"
                    
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
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def map(ctx, command):
    """Execute mapped commands

    \b
    Examples:
        actmap-execute map apt install vim git
        actmap-execute -i map pacman -Syu
        actmap-execute -f map apt remove vim
        actmap-execute -t apt map pacman -S vim
    """
    # Get options from context
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    interactive = ctx.obj.get('interactive', False)
    force = ctx.obj.get('force', False)
    
    # Set debug mode
    set_debug(debug_mode)

    debug("🚀 Starting command mapping")
    debug(f"Received arguments: {command}")
    debug(f"Debug mode: {debug_mode}")
    debug(f"Target package manager: {target}")
    debug(f"Configuration file: {config}")
    debug(f"Interactive mode: {interactive}")
    debug(f"Force mode: {force}")

    try:
        # Main business logic
        if not command:
            error("No command provided for mapping")
            fatal("Command arguments are empty")

        cmd_str = ' '.join(command)
        cmd_parts = list(command)

        info(f"Processing command: {cmd_str}")

        # Use ActMap for actual mapping - default to XDG config
        if config:
            config_path = Path(config)
        else:
            # Default to XDG config directory
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)

        # Auto-detect source package manager
        source_interface = actmap.detect_source_interface(cmd_parts)
        if not source_interface:
            error("Cannot auto-detect source package manager")
            fatal("Please ensure command format is correct, e.g.: apt install vim or pacman -S vim")

        # Use full arguments for parsing
        args_to_parse = cmd_parts

        # Set target package manager
        if target:
            target_interface = target.lower()
        else:
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_actmap', 'pacman')

        # Check if target package manager is defined in config file
        available_interfaces = list(actmap.config.get('action_interfaces', {}).keys())
        if target_interface not in available_interfaces:
            error(f"Target package manager '{target_interface}' not defined in configuration file")
            error(f"Package managers defined in config: {', '.join(available_interfaces)}")
            fatal("Please use package managers defined in configuration file")

        if debug_mode:
            progress("Parsing command...")
            debug(f"Source package manager: {source_interface}")
            debug(f"Target package manager: {target_interface}")
            debug("Command tokens:", cmd_parts)
            debug("Parsing arguments:", args_to_parse)
            step("Looking for mapping rules...")

        # Parse arguments
        parse_result = actmap.parse_arguments(source_interface, args_to_parse)

        # Detect action
        action = actmap.detect_action(source_interface, parse_result)

        if debug_mode:
            if action:
                success(f"Found {action} operation")
            else:
                warning("No matching operation found")

        # Execute mapping
        if debug_mode:
            step("Executing command mapping...")

        mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)

        if not mapped_command:
            error("Cannot map command")
            fatal("Mapping failed")

        info(f"Mapped command: {mapped_command}")

        # Determine if confirmation is needed
        need_confirmation = _need_confirmation(action, interactive, force)

        if need_confirmation:
            if not _confirm_execution(mapped_command):
                info("Execution cancelled by user")
                return

        # Execute command
        step("Executing command...")
        try:
            result = subprocess.run(mapped_command, shell=True, check=True)
            success("Command executed successfully")
        except subprocess.CalledProcessError as e:
            error(f"Command execution failed, exit code: {e.returncode}")
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            error("Command interrupted by user")
            sys.exit(130)

    except Exception as e:
        error(f"Command execution failed: {e}")
        debug("Detailed error information:", str(e))
        if debug_mode:
            import traceback
            debug_plain("Stack trace:")
            debug_plain(traceback.format_exc())
        fatal("Program exited abnormally")

if __name__ == '__main__':
    execute()