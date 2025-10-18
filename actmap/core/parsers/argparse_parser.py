from typing import Dict, List, Any, Optional


class ArgparseParser:
    """argparse style parser (supports new configuration format)"""
    
    def __init__(self, arg_parse_config: List[Dict[str, Any]]):
        self.arg_parse_config = arg_parse_config
        
    def parse(self, args: List[str]) -> Dict[str, Any]:
        """Parse argparse style arguments"""
        result = {
            'parsed_kwargs': {},
            'present_params': {},
        }
        
        # Initialize default values
        self._init_defaults(result)
        
        if not args:
            return result
        
        # Find matching main parameter configuration (prioritize subcommands)
        matched_config = None
        sub_cmd_configs = [cfg for cfg in self.arg_parse_config if cfg.get('is_sub_cmd', False)]
        flag_configs = [cfg for cfg in self.arg_parse_config if not cfg.get('is_sub_cmd', False)]
        
        # First look for subcommands (must be at the beginning of arguments)
        for config in sub_cmd_configs:
            if args[0] == config['name']:  # Subcommand must be in first position
                matched_config = config
                break
        
        # If no subcommand found, look for global flags
        if not matched_config:
            for config in flag_configs:
                # Check short_opt or long_opt
                short_opt = config.get('short_opt')
                long_opt = config.get('long_opt')
                if (short_opt and short_opt in args) or (long_opt and long_opt in args):
                    matched_config = config
                    break
        
        if matched_config:
            logical_name = matched_config.get('name', '')
            arg_key = matched_config.get('arg', 'pkgs')
            is_sub_cmd = matched_config.get('is_sub_cmd', False)
            
            # Fix: For subcommands, original_opt should be the subcommand name itself
            original_opt = matched_config.get('short_opt') or matched_config.get('long_opt') or logical_name
            
            # Record parameter
            result['present_params'][logical_name] = {
                'present': True, 
                'value': None, 
                'is_sub_cmd': is_sub_cmd,
                'original_opt': original_opt
            }
            
            # Collect parameter values (remaining arguments)
            param_values = []
            remaining_args = []
            
            if is_sub_cmd:
                # For subcommands, only collect arguments after the subcommand
                if args[0] == logical_name:  # Use logical name for matching
                    remaining_args = args[1:]
                else:
                    # Subcommand not in first position, treat as invalid
                    result['present_params'][logical_name]['present'] = False
            else:
                # For global flags, collect all non-flag arguments
                opt_name = matched_config.get('short_opt') or matched_config.get('long_opt')
                remaining_args = [arg for arg in args if not (arg.startswith('--') or arg == opt_name)]
            
            # Process remaining arguments: distinguish between parameter values and sub-parameters
            i = 0
            while i < len(remaining_args):
                arg = remaining_args[i]
                
                if arg.startswith('--') or (arg.startswith('-') and len(arg) > 2):
                    # This is a sub-parameter, check if it matches configuration
                    sub_config = self._find_sub_config_by_option(matched_config.get('sub_args', []), arg)
                    if sub_config:
                        sub_logical_name = sub_config.get('name', '')
                        sub_arg_key = sub_config.get('arg')
                        is_flag = sub_config.get('is_flag', False)
                        
                        result['present_params'][sub_logical_name] = {
                            'present': True, 
                            'value': True if is_flag else None,
                            'is_sub_cmd': False,
                            'original_opt': sub_config.get('short_opt') or sub_config.get('long_opt')
                        }
                        
                        if is_flag and sub_arg_key:
                            result['parsed_kwargs'][sub_arg_key] = True
                        i += 1
                    else:
                        # Unknown sub-parameter, skip
                        i += 1
                else:
                    # Regular parameter, treat as parameter value
                    param_values.append(arg)
                    i += 1
            
            if param_values:
                result['parsed_kwargs'][arg_key] = param_values
        
        return result
    
    def _init_defaults(self, result: Dict[str, Any]):
        """Initialize default values"""
        for config in self.arg_parse_config:
            arg_key = config.get('arg', 'pkgs')
            
            # Initialize empty list for cmd_arg
            if config.get('is_cmd_arg', False):
                result['parsed_kwargs'][arg_key] = []
                continue
                
            if config.get('is_sub_cmd', False):
                result['parsed_kwargs'][arg_key] = []
            
            # Initialize default values for sub-parameters
            for sub_config in config.get('sub_args', []):
                sub_arg_key = sub_config.get('arg')
                if sub_arg_key and sub_config.get('is_flag', False):
                    result['parsed_kwargs'][sub_arg_key] = False
    
    def _find_sub_config_by_option(self, sub_configs: List[Dict[str, Any]], option_name: str) -> Optional[Dict[str, Any]]:
        """Find configuration by option name in sub-configuration list"""
        for config in sub_configs:
            if config.get('short_opt') == option_name or config.get('long_opt') == option_name:
                return config
        return None