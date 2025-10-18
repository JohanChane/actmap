from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from .factory import ParserFactory
from ..config.loader import load_config
from ..log import debug, info, success, error, warning


class ActMap:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.config = load_config(self.config_path)
        self.debug_mode = False  # Add debug mode flag
        
    def set_debug(self, debug_flag: bool):
        """Set debug mode"""
        self.debug_mode = debug_flag
    
    def get_supported_actions(self) -> List[str]:
        """Get all supported actions"""
        return list(self.config.get('actions', {}).keys())
    
    def get_supported_interfaces(self) -> List[str]:
        """Get all supported interfaces"""
        return list(self.config.get('action_interfaces', {}).keys())
    
    def parse_arguments(self, interface: str, command_args: List[str]) -> Dict[str, Any]:
        """Parse arguments according to configuration"""
        interface_config = self.config.get('action_interfaces', {}).get(interface, {})
        args_config = interface_config.get('args', {})
        
        if self.debug_mode:
            debug(f"   Interface config keys: {list(interface_config.keys())}")
            debug(f"   Args config keys: {list(args_config.keys())}")
            debug(f"   Command arguments: {command_args}")
        
        if not command_args:
            return {'parsed_kwargs': {}, 'present_params': {}, 'detected_command': None}
        
        first_arg = command_args[0]
        
        if self.debug_mode:
            debug(f"   First argument: '{first_arg}'")
        
        # Find matching command configuration (keys ending with _command)
        for cmd_key, cmd_config in args_config.items():
            if cmd_key.endswith('_command'):
                cmd_name = cmd_config.get('cmd_name')
                if self.debug_mode:
                    debug(f"   Checking command config: {cmd_key} -> {cmd_name}")
                if cmd_name == first_arg:
                    parser_type = cmd_config.get('arg_parser', 'argparse')
                    arg_parse_config = cmd_config.get('arg_parse', [])
                    
                    if self.debug_mode:
                        debug(f"   Found matching command: {cmd_name}, using parser: {parser_type}")
                        debug(f"   Parse config: {arg_parse_config}")
                    
                    # Use existing parser factory
                    from .factory import ParserFactory
                    parser = ParserFactory.create_parser(parser_type, arg_parse_config)
                    result = parser.parse(command_args[1:])  # Remove command name
                    result['detected_command'] = first_arg
                    
                    if self.debug_mode:
                        debug(f"   Parse result: {result}")
                    
                    return result
        
        if self.debug_mode:
            debug("   No parsing configuration found")
        
        return {'parsed_kwargs': {}, 'present_params': {}, 'detected_command': None}

    def detect_action(self, interface: str, parse_result: Dict[str, Any]) -> Optional[str]:
        """Detect action"""
        interface_config = self.config.get('action_interfaces', {}).get(interface, {})
        triggers_config = interface_config.get('triggers', {})
        
        detected_command = parse_result.get('detected_command')
        present_params = parse_result['present_params']
        
        if self.debug_mode:
            debug(f"   Detected command: {detected_command}")
            debug(f"   Present parameters: {list(present_params.keys())}")
            debug(f"   Triggers config keys: {list(triggers_config.keys())}")
        
        # Find corresponding rule group based on detected command
        for rules_key, rules_config in triggers_config.items():
            if rules_key.endswith('_command'):
                rules_cmd_name = rules_config.get('cmd_name')
                if self.debug_mode:
                    debug(f"   Checking rule group: {rules_key} -> {rules_cmd_name}")
                if rules_cmd_name == detected_command:
                    rules = rules_config.get('rules', [])
                    if self.debug_mode:
                        debug(f"   Found matching rule group, rule count: {len(rules)}")
                        for i, rule in enumerate(rules):
                            debug(f"     Rule {i}: {rule.get('name', 'unnamed')}")
                    # Fix: Add parse_result parameter
                    return self._check_rules(rules, present_params, parse_result)
        
        if self.debug_mode:
            debug("   No matching rules found")
        
        return None  # Return None if no matching command found

    def _check_rules(self, rules: List[Dict], present_params: Dict, parse_result: Dict) -> Optional[str]:
        """Check rule list - consider arg_map and parameter existence"""
        for rule in rules:
            condition = rule.get('condition', {})
            triggers = rule.get('trigger', [])
            
            if self._check_condition(condition, present_params):
                # Check all matching trigger rules
                matched_triggers = []
                for trigger in triggers:
                    trigger_params = trigger.get('params', [])
                    action = trigger.get('action')
                    
                    if self._check_condition({'params': trigger_params}, present_params):
                        matched_triggers.append(trigger)
                
                # Select appropriate trigger rule based on arg_map and parameter existence
                if matched_triggers:
                    return self._select_trigger_by_arg_map(matched_triggers, parse_result)
        
        return None

    def _select_trigger_by_arg_map(self, triggers: List[Dict], parse_result: Dict) -> Optional[str]:
        """Select appropriate trigger rule based on arg_map and parameter existence"""
        parsed_kwargs = parse_result.get('parsed_kwargs', {})
        targets = parsed_kwargs.get('targets', [])
        
        # Prefer rules with arg_map and non-empty targets
        for trigger in triggers:
            has_arg_map = 'arg_map' in trigger
            if has_arg_map and targets:
                return trigger.get('action')
        
        # Then check rules without arg_map and empty targets
        for trigger in triggers:
            has_arg_map = 'arg_map' in trigger
            if not has_arg_map and not targets:
                return trigger.get('action')
        
        return None
    
    def _check_condition(self, condition: Dict[str, Any], present_params: Dict[str, Any]) -> bool:
        """Check condition - support new config format and repeat count check"""
        params_conditions = condition.get('params', [])
        
        # Empty condition always matches (for no_arg rules)
        if not params_conditions:
            return True
        
        for param_condition in params_conditions:
            logical_name = param_condition.get('name', '')
            expected_value = param_condition.get('value')
            repeat_count = param_condition.get('repeat')  # New: check repeat count
            is_sub_cmd = param_condition.get('is_sub_cmd', False)
            
            if logical_name not in present_params:
                return False
            
            param_info = present_params[logical_name]
            
            if not param_info['present']:
                return False
            
            # Check sub-command condition
            if is_sub_cmd and not param_info.get('is_sub_cmd', False):
                return False
            
            # Check repeat count condition
            if repeat_count is not None:
                param_value = param_info['value']
                if not isinstance(param_value, int) or param_value != repeat_count:
                    return False
            
            # Check value condition
            if expected_value is not None and param_info['value'] != expected_value:
                return False
    
        return True
    
    def map_command(self, source_interface: str, target_interface: str, 
                action: Optional[str], parse_result: Dict[str, Any]) -> str:
        """Generate command, support parameter mapping"""
        if action is None:
            return ""
        
        actions_config = self.config.get('actions', {})
        
        if action not in actions_config:
            raise ValueError(f"Unknown action: {action}")
        
        target_config = actions_config[action].get(target_interface)
        if not target_config:
            raise ValueError(f"Target interface does not support action: {target_interface}")
        
        cmd_format = target_config['cmd_format']
        parsed_kwargs = parse_result['parsed_kwargs']
        
        # Get parameter mappings from trigger rules
        arg_mappings = self._get_argument_mappings(source_interface, action, parse_result)
        
        # Apply parameter mappings
        mapped_kwargs = parsed_kwargs.copy()
        for source_arg, target_arg in arg_mappings.items():
            if source_arg in mapped_kwargs:
                mapped_kwargs[target_arg] = mapped_kwargs.pop(source_arg)
        
        debug(f"   Parameter names extracted from template: {re.findall(r'\{(\w+)\}', cmd_format)}")
        debug(f"   Mapped parameters: {mapped_kwargs}")
        
        # Format command using mapped parameters
        formatted_cmd = cmd_format
        
        for param_name in re.findall(r'\{(\w+)\}', cmd_format):
            if param_name in mapped_kwargs:
                value = mapped_kwargs[param_name]
                
                if isinstance(value, list):
                    if value:
                        # List is not empty, join with spaces and replace placeholder
                        placeholder = ' '.join(str(v) for v in value)
                        formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', placeholder)
                    else:
                        # List is empty, completely remove placeholder
                        formatted_cmd = formatted_cmd.replace(f' {{{param_name}}}', '')  # Space before
                        formatted_cmd = formatted_cmd.replace(f'{{{param_name}}} ', '')  # Space after
                        formatted_cmd = formatted_cmd.replace(f' {{{param_name}}} ', '') # Spaces both sides
                        formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', '')   # No spaces
                elif isinstance(value, bool):
                    # Boolean values not replaced, only used in command format when needed
                    continue
                else:
                    placeholder = str(value)
                    formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', placeholder)
            else:
                # Parameter name in template but not in parse result, remove placeholder
                formatted_cmd = formatted_cmd.replace(f' {{{param_name}}}', '')
                formatted_cmd = formatted_cmd.replace(f'{{{param_name}}} ', '')
                formatted_cmd = formatted_cmd.replace(f' {{{param_name}}} ', '')
                formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', '')
        
        # Clean up extra spaces
        formatted_cmd = ' '.join(formatted_cmd.split())
        
        return formatted_cmd

    def _get_argument_mappings(self, source_interface: str, action: str, 
                            parse_result: Dict[str, Any]) -> Dict[str, str]:
        """Get parameter mapping configuration"""
        interface_config = self.config.get('action_interfaces', {}).get(source_interface, {})
        triggers_config = interface_config.get('triggers', {})
        
        arg_mappings = {}
        
        # Iterate through all trigger rules
        for rules_key, rules_config in triggers_config.items():
            if rules_key.endswith('_command'):
                rules = rules_config.get('rules', [])
                for rule in rules:
                    triggers = rule.get('trigger', [])
                    for trigger in triggers:
                        if trigger.get('action') == action:
                            # Check if there is parameter mapping configuration
                            arg_map = trigger.get('arg_map', {})
                            arg_mappings.update(arg_map)
        
        return arg_mappings

    def detect_source_interface(self, command_args: List[str]) -> Optional[str]:
        """Automatically detect source package manager interface based on command arguments"""
        if not command_args:
            return None
        
        first_arg = command_args[0]
        
        if self.debug_mode:
            debug(f"Auto-detecting source interface, first argument: '{first_arg}'")
        
        matches = []
        
        # Collect all matching interfaces
        for interface_name, interface_config in self.config.get('action_interfaces', {}).items():
            triggers_config = interface_config.get('triggers', {})
            
            for rules_key, rules_config in triggers_config.items():
                if rules_key.endswith('_command'):
                    cmd_name = rules_config.get('cmd_name')
                    if cmd_name == first_arg:
                        matches.append(interface_name)
                        if self.debug_mode:
                            debug(f"Found matching source interface: {interface_name} (command: {cmd_name})")
        
        # Process matching results
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            warning(f"Multiple package managers support command '{first_arg}': {', '.join(matches)}")
            warning(f"Please use -s/--source option to explicitly specify source package manager, e.g.:")
            warning(f"  actmap -s {matches[0]} map -- {first_arg} ...")
            return None
        else:
            return None
        
    def map_command_direct(self, action: str, target_interface: str, parse_result: Dict[str, Any]) -> str:
        """Directly map action to target command"""
        actions_config = self.config.get('actions', {})
        
        if action not in actions_config:
            raise ValueError(f"Unknown action: {action}")
        
        target_config = actions_config[action].get(target_interface)
        if not target_config:
            raise ValueError(f"Target interface does not support action: {target_interface}")
        
        cmd_format = target_config['cmd_format']
        parsed_kwargs = parse_result['parsed_kwargs']
        
        if self.debug_mode:
            debug(f"   Direct mapping action: {action} -> {target_interface}")
            debug(f"   Command template: {cmd_format}")
            debug(f"   Parameters: {parsed_kwargs}")
        
        # Manual placeholder replacement - fix list parameter handling
        formatted_cmd = cmd_format
        for key, value in parsed_kwargs.items():
            placeholder = f'{{{key}}}'
            if placeholder in formatted_cmd:
                # Handle list parameters: join list elements with spaces
                if isinstance(value, list):
                    formatted_value = ' '.join(str(v) for v in value)
                else:
                    formatted_value = str(value)
                formatted_cmd = formatted_cmd.replace(placeholder, formatted_value)
        
        # Clean up extra spaces
        formatted_cmd = ' '.join(formatted_cmd.split())
        
        if self.debug_mode:
            debug(f"   Mapping result: {formatted_cmd}")
        
        return formatted_cmd

    def _remove_placeholder(self, cmd: str, placeholder: str) -> str:
        """Remove placeholder from command template"""
        # Try different space combinations to remove placeholder
        patterns = [
            f' {placeholder} ',
            f' {placeholder}',
            f'{placeholder} ',
            f'{placeholder}'
        ]
        
        for pattern in patterns:
            if pattern in cmd:
                cmd = cmd.replace(pattern, '')
        
        return cmd