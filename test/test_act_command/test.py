#!/usr/bin/env python3

import sys
import os
import subprocess

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_cat_grep_commands():
    """Test cat grep grep file search functionality"""
    print("🧪 Testing cat grep grep file search functionality")
    print("=" * 50)
    
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Use dedicated configuration file
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file does not exist: {config_path}")
        return False
    
    # Test cases
    # Column 1: Action name (corresponds to action in configuration file)
    # Column 2: Parameter list (use == to separate different parameter groups)
    # Column 3: Expected output
    # Column 4: Test description
    test_cases = [
        # === Single condition search ===
        ("grep_single", ["log.txt", "==", "ERROR"], "cat log.txt | grep ERROR", "Single file single condition"),
        
        # === Double condition search ===
        ("grep_double", ["access.log", "==", "ERROR", "==", "2024"], "cat access.log | grep ERROR | grep 2024", "Single file double condition"),
        ("grep_double", ["app.log", "==", "WARNING", "CRITICAL", "==", "nginx"], "cat app.log | grep WARNING CRITICAL | grep nginx", "Single file multi-value double condition"),
        
        # === Triple condition search ===
        ("grep_triple", ["server.log", "==", "ERROR", "==", "auth", "==", "failed"], "cat server.log | grep ERROR | grep auth | grep failed", "Single file triple condition"),
        ("grep_triple", ["debug.log", "==", "DEBUG", "TRACE", "==", "module", "==", "init"], "cat debug.log | grep DEBUG TRACE | grep module | grep init", "Single file multi-value triple condition"),
        
        # === Multi-file search ===
        ("grep_multi_files", ["log1.txt", "log2.txt", "log3.txt", "==", "ERROR"], "cat log1.txt log2.txt log3.txt | grep ERROR", "Multi-file single condition"),
        
        # === Complex scenarios ===
        ("grep_triple", ["/var/log/nginx/access.log", "==", "404", "500", "==", "POST", "==", "/api"], "cat /var/log/nginx/access.log | grep 404 500 | grep POST | grep /api", "Complex multi-condition search"),
        ("grep_triple", ["/var/log/syslog", "==", "kernel", "==", "error", "warning", "==", "memory"], "cat /var/log/syslog | grep kernel | grep error warning | grep memory", "Complex multi-value search"),
        
        # === Special character search ===
        ("grep_special_chars", ["code.py", "==", "if == xxx", "==", "def main()"], "cat code.py | grep if == xxx | grep def main()", "Special strings containing =="),
        ("grep_special_chars", ["script.sh", "==", "grep == pattern", "==", "sed s/old/new/"], "cat script.sh | grep grep == pattern | grep sed s/old/new/", "Patterns containing special characters"),
        ("grep_special_chars", ["config.txt", "==", "key=value", "==", "port == 8080"], "cat config.txt | grep key=value | grep port == 8080", "Mixed special characters"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for action_name, args, expected_output, description in test_cases:
        print(f"\nTest: {description}")
        print(f"     Action: {action_name}")
        
        # Build complete command
        cmd = [
            sys.executable, "-m", "actmap.cli",
            "--config", config_path,
            "act", action_name
        ] + args
        
        cmd_str = " ".join(cmd[2:])
        print(f"     Executing command: {cmd_str}")
        print(f"     Expected output: {expected_output}")
        
        try:
            # Execute command
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check result
            output = result.stdout.strip()
            if expected_output == output:
                print(f"  ✅ Passed: {output}")
                passed += 1
            else:
                print(f"  ❌ Failed: expected '{expected_output}'")
                print(f"         got '{output}'")
                if result.stderr:
                    print(f"         error: {result.stderr}")
                print(f"         return code: {result.returncode}")
                    
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout: command execution timed out")
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All cat grep grep tests passed!")
    else:
        print("❌ Some tests failed")
        print(f"   Success rate: {passed/total*100:.1f}%")
    
    return passed == total


if __name__ == "__main__":
    success = test_cat_grep_commands()
    
    print("\n" + "=" * 50)
    print("🎯 Final test results:")
    print(f"   Normal functionality: {'✅ Passed' if success else '❌ Failed'}")
    print(f"   Overall: {'✅ All tests passed!' if success else '❌ Tests failed'}")
    
    sys.exit(0 if success else 1)