#!/usr/bin/env python3

import sys
import os
import subprocess

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_cat_grep_commands():
    """测试 cat grep grep 文件搜索功能"""
    print("🧪 测试 cat grep grep 文件搜索功能")
    print("=" * 50)
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 使用专门的配置文件
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    # 测试案例
    # 第一列: 动作名称 (对应配置文件中的动作)
    # 第二列: 参数列表 (使用 == 分隔不同参数组)
    # 第三列: 期望输出
    # 第四列: 测试描述
    test_cases = [
        # === 单条件搜索 ===
        ("grep_single", ["log.txt", "==", "ERROR"], "cat log.txt | grep ERROR", "单文件单条件"),
        
        # === 双条件搜索 ===
        ("grep_double", ["access.log", "==", "ERROR", "==", "2024"], "cat access.log | grep ERROR | grep 2024", "单文件双条件"),
        ("grep_double", ["app.log", "==", "WARNING", "CRITICAL", "==", "nginx"], "cat app.log | grep WARNING CRITICAL | grep nginx", "单文件多值双条件"),
        
        # === 三条件搜索 ===
        ("grep_triple", ["server.log", "==", "ERROR", "==", "auth", "==", "failed"], "cat server.log | grep ERROR | grep auth | grep failed", "单文件三条件"),
        ("grep_triple", ["debug.log", "==", "DEBUG", "TRACE", "==", "module", "==", "init"], "cat debug.log | grep DEBUG TRACE | grep module | grep init", "单文件多值三条件"),
        
        # === 多文件搜索 ===
        ("grep_multi_files", ["log1.txt", "log2.txt", "log3.txt", "==", "ERROR"], "cat log1.txt log2.txt log3.txt | grep ERROR", "多文件单条件"),
        
        # === 复杂场景 ===
        ("grep_triple", ["/var/log/nginx/access.log", "==", "404", "500", "==", "POST", "==", "/api"], "cat /var/log/nginx/access.log | grep 404 500 | grep POST | grep /api", "复杂多条件搜索"),
        ("grep_triple", ["/var/log/syslog", "==", "kernel", "==", "error", "warning", "==", "memory"], "cat /var/log/syslog | grep kernel | grep error warning | grep memory", "复杂多值搜索"),
        
        # === 特殊字符搜索 ===
        ("grep_special_chars", ["code.py", "==", "if == xxx", "==", "def main()"], "cat code.py | grep if == xxx | grep def main()", "包含 == 的特殊字符串"),
        ("grep_special_chars", ["script.sh", "==", "grep == pattern", "==", "sed s/old/new/"], "cat script.sh | grep grep == pattern | grep sed s/old/new/", "包含特殊字符的模式"),
        ("grep_special_chars", ["config.txt", "==", "key=value", "==", "port == 8080"], "cat config.txt | grep key=value | grep port == 8080", "混合特殊字符"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for action_name, args, expected_output, description in test_cases:
        print(f"\n测试: {description}")
        print(f"     动作: {action_name}")
        
        # 构建完整的命令
        cmd = [
            sys.executable, "-m", "actmap.cli",
            "--config", config_path,
            "act", action_name
        ] + args
        
        cmd_str = " ".join(cmd[2:])
        print(f"     执行命令: {cmd_str}")
        print(f"     期望输出: {expected_output}")
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 检查结果
            output = result.stdout.strip()
            if expected_output == output:
                print(f"  ✅ 通过: {output}")
                passed += 1
            else:
                print(f"  ❌ 失败: 期望 '{expected_output}'")
                print(f"         得到 '{output}'")
                if result.stderr:
                    print(f"         错误: {result.stderr}")
                print(f"         返回码: {result.returncode}")
                    
        except subprocess.TimeoutExpired:
            print(f"  ❌ 超时: 命令执行超时")
        except Exception as e:
            print(f"  ❌ 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有 cat grep grep 测试通过！")
    else:
        print("❌ 部分测试失败")
        print(f"   成功率: {passed/total*100:.1f}%")
    
    return passed == total


def test_missing_parameters():
    """测试缺少参数的情况"""
    print("\n" + "=" * 50)
    print("🧪 测试缺少参数的情况")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    
    # 测试缺少参数的情况
    missing_param_cases = [
        ("grep_single", ["log.txt"], "缺少 pattern1 参数"),
        ("grep_double", ["file.txt", "==", "pattern"], "缺少 pattern2 参数"),
        ("grep_multi_files", ["file1.txt", "file2.txt"], "缺少 pattern1 参数"),
        ("grep_special_chars", ["code.py", "==", "if == xxx"], "缺少 pattern2 参数"),
    ]
    
    passed = 0
    total = len(missing_param_cases)
    
    for action_name, args, description in missing_param_cases:
        print(f"\n测试: {description}")
        
        cmd = [
            sys.executable, "-m", "actmap.cli",
            "--config", config_path,
            "act", action_name
        ] + args
        
        cmd_str = " ".join(cmd[2:])
        print(f"     执行命令: {cmd_str}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 检查是否报错（返回码非0）
            if result.returncode != 0 and "缺少必需参数" in result.stderr:
                print(f"  ✅ 通过: 正确报错")
                passed += 1
            else:
                print(f"  ❌ 失败: 应该报错但没有")
                print(f"         输出: {result.stdout}")
                print(f"         错误: {result.stderr}")
                print(f"         返回码: {result.returncode}")
                        
        except subprocess.TimeoutExpired:
            print(f"  ❌ 超时")
        except Exception as e:
            print(f"  ❌ 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 缺少参数测试结果: {passed}/{total} 通过")
    
    return passed == total


if __name__ == "__main__":
    success1 = test_cat_grep_commands()
    success2 = test_missing_parameters()
    
    final_success = success1 and success2
    print("\n" + "=" * 50)
    print("🎯 最终测试结果:")
    print(f"   正常功能: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"   错误处理: {'✅ 通过' if success2 else '❌ 失败'}")
    print(f"   总体: {'✅ 所有测试通过！' if final_success else '❌ 测试失败'}")
    
    sys.exit(0 if final_success else 1)