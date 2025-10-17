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
        
        # 基础测试用例 - 保留原有的测试案例
        test_cases = [
            # (接口, 完整参数, 期望动作, 描述)
            ("pacman", ["pacman", "vim"], "install", "基本安装"),
            ("pacman", ["pacman", "-S", "vim"], "install", "带选项安装"),
            ("pacman", ["pacman", "-Ss", "vim"], "search", "搜索包"),
            ("pacman", ["pacman", "-s", "vim", "-S"], "search", "逆序搜索"),
            ("pacman", ["pacman", "-Ss"], "search", "不指定参数"),
            ("pacman", ["pacman", "-S"], "install", "不指定参数"),
            ("pacman", ["pacman", "-Qs", "vim"], "search", "查询搜索"),
            ("pacman", ["pacman", "-h"], "help", "帮助"),
            
            ("apt", ["apt", "install", "vim"], "install", "APT安装"),
            ("apt", ["apt", "install"], "install", "不指定参数"),
            ("apt", ["apt", "search", "vim"], "search", "APT搜索"),
            ("apt", ["apt", "search"], "search", "不指定参数"),
            ("apt", ["apt", "--help"], "help", "APT帮助"),
        ]
        
        print("\n🧪 基础功能测试:")
        passed_basic = 0
        total_basic = len(test_cases)
        
        for interface, full_args, expected_action, description in test_cases:
            print(f"\n  测试: {' '.join(full_args)} - {description}")
            
            try:
                # 解析参数 - 传递完整参数（包含命令名）
                parse_result = actmap.parse_arguments(interface, full_args)
                
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
                    
                    passed_basic += 1
                else:
                    print(f"     ❌ 动作检测错误: 期望 {expected_action}, 得到 {action}")
                    
            except Exception as e:
                print(f"     ❌ 测试失败: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 基础测试结果: {passed_basic}/{total_basic} 通过")
        
        if passed_basic == total_basic:
            print("🎉 所有基础测试通过！")
        else:
            print("❌ 部分基础测试失败")
        
        # 新增：参数映射专项测试
        print("\n" + "=" * 60)
        test_parameter_mapping(actmap)
        
        return passed_basic == total_basic
        
    except Exception as e:
        error(f"❌ 基础测试失败: {e}")
        debug(f"详细错误: {str(e)}")
        return False


def test_parameter_mapping(actmap):
    """参数映射专项测试"""
    print("🧪 参数映射专项测试:")
    
    # 参数映射测试用例 - 重点测试有参数的命令
    mapping_cases = [
        # (源接口, 源命令, 目标接口, 期望包含的包名, 描述)
        ("pacman", ["pacman", "-S", "vim", "git"], "apt", ["vim", "git"], "Pacman安装映射到APT"),
        ("pacman", ["pacman", "-Ss", "python"], "apt", ["python"], "Pacman搜索映射到APT"),
        ("apt", ["apt", "install", "vim", "git"], "pacman", ["vim", "git"], "APT安装映射到Pacman"),
        ("apt", ["apt", "search", "python"], "pacman", ["python"], "APT搜索映射到Pacman"),
        ("pacman", ["pacman", "-S"], "apt", [], "Pacman安装无参数"),
        ("apt", ["apt", "install"], "pacman", [], "APT安装无参数"),
    ]
    
    passed_mapping = 0
    total_mapping = len(mapping_cases)
    
    for source_interface, source_args, target_interface, expected_packages, description in mapping_cases:
        print(f"\n  测试: {' '.join(source_args)} -> {target_interface} - {description}")
        
        try:
            # 解析源命令参数
            parse_result = actmap.parse_arguments(source_interface, source_args)
            
            # 检测动作
            action = actmap.detect_action(source_interface, parse_result)
            
            if action:
                print(f"     🎯 检测到动作: {action}")
                
                # 执行命令映射
                mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)
                print(f"     🔄 映射命令: {mapped_command}")
                
                # 检测参数是否生效
                success = True
                missing_packages = []
                
                # 检查期望的包名是否出现在映射后的命令中
                for package in expected_packages:
                    if package not in mapped_command:
                        missing_packages.append(package)
                        success = False
                
                if success:
                    if expected_packages:
                        print(f"     ✅ 参数映射成功: 所有包名都出现在目标命令中")
                    else:
                        print(f"     ✅ 参数映射成功: 无参数命令映射正确")
                    passed_mapping += 1
                else:
                    print(f"     ❌ 参数映射失败: 包名 {missing_packages} 未出现在目标命令中")
                    print(f"       映射命令: {mapped_command}")
                    
            else:
                print(f"     ❌ 未检测到动作")
                
        except Exception as e:
            print(f"     ❌ 测试失败: {e}")
            import traceback
            print(f"       详细错误: {traceback.format_exc()}")
    
    print("\n" + "=" * 60)
    print(f"📊 参数映射测试结果: {passed_mapping}/{total_mapping} 通过")
    
    if passed_mapping == total_mapping:
        print("🎉 所有参数映射测试通过！")
    else:
        print("❌ 部分参数映射测试失败")


if __name__ == '__main__':
    test_basic()