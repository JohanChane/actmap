import tomllib
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: Path) -> Dict[str, Any]:
    """加载配置文件"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")
    
    with open(config_path, 'rb') as f:
        return tomllib.load(f)