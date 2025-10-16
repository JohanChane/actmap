from typing import List, Dict, Any

from .parsers import GetoptParser, ArgparseParser


class ParserFactory:
    """解析器工厂"""
    
    @staticmethod
    def create_parser(parser_type: str, arg_parse_config: List[Dict[str, Any]]):
        if parser_type == "getopt":
            return GetoptParser(arg_parse_config)
        elif parser_type == "argparse":
            return ArgparseParser(arg_parse_config)
        else:
            raise ValueError(f"不支持的解析器类型: {parser_type}")