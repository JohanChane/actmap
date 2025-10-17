#!/usr/bin/env python3

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug, info, success, error, debug


def test_dnf_rpm_pacman_mapping():
    """测试 DNF/RPM 和 Pacman 之间的复杂命令映射"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    info(f"🧪 使用配置文件: {config_path}")
    print("=" * 80)
    
    try:
        # 设置调试模式
        set_debug(True)
        
        # 测试 ActMap 功能
        actmap = ActMap(config_path)
        actmap.set_debug(True)
        
        # 测试基本功能
        print("✅ ActMap 初始化成功")
        print(f"✅ 支持的动作: {actmap.get_supported_actions()}")
        print(f"✅ 支持的接口: {actmap.get_supported_interfaces()}")
        
        # 复杂映射测试用例 - 专注于文件相关操作
        # 列说明:
        # 第1列: 源接口 - 使用哪个包管理器的配置解析命令
        # 第2列: 源命令 - 实际的命令行参数列表
        # 第3列: 目标接口 - 映射到哪个包管理器  
        # 第4列: 期望参数 - 期望在目标命令中出现的参数值
        # 第5列: 描述 - 测试用例的人类可读描述
        test_cases = [
            # ==================== DNF/RPM → Pacman 映射 ====================
            # 文件相关操作 - 重点测试参数映射
            ("dnf", ["dnf", "provides", "/usr/bin/vim"], "pacman", ["/usr/bin/vim"], "DNF远程文件查找→Pacman"),
            ("dnf", ["rpm", "-qf", "/usr/bin/bash"], "pacman", ["/usr/bin/bash"], "RPM本地文件查找→Pacman"),
            ("dnf", ["rpm", "-ql", "vim"], "pacman", ["vim"], "RPM文件列表→Pacman"),
            ("dnf", ["rpm", "-qi", "git"], "pacman", ["git"], "RPM包信息→Pacman"),
            ("dnf", ["dnf", "search", "editor"], "pacman", ["editor"], "DNF搜索→Pacman"),
            ("dnf", ["dnf", "info", "kernel"], "pacman", ["kernel"], "DNF包信息→Pacman"),
            
            # ==================== Pacman → DNF/RPM 映射 ====================
            # 文件相关操作 - 重点测试参数映射
            ("pacman", ["pacman", "-F", "/usr/bin/gcc"], "dnf", ["/usr/bin/gcc"], "Pacman远程文件查找→DNF"),
            ("pacman", ["pacman", "-Qo", "/usr/bin/python"], "dnf", ["/usr/bin/python"], "Pacman本地文件查找→RPM"),
            ("pacman", ["pacman", "-Ql", "git"], "dnf", ["git"], "Pacman文件列表→RPM"),
            ("pacman", ["pacman", "-Si", "firefox"], "dnf", ["firefox"], "Pacman包信息→DNF"),
            ("pacman", ["pacman", "-Ss", "browser"], "dnf", ["browser"], "Pacman搜索→DNF"),
        ]
        
        print("\n🧪 DNF/RPM ↔ Pacman 文件操作映射测试:")
        print("📋 列说明:")
        print("  第1列: 源接口 (解析器选择)")
        print("  第2列: 源命令 (实际参数)") 
        print("  第3列: 目标接口 (映射目标)")
        print("  第4列: 期望参数 (验证值)")
        print("  第5列: 描述")
        print("-" * 80)
        
        passed = 0
        total = len(test_cases)
        
        for source_interface, source_args, target_interface, expected_values, description in test_cases:
            print(f"\n  🧪 {description}")
            print(f"     📥 输入: {' '.join(source_args)}")
            print(f"     🎯 目标: {target_interface}")
            
            try:
                # 解析源命令参数
                parse_result = actmap.parse_arguments(source_interface, source_args)
                
                # 检测动作
                action = actmap.detect_action(source_interface, parse_result)
                
                if action:
                    print(f"     🔍 检测动作: {action}")
                    
                    # 执行命令映射
                    mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)
                    print(f"     🔄 映射命令: {mapped_command}")
                    
                    # 检测参数是否生效
                    success = True
                    missing_values = []
                    
                    # 检查期望的值是否出现在映射后的命令中
                    for value in expected_values:
                        if value not in mapped_command:
                            missing_values.append(value)
                            success = False
                    
                    if success:
                        print(f"     ✅ 验证成功: 所有参数正确映射")
                        passed += 1
                    else:
                        print(f"     ❌ 验证失败: 参数 {missing_values} 未出现在目标命令中")
                        
                else:
                    print(f"     ❌ 动作检测失败")
                    print(f"       解析结果: {parse_result}")
                    
            except Exception as e:
                print(f"     ❌ 测试异常: {e}")
        
        print("\n" + "=" * 80)
        print(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有文件操作映射测试通过！")
        else:
            print("❌ 部分测试失败")
        
        return passed == total
        
    except Exception as e:
        error(f"❌ 文件操作映射测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_dnf_rpm_pacman_mapping()