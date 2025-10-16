from typing import Dict, List, Any, Optional


class ArgparseParser:
    """argparse 风格解析器（支持新配置格式）"""
    
    def __init__(self, arg_parse_config: List[Dict[str, Any]]):
        self.arg_parse_config = arg_parse_config
        
    def parse(self, args: List[str]) -> Dict[str, Any]:
        """解析 argparse 风格参数"""
        result = {
            'parsed_kwargs': {},
            'present_params': {},
        }
        
        # 初始化默认值
        self._init_defaults(result)
        
        if not args:
            return result
        
        # 查找匹配的主参数配置（优先查找子命令）
        matched_config = None
        sub_cmd_configs = [cfg for cfg in self.arg_parse_config if cfg.get('is_sub_cmd', False)]
        flag_configs = [cfg for cfg in self.arg_parse_config if not cfg.get('is_sub_cmd', False)]
        
        # 首先查找子命令（必须在参数的开头位置）
        for config in sub_cmd_configs:
            if args[0] == config['name']:  # 子命令必须在第一个位置
                matched_config = config
                break
        
        # 如果没有找到子命令，查找全局标志
        if not matched_config:
            for config in flag_configs:
                # 检查 short_opt 或 long_opt
                short_opt = config.get('short_opt')
                long_opt = config.get('long_opt')
                if (short_opt and short_opt in args) or (long_opt and long_opt in args):
                    matched_config = config
                    break
        
        if matched_config:
            logical_name = matched_config.get('name', '')
            arg_key = matched_config.get('arg', 'pkgs')
            is_sub_cmd = matched_config.get('is_sub_cmd', False)
            
            # 修复：对于子命令，original_opt 应该是子命令名称本身
            original_opt = matched_config.get('short_opt') or matched_config.get('long_opt') or logical_name
            
            # 记录参数
            result['present_params'][logical_name] = {
                'present': True, 
                'value': None, 
                'is_sub_cmd': is_sub_cmd,
                'original_opt': original_opt
            }
            
            # 收集参数值（剩余参数）
            param_values = []
            remaining_args = []
            
            if is_sub_cmd:
                # 对于子命令，只收集子命令后面的参数
                if args[0] == logical_name:  # 使用逻辑名称匹配
                    remaining_args = args[1:]
                else:
                    # 子命令不在第一个位置，视为无效
                    result['present_params'][logical_name]['present'] = False
            else:
                # 对于全局标志，收集所有非标志参数
                opt_name = matched_config.get('short_opt') or matched_config.get('long_opt')
                remaining_args = [arg for arg in args if not (arg.startswith('--') or arg == opt_name)]
            
            # 处理剩余参数：区分参数值和子参数
            i = 0
            while i < len(remaining_args):
                arg = remaining_args[i]
                
                if arg.startswith('--') or (arg.startswith('-') and len(arg) > 2):
                    # 这是子参数，检查是否匹配配置
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
                        # 未知的子参数，跳过
                        i += 1
                else:
                    # 普通参数，当作参数值
                    param_values.append(arg)
                    i += 1
            
            if param_values:
                result['parsed_kwargs'][arg_key] = param_values
        
        return result
    
    def _init_defaults(self, result: Dict[str, Any]):
        """初始化默认值"""
        for config in self.arg_parse_config:
            arg_key = config.get('arg', 'pkgs')
            
            # 为 cmd_arg 初始化空列表
            if config.get('is_cmd_arg', False):
                result['parsed_kwargs'][arg_key] = []
                continue
                
            if config.get('is_sub_cmd', False):
                result['parsed_kwargs'][arg_key] = []
            
            # 初始化子参数的默认值
            for sub_config in config.get('sub_args', []):
                sub_arg_key = sub_config.get('arg')
                if sub_arg_key and sub_config.get('is_flag', False):
                    result['parsed_kwargs'][sub_arg_key] = False
    
    def _find_sub_config_by_option(self, sub_configs: List[Dict[str, Any]], option_name: str) -> Optional[Dict[str, Any]]:
        """在子配置列表中通过选项名查找"""
        for config in sub_configs:
            if config.get('short_opt') == option_name or config.get('long_opt') == option_name:
                return config
        return None