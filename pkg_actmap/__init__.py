"""
Package Manager Mapping Configuration Module
"""

import tomllib
from pathlib import Path
from typing import Dict, Any


def load_package_config(package_name: str) -> Dict[str, Any]:
    """Load configuration for specified package manager"""
    config_path = Path(__file__).parent / f"{package_name}.toml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Package manager configuration does not exist: {package_name}")
    
    with open(config_path, 'rb') as f:
        return tomllib.load(f)


def get_available_packages() -> list:
    """Get available package manager list"""
    pkg_dir = Path(__file__).parent
    return [f.stem for f in pkg_dir.glob("*.toml") if f.stem != "base"]


def merge_configs(base_config: Dict[str, Any], package_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge base configuration and package manager configuration"""
    merged = base_config.copy()
    
    # Merge actions
    if 'actions' in package_config:
        for action, action_config in package_config['actions'].items():
            if action in merged['actions']:
                merged['actions'][action].update(action_config)
            else:
                merged['actions'][action] = action_config
    
    # Merge action_interfaces
    if 'action_interfaces' in package_config:
        merged['action_interfaces'].update(package_config['action_interfaces'])
    
    return merged