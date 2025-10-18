import tomllib
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration file"""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file {config_path} does not exist")
    
    with open(config_path, 'rb') as f:
        return tomllib.load(f)