#!/usr/bin/env python3

import sys
import os

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug  # 添加这行导入


def run_actions_test(config_path):
    """运行扩展动作测试"""
    print(f"🧪 使用配置文件: {config_path}")
    print("=" * 60)
    
    try:
        # 设置调试模式
        set_debug(True)  # 启用全局调试模式
        
        actmap = ActMap(config_path)
        actmap.set_debug(True)  # 启用 ActMap 的调试模式
        
        # 测试基本功能
        print("✅ ActMap 初始化成功")
        print(f"✅ 支持的动作: {actmap.get_supported_actions()}")
        print(f"✅ 支持的接口: {actmap.get_supported_interfaces()}")
        
        # 扩展测试用例 - 测试所有动作
        test_cases = [
            # Pacman 测试用例
            ("pacman", ["-S", "vim", "git"], "install", "多包安装"),
            ("pacman", ["-R", "vim"], "remove", "卸载包"),
            ("pacman", ["-Sy"], "update", "更新数据库"),
            ("pacman", ["-Syu"], "upgrade", "系统升级"),
            ("pacman", ["-Si", "vim"], "info", "包信息"),
            ("pacman", ["-Q"], "list_installed", "列出已安装"),
            ("pacman", ["-Sc"], "clean", "清理缓存"),
            
            # APT 测试用例
            ("apt", ["remove", "vim"], "remove", "APT卸载"),
            ("apt", ["update"], "update", "APT更新"),
            ("apt", ["upgrade"], "upgrade", "APT升级"),
            ("apt", ["show", "vim"], "info", "APT包信息"),
            ("apt", ["list", "--installed"], "list_installed", "APT列出已安装"),
            ("apt", ["autoclean"], "clean", "APT清理缓存"),
            
            # Brew 测试用例
            ("brew", ["install", "vim"], "install", "Brew安装"),
            ("brew", ["uninstall", "vim"], "remove", "Brew卸载"),
            ("brew", ["update"], "update", "Brew更新"),
            ("brew", ["upgrade"], "upgrade", "Brew升级"),
            ("brew", ["search", "python"], "search", "Brew搜索"),
            ("brew", ["info", "vim"], "info", "Brew包信息"),
            ("brew", ["list"], "list_installed", "Brew列出已安装"),
            ("brew", ["cleanup"], "clean", "Brew清理缓存"),
            ("brew", ["--help"], "help", "Brew帮助"),
        ]
        
        print("\n🧪 扩展动作测试:")
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
                    
                    # 测试命令映射到其他包管理器
                    if action:
                        # 简单的目标选择逻辑
                        if interface == "pacman":
                            target = "apt"
                        elif interface == "apt":
                            target = "brew"
                        else:
                            target = "pacman"
                            
                        mapped_cmd = actmap.map_command(interface, target, action, parse_result)
                        print(f"     🔄 映射到 {target}: {mapped_cmd}")
                    
                    passed += 1
                else:
                    print(f"     ❌ 动作检测错误: 期望 {expected_action}, 得到 {action}")
                    
            except Exception as e:
                print(f"     ❌ 测试失败: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 扩展动作测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有扩展动作测试通过！")
        else:
            print("❌ 部分扩展动作测试失败")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ 扩展动作测试失败: {e}")
        return False

if __name__ == "__main__":
    # 使用测试目录下的配置文件
    config_path = os.path.join(os.path.dirname(__file__), "config.toml")
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    
    success = run_actions_test(config_path)
    sys.exit(0 if success else 1)