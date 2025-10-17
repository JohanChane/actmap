#!/usr/bin/env python3

import sys
import os

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug  # 添加这行导入


def run_repeatable_test(config_path):
    """运行重复选项测试"""
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
        
        # 重复选项测试用例 - 包含命令名
        test_cases = [
            # Pacman 重复选项测试
            ("pacman", ["pacman", "-Syy"], "force_update", "强制更新数据库"),
            ("pacman", ["pacman", "-Syyu"], "force_upgrade", "强制更新并升级"),
            ("pacman", ["pacman", "-Sy"], "update", "普通更新数据库"),
            ("pacman", ["pacman", "-Syu"], "upgrade", "普通升级"),
            
            # APT 区分测试
            ("apt", ["apt", "update"], "update", "普通更新"),
            ("apt", ["apt", "update", "--refresh-all"], "force_update", "强制更新"),
            ("apt", ["apt", "upgrade"], "upgrade", "普通升级"),
        ]
        
        print("\n🧪 重复选项测试:")
        passed = 0
        total = len(test_cases)
        
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
                    
                    # 检查 y 参数的重复次数（对于 pacman）
                    if interface == "pacman" and 'y' in parse_result['present_params']:
                        y_param = parse_result['present_params']['y']
                        repeat_count = y_param['value']
                        print(f"     🔢 y参数重复次数: {repeat_count}")
                    
                    # 测试命令映射
                    if action:
                        # Pacman 映射到 APT，APT 映射到 Pacman
                        target = "apt" if interface == "pacman" else "pacman"
                        try:
                            mapped_cmd = actmap.map_command(interface, target, action, parse_result)
                            print(f"     🔄 映射到 {target}: {mapped_cmd}")
                        except Exception as map_e:
                            print(f"     ⚠️  映射失败: {map_e}")
                    
                    passed += 1
                else:
                    print(f"     ❌ 动作检测错误: 期望 {expected_action}, 得到 {action}")
                    # 输出调试信息
                    print(f"       解析结果: {parse_result}")
                    
            except Exception as e:
                print(f"     ❌ 测试失败: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 重复选项测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有重复选项测试通过！")
        else:
            print("❌ 部分重复选项测试失败")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ 重复选项测试失败: {e}")
        return False

if __name__ == "__main__":
    # 使用测试目录下的配置文件
    config_path = os.path.join(os.path.dirname(__file__), "config.toml")
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    
    # 运行重复选项测试
    success = run_repeatable_test(config_path)
    
    sys.exit(0 if success else 1)