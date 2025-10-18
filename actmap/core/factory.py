from typing import List, Dict, Any

from .parsers import GetoptParser, ArgparseParser


class ParserFactory:
    """Parser Factory"""
    
    @staticmethod
    def create_parser(parser_type: str, arg_parse_config: List[Dict[str, Any]]):
        if parser_type == "getopt":
            return GetoptParser(arg_parse_config)
        elif parser_type == "argparse":
            return ArgparseParser(arg_parse_config)
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")