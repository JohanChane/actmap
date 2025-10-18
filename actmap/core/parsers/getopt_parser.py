from typing import Dict, List, Any, Optional


class GetoptParser:
    """getopt style parser (supports new configuration format)"""
    
    def __init__(self, arg_parse_config: List[Dict[str, Any]]):
        self.arg_parse_config = arg_parse_config
        
    def parse(self, args: List[str]) -> Dict[str, Any]:
        """Parse getopt style arguments"""
        result = {
            'parsed_kwargs': {},
            'present_params': {},
        }
        
        # Expand combined arguments - support repeated options
        expanded_args = self._expand_combined_args(args)
        
        # Initialize default values
        self._init_defaults(result)
        
        # Find cmd_arg configuration
        cmd_arg_config = self._find_cmd_arg_config()
        
        # Remove these two print statements
        # print(f"   Expanded arguments: {expanded_args}")
        # print(f"   cmd_arg configuration: {cmd_arg_config}")
        
        i = 0
        while i < len(expanded_args):
            arg = expanded_args[i]
            
            if arg.startswith('-'):
                # First try to find as main parameter
                config = self._find_config_by_option(arg)
                if config:
                    i = self._parse_option_arg(i, expanded_args, config, result)
                else:
                    # If not main parameter, try to find as sub-parameter
                    sub_config = self._find_sub_config_globally(arg)
                    if sub_config:
                        self._handle_standalone_sub_arg(sub_config, result)
                        i += 1
                    else:
                        # Unknown option, skip
                        i += 1
            else:
                # Handle package name parameters (cmd_arg)
                if cmd_arg_config:
                    self._handle_cmd_arg(arg, cmd_arg_config, result)
                else:
                    # If no cmd_arg configuration, treat as normal parameter value
                    pass
                i += 1
        
        return result
        
    def _init_defaults(self, result: Dict[str, Any]):
        """Initialize default values"""
        for config in self.arg_parse_config:
            arg_key = config.get('arg')
            logical_name = config.get('name', '')
            
            # Initialize empty list for cmd_arg
            if config.get('is_cmd_arg', False):
                if arg_key:
                    result['parsed_kwargs'][arg_key] = []
                continue
                
            # Initialize default values for flag parameters
            if config.get('is_flag', False) and arg_key:
                result['parsed_kwargs'][arg_key] = False
            
            # Initialize default values for sub-parameters
            for sub_config in config.get('sub_args', []):
                sub_arg_key = sub_config.get('arg')
                if sub_arg_key and sub_config.get('is_flag', False):
                    result['parsed_kwargs'][sub_arg_key] = False
    
    def _parse_option_arg(self, current_index: int, args: List[str], 
                         config: Dict[str, Any], result: Dict[str, Any]) -> int:
        """Parse option argument - support repeated option counting"""
        i = current_index
        logical_name = config.get('name', '')
        arg_key = config.get('arg')
        is_flag = config.get('is_flag', False)
        is_repeatable = config.get('is_repeatable', False)
        sub_args = config.get('sub_args', [])
        
        # Record parameter (using logical name as key)
        # If parameter already exists and is repeatable, increment count
        if logical_name in result['present_params'] and is_repeatable:
            current_value = result['present_params'][logical_name]['value']
            if isinstance(current_value, int):
                result['present_params'][logical_name]['value'] = current_value + 1
            else:
                result['present_params'][logical_name]['value'] = 2
        else:
            result['present_params'][logical_name] = {
                'present': True, 
                'value': 1 if is_flag else None,
                'is_sub_cmd': False,
                'original_opt': config.get('short_opt') or config.get('long_opt'),
                'is_repeatable': is_repeatable
            }
        
        # If it's a flag parameter, set corresponding value (support counting)
        if is_flag and arg_key:
            if arg_key in result['parsed_kwargs'] and is_repeatable:
                current_val = result['parsed_kwargs'][arg_key]
                if isinstance(current_val, int):
                    result['parsed_kwargs'][arg_key] = current_val + 1
                else:
                    result['parsed_kwargs'][arg_key] = 2
            else:
                result['parsed_kwargs'][arg_key] = True
        
        # Move to next argument
        i += 1
        
        # Handle sub-arguments
        if sub_args and i < len(args) and args[i].startswith('-'):
            i = self._parse_sub_args(i, args, sub_args, result)
        
        return i
    
    def _parse_sub_args(self, current_index: int, args: List[str], 
                       sub_configs: List[Dict[str, Any]], result: Dict[str, Any]) -> int:
        """Parse sub-arguments - support repeated option counting"""
        i = current_index
        
        while i < len(args):
            arg = args[i]
            
            if not arg.startswith('-'):
                # Non-option argument, stop parsing sub-arguments
                break
                
            sub_config = self._find_config_by_option_in_list(sub_configs, arg)
            if not sub_config:
                # Not a sub-argument, stop parsing
                break
                
            logical_name = sub_config.get('name', '')
            arg_key = sub_config.get('arg')
            is_flag = sub_config.get('is_flag', False)
            is_repeatable = sub_config.get('is_repeatable', False)
            
            # Record sub-parameter (support counting)
            if logical_name in result['present_params'] and is_repeatable:
                current_value = result['present_params'][logical_name]['value']
                if isinstance(current_value, int):
                    result['present_params'][logical_name]['value'] = current_value + 1
                else:
                    result['present_params'][logical_name]['value'] = 2
            else:
                result['present_params'][logical_name] = {
                    'present': True, 
                    'value': 1 if is_flag else None,
                    'is_sub_cmd': False,
                    'original_opt': sub_config.get('short_opt') or sub_config.get('long_opt'),
                    'is_repeatable': is_repeatable
                }
            
            if is_flag and arg_key:
                if arg_key in result['parsed_kwargs'] and is_repeatable:
                    current_val = result['parsed_kwargs'][arg_key]
                    if isinstance(current_val, int):
                        result['parsed_kwargs'][arg_key] = current_val + 1
                    else:
                        result['parsed_kwargs'][arg_key] = 2
                else:
                    result['parsed_kwargs'][arg_key] = True
            
            i += 1
        
        return i
    
    def _handle_cmd_arg(self, arg: str, config: Dict[str, Any], result: Dict[str, Any]):
        """Handle cmd_arg parameters (generic parameter values)"""
        arg_key = config.get('arg', 'pkgs')
        
        # Add to parameter value list
        if arg_key not in result['parsed_kwargs']:
            result['parsed_kwargs'][arg_key] = []
        result['parsed_kwargs'][arg_key].append(arg)
    
    def _handle_standalone_sub_arg(self, config: Dict[str, Any], result: Dict[str, Any]):
        """Handle standalone sub-arguments"""
        logical_name = config.get('name', '')
        arg_key = config.get('arg')
        is_flag = config.get('is_flag', False)
        is_repeatable = config.get('is_repeatable', False)
        
        # Support repeated option counting
        if logical_name in result['present_params'] and is_repeatable:
            current_value = result['present_params'][logical_name]['value']
            if isinstance(current_value, int):
                result['present_params'][logical_name]['value'] = current_value + 1
            else:
                result['present_params'][logical_name]['value'] = 2
        else:
            result['present_params'][logical_name] = {
                'present': True, 
                'value': 1 if is_flag else None,
                'is_sub_cmd': False,
                'original_opt': config.get('short_opt') or config.get('long_opt'),
                'is_repeatable': is_repeatable
            }
        
        if is_flag and arg_key:
            if arg_key in result['parsed_kwargs'] and is_repeatable:
                current_val = result['parsed_kwargs'][arg_key]
                if isinstance(current_val, int):
                    result['parsed_kwargs'][arg_key] = current_val + 1
                else:
                    result['parsed_kwargs'][arg_key] = 2
            else:
                result['parsed_kwargs'][arg_key] = True
    
    def _find_config_by_option(self, option_name: str) -> Optional[Dict[str, Any]]:
        """Find configuration by option name"""
        for config in self.arg_parse_config:
            # Check short_opt
            if config.get('short_opt') == option_name:
                return config
            # Check long_opt
            if config.get('long_opt') == option_name:
                return config
        return None
    
    def _find_config_by_option_in_list(self, configs: List[Dict[str, Any]], option_name: str) -> Optional[Dict[str, Any]]:
        """Find configuration by option name in configuration list"""
        for config in configs:
            if config.get('short_opt') == option_name or config.get('long_opt') == option_name:
                return config
        return None
    
    def _find_sub_config_globally(self, option_name: str) -> Optional[Dict[str, Any]]:
        """Find sub-parameter configuration globally"""
        for config in self.arg_parse_config:
            for sub_config in config.get('sub_args', []):
                if (sub_config.get('short_opt') == option_name or 
                    sub_config.get('long_opt') == option_name):
                    return sub_config
        return None
    
    def _find_cmd_arg_config(self) -> Optional[Dict[str, Any]]:
        """Find is_cmd_arg configuration"""
        for config in self.arg_parse_config:
            if config.get('is_cmd_arg', False):
                return config
        return None
    
    def _expand_combined_args(self, args: List[str]) -> List[str]:
        """Expand combined arguments - support repeated options"""
        expanded = []
        for arg in args:
            # Handle combined arguments like -Syyu
            if (arg.startswith('-') and 
                len(arg) > 2 and 
                not arg.startswith('--') and
                arg[1] != '-'):  # Ensure not double dash
                
                # Check for repeated characters
                chars = list(arg[1:])
                expanded_chars = []
                
                # Count occurrences of each character
                char_count = {}
                for char in chars:
                    char_count[char] = char_count.get(char, 0) + 1
                
                # Generate corresponding arguments based on occurrence count
                for char, count in char_count.items():
                    if count == 1:
                        expanded_chars.append(f'-{char}')
                    else:
                        # Repeated character, generate multiple arguments
                        for _ in range(count):
                            expanded_chars.append(f'-{char}')
                
                expanded.extend(expanded_chars)
            else:
                expanded.append(arg)
        return expanded