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
        """根据配置解析参数"""
        interface_config = self.config.get('action_interfaces', {}).get(interface, {})
        args_config = interface_config.get('args', {})
        arg_parse_config = args_config.get('arg_parse', [])
        parser_type = args_config.get('arg_parser', 'getopt')
        
        debug(f"💡 参数解析:")
        debug(f"   接口: {interface}")
        debug(f"   解析器: {parser_type}")
        debug(f"   原始参数: {command_args}")
        
        try:
            parser = ParserFactory.create_parser(parser_type, arg_parse_config)
            result = parser.parse(command_args)
            
            debug(f"   解析结果: {result}")
            return result
            
        except Exception as e:
            error(f"   解析错误: {e}")
            return {'parsed_kwargs': {}, 'present_params': {}}
    
    def detect_action(self, interface: str, parse_result: Dict[str, Any]) -> Optional[str]:
        """检测动作，如果没有匹配返回 None"""
        interface_config = self.config.get('action_interfaces', {}).get(interface, {})
        triggers_config = interface_config.get('triggers', {})
        rules = triggers_config.get('rules', [])
        
        present_params = parse_result['present_params']
        
        debug(f"🔍 动作检测:")
        debug(f"   接口: {interface}")
        debug(f"   出现的参数: {list(present_params.keys())}")
        
        for rule in rules:
            rule_name = rule.get('name', '未知规则')
            condition = rule.get('condition', {})
            triggers = rule.get('trigger', [])
            
            debug(f"   检查规则: {rule_name}")
            
            if self._check_condition(condition, present_params):
                debug(f"     ✅ 基础条件满足")
                
                for trigger in triggers:
                    trigger_params = trigger.get('params', [])
                    action = trigger.get('action')
                    
                    if self._check_condition({'params': trigger_params}, present_params):
                        debug(f"     🎯 触发动作: {action}")
                        return action
            
            else:
                debug(f"     ❌ 基础条件不满足")
        
        debug(f"⚠️  未匹配任何规则")
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