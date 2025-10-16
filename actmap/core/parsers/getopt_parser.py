from typing import Dict, List, Any, Optional


class GetoptParser:
    """getopt 风格解析器（支持新配置格式）"""
    
    def __init__(self, arg_parse_config: List[Dict[str, Any]]):
        self.arg_parse_config = arg_parse_config
        
    def parse(self, args: List[str]) -> Dict[str, Any]:
        """解析 getopt 风格参数"""
        result = {
            'parsed_kwargs': {},
            'present_params': {},
        }
        
        # 展开组合参数 - 支持重复选项
        expanded_args = self._expand_combined_args(args)
        
        # 初始化默认值
        self._init_defaults(result)
        
        # 查找 cmd_arg 配置
        cmd_arg_config = self._find_cmd_arg_config()
        
        # 删除这两行 print 语句
        # print(f"   展开后参数: {expanded_args}")
        # print(f"   cmd_arg 配置: {cmd_arg_config}")
        
        i = 0
        while i < len(expanded_args):
            arg = expanded_args[i]
            
            if arg.startswith('-'):
                # 首先尝试作为主参数查找
                config = self._find_config_by_option(arg)
                if config:
                    i = self._parse_option_arg(i, expanded_args, config, result)
                else:
                    # 如果不是主参数，尝试作为子参数查找
                    sub_config = self._find_sub_config_globally(arg)
                    if sub_config:
                        self._handle_standalone_sub_arg(sub_config, result)
                        i += 1
                    else:
                        # 未知选项，跳过
                        i += 1
            else:
                # 处理包名参数（cmd_arg）
                if cmd_arg_config:
                    self._handle_cmd_arg(arg, cmd_arg_config, result)
                else:
                    # 如果没有 cmd_arg 配置，当作普通参数值
                    pass
                i += 1
        
        return result
        
    def _init_defaults(self, result: Dict[str, Any]):
        """初始化默认值"""
        for config in self.arg_parse_config:
            arg_key = config.get('arg')
            logical_name = config.get('name', '')
            
            # 为 cmd_arg 初始化空列表
            if config.get('is_cmd_arg', False):
                if arg_key:
                    result['parsed_kwargs'][arg_key] = []
                continue
                
            # 初始化标志参数的默认值
            if config.get('is_flag', False) and arg_key:
                result['parsed_kwargs'][arg_key] = False
            
            # 初始化子参数的默认值
            for sub_config in config.get('sub_args', []):
                sub_arg_key = sub_config.get('arg')
                if sub_arg_key and sub_config.get('is_flag', False):
                    result['parsed_kwargs'][sub_arg_key] = False
    
    def _parse_option_arg(self, current_index: int, args: List[str], 
                         config: Dict[str, Any], result: Dict[str, Any]) -> int:
        """解析选项参数 - 支持重复选项计数"""
        i = current_index
        logical_name = config.get('name', '')
        arg_key = config.get('arg')
        is_flag = config.get('is_flag', False)
        is_repeatable = config.get('is_repeatable', False)
        sub_args = config.get('sub_args', [])
        
        # 记录参数（使用逻辑名称作为键）
        # 如果参数已经存在且可重复，增加计数
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
        
        # 如果是标志参数，设置对应的值（支持计数）
        if is_flag and arg_key:
            if arg_key in result['parsed_kwargs'] and is_repeatable:
                current_val = result['parsed_kwargs'][arg_key]
                if isinstance(current_val, int):
                    result['parsed_kwargs'][arg_key] = current_val + 1
                else:
                    result['parsed_kwargs'][arg_key] = 2
            else:
                result['parsed_kwargs'][arg_key] = True
        
        # 移动到下一个参数
        i += 1
        
        # 处理子参数
        if sub_args and i < len(args) and args[i].startswith('-'):
            i = self._parse_sub_args(i, args, sub_args, result)
        
        return i
    
    def _parse_sub_args(self, current_index: int, args: List[str], 
                       sub_configs: List[Dict[str, Any]], result: Dict[str, Any]) -> int:
        """解析子参数 - 支持重复选项计数"""
        i = current_index
        
        while i < len(args):
            arg = args[i]
            
            if not arg.startswith('-'):
                # 非选项参数，停止解析子参数
                break
                
            sub_config = self._find_config_by_option_in_list(sub_configs, arg)
            if not sub_config:
                # 不是子参数，停止解析
                break
                
            logical_name = sub_config.get('name', '')
            arg_key = sub_config.get('arg')
            is_flag = sub_config.get('is_flag', False)
            is_repeatable = sub_config.get('is_repeatable', False)
            
            # 记录子参数（支持计数）
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
        """处理 cmd_arg 参数（通用参数值）"""
        arg_key = config.get('arg', 'pkgs')
        
        # 添加到参数值列表
        if arg_key not in result['parsed_kwargs']:
            result['parsed_kwargs'][arg_key] = []
        result['parsed_kwargs'][arg_key].append(arg)
    
    def _handle_standalone_sub_arg(self, config: Dict[str, Any], result: Dict[str, Any]):
        """处理独立的子参数"""
        logical_name = config.get('name', '')
        arg_key = config.get('arg')
        is_flag = config.get('is_flag', False)
        is_repeatable = config.get('is_repeatable', False)
        
        # 支持重复选项计数
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
        """通过选项名查找配置"""
        for config in self.arg_parse_config:
            # 检查 short_opt
            if config.get('short_opt') == option_name:
                return config
            # 检查 long_opt
            if config.get('long_opt') == option_name:
                return config
        return None
    
    def _find_config_by_option_in_list(self, configs: List[Dict[str, Any]], option_name: str) -> Optional[Dict[str, Any]]:
        """在配置列表中通过选项名查找"""
        for config in configs:
            if config.get('short_opt') == option_name or config.get('long_opt') == option_name:
                return config
        return None
    
    def _find_sub_config_globally(self, option_name: str) -> Optional[Dict[str, Any]]:
        """全局查找子参数配置"""
        for config in self.arg_parse_config:
            for sub_config in config.get('sub_args', []):
                if (sub_config.get('short_opt') == option_name or 
                    sub_config.get('long_opt') == option_name):
                    return sub_config
        return None
    
    def _find_cmd_arg_config(self) -> Optional[Dict[str, Any]]:
        """查找 is_cmd_arg 配置"""
        for config in self.arg_parse_config:
            if config.get('is_cmd_arg', False):
                return config
        return None
    
    def _expand_combined_args(self, args: List[str]) -> List[str]:
        """展开组合参数 - 支持重复选项"""
        expanded = []
        for arg in args:
            # 处理 -Syyu 这样的组合参数
            if (arg.startswith('-') and 
                len(arg) > 2 and 
                not arg.startswith('--') and
                arg[1] != '-'):  # 确保不是双横线
                
                # 检查是否有重复字符
                chars = list(arg[1:])
                expanded_chars = []
                
                # 统计每个字符的出现次数
                char_count = {}
                for char in chars:
                    char_count[char] = char_count.get(char, 0) + 1
                
                # 根据出现次数生成对应的参数
                for char, count in char_count.items():
                    if count == 1:
                        expanded_chars.append(f'-{char}')
                    else:
                        # 重复字符，生成多个参数
                        for _ in range(count):
                            expanded_chars.append(f'-{char}')
                
                expanded.extend(expanded_chars)
            else:
                expanded.append(arg)
        return expanded