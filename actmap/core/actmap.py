from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from .factory import ParserFactory
from ..config.loader import load_config
from ..log import debug, info, success, error, warning  # 添加这行导入


class ActMap:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.config = load_config(self.config_path)
        self.debug_mode = False  # 添加 debug 模式标志
        
    def set_debug(self, debug_flag: bool):
        """设置debug模式"""
        self.debug_mode = debug_flag
    
    def get_supported_actions(self) -> List[str]:
        """获取所有支持的动作"""
        return list(self.config.get('actions', {}).keys())
    
    def get_supported_interfaces(self) -> List[str]:
        """获取所有支持的接口"""
        return list(self.config.get('action_interfaces', {}).keys())
    
    def parse_arguments(self, interface: str, command_args: List[str]) -> Dict[str, Any]:
        """根据配置解析参数 - 支持多命令结构"""
        interface_config = self.config.get('action_interfaces', {}).get(interface, {})
        args_config = interface_config.get('args', {})
        
        if self.debug_mode:
            debug(f"   接口配置键: {list(interface_config.keys())}")
            debug(f"   参数配置键: {list(args_config.keys())}")
            debug(f"   命令参数: {command_args}")
        
        if not command_args:
            return {'parsed_kwargs': {}, 'present_params': {}, 'detected_command': None}
        
        first_arg = command_args[0]
        
        if self.debug_mode:
            debug(f"   第一个参数: '{first_arg}'")
        
        # 查找匹配的命令配置（以 _command 结尾的键）
        for cmd_key, cmd_config in args_config.items():
            if cmd_key.endswith('_command'):
                cmd_name = cmd_config.get('cmd_name')
                if self.debug_mode:
                    debug(f"   检查命令配置: {cmd_key} -> {cmd_name}")
                if cmd_name == first_arg:
                    parser_type = cmd_config.get('arg_parser', 'argparse')
                    arg_parse_config = cmd_config.get('arg_parse', [])
                    
                    if self.debug_mode:
                        debug(f"   找到匹配命令: {cmd_name}, 使用解析器: {parser_type}")
                        debug(f"   解析配置: {arg_parse_config}")
                    
                    # 使用现有的解析器工厂
                    from .factory import ParserFactory
                    parser = ParserFactory.create_parser(parser_type, arg_parse_config)
                    result = parser.parse(command_args[1:])  # 移除命令名
                    result['detected_command'] = first_arg
                    
                    if self.debug_mode:
                        debug(f"   解析结果: {result}")
                    
                    return result
        
        # 向后兼容：如果没有找到命令配置，使用传统方式
        if 'arg_parse' in args_config:
            if self.debug_mode:
                debug("   使用传统单命令解析方式")
            parser_type = args_config.get('arg_parser', 'getopt')
            arg_parse_config = args_config.get('arg_parse', [])
            from .factory import ParserFactory
            parser = ParserFactory.create_parser(parser_type, arg_parse_config)
            result = parser.parse(command_args)
            result['detected_command'] = None
            
            if self.debug_mode:
                debug(f"   传统解析结果: {result}")
            
            return result
        
        if self.debug_mode:
            debug("   未找到任何解析配置")
        
        return {'parsed_kwargs': {}, 'present_params': {}, 'detected_command': None}

    def detect_action(self, interface: str, parse_result: Dict[str, Any]) -> Optional[str]:
        """检测动作 - 支持多命令结构"""
        interface_config = self.config.get('action_interfaces', {}).get(interface, {})
        triggers_config = interface_config.get('triggers', {})
        
        detected_command = parse_result.get('detected_command')
        present_params = parse_result['present_params']
        
        if self.debug_mode:
            debug(f"   检测到的命令: {detected_command}")
            debug(f"   出现的参数: {list(present_params.keys())}")
            debug(f"   触发配置键: {list(triggers_config.keys())}")
        
        # 根据检测到的命令查找对应的规则组
        for rules_key, rules_config in triggers_config.items():
            if rules_key.endswith('_command'):
                rules_cmd_name = rules_config.get('cmd_name')
                if self.debug_mode:
                    debug(f"   检查规则组: {rules_key} -> {rules_cmd_name}")
                if rules_cmd_name == detected_command:
                    rules = rules_config.get('rules', [])
                    if self.debug_mode:
                        debug(f"   找到匹配规则组，规则数量: {len(rules)}")
                        for i, rule in enumerate(rules):
                            debug(f"     规则 {i}: {rule.get('name', 'unnamed')}")
                    return self._check_rules(rules, present_params)
        
        # 向后兼容：如果没有找到命令规则，使用传统方式
        if 'rules' in triggers_config:
            if self.debug_mode:
                debug("   使用传统规则检测方式")
            rules = triggers_config.get('rules', [])
            return self._check_rules(rules, present_params)
        
        if self.debug_mode:
            debug("   未找到任何匹配的规则")
        
        return None

    def _check_rules(self, rules: List[Dict], present_params: Dict) -> Optional[str]:
        """检查规则列表"""
        for rule in rules:
            condition = rule.get('condition', {})
            triggers = rule.get('trigger', [])
            
            if self._check_condition(condition, present_params):
                for trigger in triggers:
                    trigger_params = trigger.get('params', [])
                    action = trigger.get('action')
                    
                    if self._check_condition({'params': trigger_params}, present_params):
                        return action
        return None
    
    def _check_condition(self, condition: Dict[str, Any], present_params: Dict[str, Any]) -> bool:
        """检查条件 - 支持新配置格式和重复次数检查"""
        params_conditions = condition.get('params', [])
        
        # 空条件总是匹配（用于 no_arg 规则）
        if not params_conditions:
            return True
        
        for param_condition in params_conditions:
            logical_name = param_condition.get('name', '')
            expected_value = param_condition.get('value')
            repeat_count = param_condition.get('repeat')  # 新增：检查重复次数
            is_sub_cmd = param_condition.get('is_sub_cmd', False)
            
            if logical_name not in present_params:
                return False
            
            param_info = present_params[logical_name]
            
            if not param_info['present']:
                return False
            
            # 检查子命令条件
            if is_sub_cmd and not param_info.get('is_sub_cmd', False):
                return False
            
            # 检查重复次数条件
            if repeat_count is not None:
                param_value = param_info['value']
                if not isinstance(param_value, int) or param_value != repeat_count:
                    return False
            
            # 检查值条件
            if expected_value is not None and param_info['value'] != expected_value:
                return False
    
        return True
    
    def map_command(self, source_interface: str, target_interface: str, 
                   action: Optional[str], parse_result: Dict[str, Any]) -> str:
        """生成命令，如果 action 为 None 则返回空字符串"""
        if action is None:
            return ""
        
        actions_config = self.config.get('actions', {})
        
        if action not in actions_config:
            raise ValueError(f"未知动作: {action}")
        
        target_config = actions_config[action].get(target_interface)
        if not target_config:
            raise ValueError(f"目标接口不支持动作: {target_interface}")
        
        cmd_format = target_config['cmd_format']
        parsed_kwargs = parse_result['parsed_kwargs']
        
        debug(f"   从模板中提取的参数名: {re.findall(r'\{(\w+)\}', cmd_format)}")
        
        # 格式化命令
        formatted_cmd = cmd_format
        
        for param_name in re.findall(r'\{(\w+)\}', cmd_format):
            if param_name in parsed_kwargs:
                value = parsed_kwargs[param_name]
                
                if isinstance(value, list):
                    if value:
                        # 列表不为空，用空格连接并替换占位符
                        placeholder = ' '.join(str(v) for v in value)
                        formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', placeholder)
                    else:
                        # 列表为空，完全移除占位符
                        formatted_cmd = formatted_cmd.replace(f' {{{param_name}}}', '')  # 前有空格
                        formatted_cmd = formatted_cmd.replace(f'{{{param_name}}} ', '')  # 后有空格
                        formatted_cmd = formatted_cmd.replace(f' {{{param_name}}} ', '') # 前后都有空格
                        formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', '')   # 无空格
                elif isinstance(value, bool):
                    # 布尔值不替换，只在命令格式中需要时使用
                    continue
                else:
                    placeholder = str(value)
                    formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', placeholder)
            else:
                # 参数名在模板中但解析结果中没有，移除占位符
                formatted_cmd = formatted_cmd.replace(f' {{{param_name}}}', '')
                formatted_cmd = formatted_cmd.replace(f'{{{param_name}}} ', '')
                formatted_cmd = formatted_cmd.replace(f' {{{param_name}}} ', '')
                formatted_cmd = formatted_cmd.replace(f'{{{param_name}}}', '')
        
        # 清理多余的空格
        formatted_cmd = ' '.join(formatted_cmd.split())
        
        return formatted_cmd
    
    def detect_source_interface(self, command_args: List[str]) -> Optional[str]:
        """根据命令参数自动检测源包管理器接口"""
        if not command_args:
            return None
        
        first_arg = command_args[0]
        
        if self.debug_mode:
            debug(f"自动检测源接口，第一个参数: '{first_arg}'")
        
        matches = []
        
        # 收集所有匹配的接口
        for interface_name, interface_config in self.config.get('action_interfaces', {}).items():
            triggers_config = interface_config.get('triggers', {})
            
            for rules_key, rules_config in triggers_config.items():
                if rules_key.endswith('_command'):
                    cmd_name = rules_config.get('cmd_name')
                    if cmd_name == first_arg:
                        matches.append(interface_name)
                        if self.debug_mode:
                            debug(f"找到匹配的源接口: {interface_name} (命令: {cmd_name})")
        
        # 处理匹配结果
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            warning(f"检测到多个包管理器都支持命令 '{first_arg}': {', '.join(matches)}")
            warning(f"请使用 -s/--source 选项明确指定源包管理器，例如:")
            warning(f"  actmap -s {matches[0]} map -- {first_arg} ...")
            return None
        else:
            return None