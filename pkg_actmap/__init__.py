"""
包管理器映射配置模块
"""

import tomllib
from pathlib import Path
from typing import Dict, Any


def load_package_config(package_name: str) -> Dict[str, Any]:
    """加载指定包管理器的配置"""
    config_path = Path(__file__).parent / f"{package_name}.toml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"包管理器配置不存在: {package_name}")
    
    with open(config_path, 'rb') as f:
        return tomllib.load(f)


def get_available_packages() -> list:
    """获取可用的包管理器列表"""
    pkg_dir = Path(__file__).parent
    return [f.stem for f in pkg_dir.glob("*.toml") if f.stem != "base"]


def merge_configs(base_config: Dict[str, Any], package_config: Dict[str, Any]) -> Dict[str, Any]:
    """合并基础配置和包管理器配置"""
    merged = base_config.copy()
    
    # 合并 actions
    if 'actions' in package_config:
        for action, action_config in package_config['actions'].items():
            if action in merged['actions']:
                merged['actions'][action].update(action_config)
            else:
                merged['actions'][action] = action_config
    
    # 合并 action_interfaces
    if 'action_interfaces' in package_config:
        merged['action_interfaces'].update(package_config['action_interfaces'])
    
    return merged