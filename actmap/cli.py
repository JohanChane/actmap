#!/usr/bin/env python3
"""
Command line interface module
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
    """Fully self-contained completion function - show complete command format"""
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


def _output_actmap_mappings(source_interface, target_interface, config_path, debug_mode):
    """Output configured mapping relationships"""
    try:
        # Use ActMap to load configuration
        if config_path:
            config_path = Path(config_path)
        else:
            # Default to XDG config directory
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        
        # Get supported actions
        actions = actmap.get_supported_actions()
        
        info(f"📋 Mapping configuration: {source_interface} → {target_interface}")
        print("=" * 80)
        
        # Table header
        print(f"{'Status':<4} {'Action':<15} {'Source Command':<25} {'Target Command':<30}")
        print("-" * 80)
        
        supported_count = 0
        
        for action in actions:
            # Check if source interface supports this action
            action_config = actmap.config.get('actions', {}).get(action, {})
            source_supported = source_interface in action_config
            target_supported = target_interface in action_config
            
            # Get source command format
            if source_supported:
                source_cmd = action_config.get(source_interface, {}).get('cmd_format', 'Not supported')
            else:
                source_cmd = "Not supported"
            
            # Get target command format
            if target_supported:
                target_cmd = action_config.get(target_interface, {}).get('cmd_format', 'Not supported')
                status = "✅"
                supported_count += 1
            else:
                target_cmd = "Not supported"
                status = "❌"
            
            print(f"{status:<4} {action:<15} {source_cmd:<25} {target_cmd:<30}")
            
            # If in debug mode, show trigger rules
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
                                print(f"   Trigger condition: {param_names}")
        
        print("=" * 80)
        success(f"Found {supported_count}/{len(actions)} supported mappings")
        
    except Exception as e:
        error(f"Failed to output mapping configuration: {e}")
        if debug_mode:
            import traceback
            debug_plain("Stack trace:")
            debug_plain(traceback.format_exc())

def get_source_interfaces(ctx, param, incomplete):
    """Get available source package manager interface list"""
    return get_available_interfaces(ctx, param, incomplete)

def get_target_interfaces(ctx, param, incomplete):
    """Get available target package manager interface list"""
    return get_available_interfaces(ctx, param, incomplete)

@click.group(invoke_without_command=True)
@click.option('-d', '--debug', 'debug_mode', is_flag=True, help='Show debug information')
@click.option('-t', '--target', help='Target package manager', shell_complete=get_target_interfaces)
@click.option('-s', '--source', help='Source package manager (use when auto-detection is ambiguous)', shell_complete=get_source_interfaces)
@click.option('--config', help='Configuration file path')
@click.option('--output-actmap', nargs=2, help='Output mapping configuration, e.g.: --output-actmap pacman apt')
@click.option('--list-actmaps', is_flag=True, help='Show available package managers in current config')
@click.pass_context
def cli(ctx, debug_mode, target, config, source, output_actmap, list_actmaps):
    """ActMap - Intelligent Command Mapping Tool
    
    Map commands from one package manager to another.
    
    \b
    Examples:
        actmap --output-actmap pacman apt        # Output mapping configuration
        actmap --list-actmaps                    # Show available package managers
        actmap map apt install vim git        # Map command
        actmap map apt install vim git           # Short form
        actmap -t apt --debug map pacman -Syu # Specify target and debug
    """
    # Ensure subcommands can access these options
    ctx.ensure_object(dict)
    ctx.obj['debug_mode'] = debug_mode
    ctx.obj['target'] = target
    ctx.obj['config'] = config
    
    # Handle --list-actmaps option
    if list_actmaps and not ctx.invoked_subcommand:
        _list_actmaps_in_config(config, debug_mode)
        return
    
    # Handle --output-actmap option (if no subcommand)
    if output_actmap and not ctx.invoked_subcommand:
        source_interface, target_interface = output_actmap
        _output_actmap_mappings(source_interface, target_interface, config, debug_mode)
        return
    
    # If no subcommand and no options, show help
    if not ctx.invoked_subcommand and not any([output_actmap, list_actmaps]):
        click.echo(ctx.get_help())


def get_available_interfaces(ctx, param, incomplete):
    """Get available package manager interface list for completion"""
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
    """Map command from source package manager to target package manager

    \b
    Examples:
        actmap map apt install vim git
        actmap -t apt map pacman -S vim
        actmap map pacman -Si neovim
    """

    # Get options from context
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    source = ctx.obj.get('source')
    
    # Set debug mode
    set_debug(debug_mode)
    
    debug("🚀 Starting command mapping")
    debug(f"Received arguments: {command}")
    debug(f"Debug mode: {debug_mode}")
    debug(f"Target package manager: {target}")
    debug(f"Source package manager: {source}")
    debug(f"Configuration file: {config}")
    
    try:
        # Main business logic
        if not command:
            error("No command provided for mapping")
            fatal("Command arguments are empty")
        
        cmd_str = ' '.join(command)
        cmd_parts = list(command)
        
        if debug_mode:
            info(f"Processing command: {cmd_str}")
        
        # Use ActMap for actual mapping
        if config:
            config_path = Path(config)
        else:
            # Default to XDG config directory
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        actmap.set_debug(debug_mode)
        
        # Detect source package manager: prioritize user-specified source
        if source:
            source_interface = source
            if debug_mode:
                progress(f"Using user-specified source package manager: {source_interface}")
        else:
            source_interface = actmap.detect_source_interface(cmd_parts)
            if not source_interface:
                fatal("Cannot auto-detect source package manager, please use -s/--source option to specify explicitly")
        
        # Use full arguments for parsing
        args_to_parse = cmd_parts

        if debug_mode:
            debug(f"Full parsing arguments: {args_to_parse}")
        
        # Set target package manager
        if target:
            target_interface = target.lower()
        else:
            # Read default target from configuration file
            config_data = actmap.config
            target_interface = config_data.get('config', {}).get('default_target_actmap', 'pacman')
        
        available_interfaces = actmap.get_supported_interfaces()
        if target_interface not in available_interfaces:
            error(f"Unsupported target package manager: {target_interface}")
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
                info("Executing normal command")
        
        # Execute mapping
        if debug_mode:
            step("Executing command mapping...")
        
        mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)
        
        if mapped_command:
            # Only output the mapped command
            print(mapped_command)
            if debug_mode:
                success("Operation executed successfully")
        else:
            if debug_mode:
                error("Cannot map command")
                fatal("Mapping failed")
            else:
                # In non-debug mode, if mapping fails, exit silently
                return
        
    except Exception as e:
        error(f"Command mapping failed: {e}")
        debug("Detailed error information:", str(e))
        if debug_mode:
            import traceback
            debug_plain("Stack trace:")
            debug_plain(traceback.format_exc())
        fatal("Program exited abnormally")


def _list_actmaps_in_config(config_path, debug_mode):
    """Show available package managers in current configuration file"""
    try:
        # Use ActMap to load configuration
        if config_path:
            config_path = Path(config_path)
        else:
            # Default to XDG config directory
            xdg_config_home = Path.home() / '.config' / 'actmap' / 'config.toml'
            config_path = xdg_config_home

        actmap = ActMap(config_path)
        
        # Get package managers defined in config file
        action_interfaces = actmap.config.get('action_interfaces', {})
        available_actmaps = list(action_interfaces.keys())
        
        if not available_actmaps:
            info("No package managers defined in current configuration file")
            return
        
        info("📦 Package managers in current configuration:")
        for actmap_name in sorted(available_actmaps):
            # Check if there are corresponding action definitions
            actions_with_this_actmap = []
            for action_name, action_config in actmap.config.get('actions', {}).items():
                if actmap_name in action_config:
                    actions_with_this_actmap.append(action_name)
            
            if actions_with_this_actmap:
                print(f"  ✅ {actmap_name} - supports {len(actions_with_this_actmap)} actions")
            else:
                print(f"  ⚠️  {actmap_name} - no action definitions")
        
        # Show default target
        default_target = actmap.config.get('config', {}).get('default_target_actmap')
        if default_target:
            print(f"\n🎯 Default target package manager: {default_target}")
        
        print(f"\n💡 Use 'actmap --output-actmap <source> <target>' to view specific mappings")
        
    except Exception as e:
        error(f"Failed to read configuration file: {e}")
        if debug_mode:
            import traceback
            debug_plain("Stack trace:")
            debug_plain(traceback.format_exc())

@click.command()
@click.argument('action_name', shell_complete=get_available_actions)
@click.argument('params', nargs=-1)
@click.pass_context
def act(ctx, action_name, params):
    """Map commands based on specified action
    
    \b
    Examples:
        actmap act install vim git              # Install packages
        actmap act search python == editor      # Search packages (use == to separate parameters)
        actmap act update                       # Update database  
        actmap act list_installed               # List installed packages
    """
    # Existing act function implementation remains unchanged
    debug_mode = ctx.obj.get('debug_mode', False)
    target = ctx.obj.get('target')
    config = ctx.obj.get('config')
    
    set_debug(debug_mode)
    
    debug("🚀 Starting direct action execution")
    debug(f"Action name: {action_name}")
    debug(f"Parameters: {params}")
    debug(f"Target package manager: {target}")
    debug(f"Configuration file: {config}")
        
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
            error(f"Usage: actmap act {action_name} [parameter1] == [parameter2] == ...")
            fatal("Please provide all required parameters")
        
        # If there are remaining parameters and no more configuration parameters, warn user
        if remaining_params and debug_mode:
            warning(f"Unused parameters: {remaining_params}")
        
        # Execute mapping
        mapped_command = actmap.map_command_direct(action_name, target_interface, parse_result)
        
        if mapped_command:
            print(mapped_command)
            if debug_mode:
                success("Action executed successfully")
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
        
# Add subcommands
cli.add_command(map)
cli.add_command(act)


if __name__ == '__main__':
    cli()