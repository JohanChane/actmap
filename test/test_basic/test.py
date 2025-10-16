#!/usr/bin/env python3

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug, info, success, error, debug


def test_basic():
    """基础功能测试"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    info(f"🧪 使用配置文件: {config_path}")
    print("=" * 60)
    
    try:
        # 设置调试模式
        set_debug(True)
        
        # 测试 ActMap 功能
        actmap = ActMap(config_path)
        actmap.set_debug(True)  # 启用 ActMap 的调试模式
        
        # 测试基本功能
        print("✅ ActMap 初始化成功")
        print(f"✅ 支持的动作: {actmap.get_supported_actions()}")
        print(f"✅ 支持的接口: {actmap.get_supported_interfaces()}")
        
        # 基础测试用例
        test_cases = [
            # (接口, 参数, 期望动作, 描述)
            ("pacman", ["vim"], "install", "基本安装"),
            ("pacman", ["-S", "vim"], "install", "带选项安装"),
            ("pacman", ["-Ss", "vim"], "search", "搜索包"),
            ("pacman", ["-s", "vim", "-S"], "search", "逆序搜索"),
            ("pacman", ["-Ss"], "search", "不指定参数"),
            ("pacman", ["-S"], "install", "不指定参数"),
            ("pacman", ["-Qs", "vim"], "search", "查询搜索"),
            ("pacman", ["-h"], "help", "帮助"),
            
            ("apt", ["install", "vim"], "install", "APT安装"),
            ("apt", ["install"], "install", "不指定参数"),
            ("apt", ["search", "vim"], "search", "APT搜索"),
            ("apt", ["search"], "search", "不指定参数"),
            ("apt", ["--help"], "help", "APT帮助"),
        ]
        
        print("\n🧪 基础功能测试:")
        passed = 0
        total = len(test_cases)
        
        for interface, args, expected_action, description in test_cases:
            print(f"\n  测试: {interface} {' '.join(args)} - {description}")
            
            try:
                # 解析参数
                parse_result = actmap.parse_arguments(interface, args)
                
                # 检测动作
                action = actmap.detect_action(interface, parse_result)
                
                # 验证结果
                if action == expected_action:
                    print(f"     ✅ 动作检测正确: {action}")
                    
                    # 测试命令映射
                    if action:
                        target = "apt" if interface == "pacman" else "pacman"
                        mapped_cmd = actmap.map_command(interface, target, action, parse_result)
                        print(f"     🔄 映射到 {target}: {mapped_cmd}")
                    
                    passed += 1
                else:
                    print(f"     ❌ 动作检测错误: 期望 {expected_action}, 得到 {action}")
                    
            except Exception as e:
                print(f"     ❌ 测试失败: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 基础测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有基础测试通过！")
        else:
            print("❌ 部分基础测试失败")
        
        return passed == total
        
    except Exception as e:
        error(f"❌ 基础测试失败: {e}")
        debug(f"详细错误: {str(e)}")
        return False


if __name__ == '__main__':
    test_basic()