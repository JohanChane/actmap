#!/usr/bin/env python3

import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug  # Add this import


def run_repeatable_test(config_path):
    """Run repeatable option tests"""
    print(f"🧪 Using configuration file: {config_path}")
    print("=" * 60)
    
    try:
        # Set debug mode
        set_debug(True)  # Enable global debug mode
        
        actmap = ActMap(config_path)
        actmap.set_debug(True)  # Enable ActMap debug mode
        
        # Test basic functionality
        print("✅ ActMap initialization successful")
        print(f"✅ Supported actions: {actmap.get_supported_actions()}")
        print(f"✅ Supported interfaces: {actmap.get_supported_interfaces()}")
        
        # Repeatable option test cases - include command names
        test_cases = [
            # Pacman repeatable option tests
            ("pacman", ["pacman", "-Syy"], "force_update", "Force update database"),
            ("pacman", ["pacman", "-Syyu"], "force_upgrade", "Force update and upgrade"),
            ("pacman", ["pacman", "-Sy"], "update", "Normal update database"),
            ("pacman", ["pacman", "-Syu"], "upgrade", "Normal upgrade"),
            
            # APT differentiation tests
            ("apt", ["apt", "update"], "update", "Normal update"),
            ("apt", ["apt", "update", "--refresh-all"], "force_update", "Force update"),
            ("apt", ["apt", "upgrade"], "upgrade", "Normal upgrade"),
        ]
        
        print("\n🧪 Repeatable option tests:")
        passed = 0
        total = len(test_cases)
        
        for interface, full_args, expected_action, description in test_cases:
            print(f"\n  Test: {' '.join(full_args)} - {description}")
            
            try:
                # Parse arguments - pass complete arguments (including command name)
                parse_result = actmap.parse_arguments(interface, full_args)
                
                # Detect action
                action = actmap.detect_action(interface, parse_result)
                
                # Verify result
                if action == expected_action:
                    print(f"     ✅ Action detection correct: {action}")
                    
                    # Check y parameter repeat count (for pacman)
                    if interface == "pacman" and 'y' in parse_result['present_params']:
                        y_param = parse_result['present_params']['y']
                        repeat_count = y_param['value']
                        print(f"     🔢 y parameter repeat count: {repeat_count}")
                    
                    # Test command mapping
                    if action:
                        # Pacman maps to APT, APT maps to Pacman
                        target = "apt" if interface == "pacman" else "pacman"
                        try:
                            mapped_cmd = actmap.map_command(interface, target, action, parse_result)
                            print(f"     🔄 Mapped to {target}: {mapped_cmd}")
                        except Exception as map_e:
                            print(f"     ⚠️  Mapping failed: {map_e}")
                    
                    passed += 1
                else:
                    print(f"     ❌ Action detection error: expected {expected_action}, got {action}")
                    # Output debug information
                    print(f"       Parse result: {parse_result}")
                    
            except Exception as e:
                print(f"     ❌ Test failed: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Repeatable option test results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All repeatable option tests passed!")
        else:
            print("❌ Some repeatable option tests failed")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Repeatable option test failed: {e}")
        return False

if __name__ == "__main__":
    # Use configuration file in test directory
    config_path = os.path.join(os.path.dirname(__file__), "config.toml")
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file does not exist: {config_path}")
        sys.exit(1)
    
    # Run repeatable option tests
    success = run_repeatable_test(config_path)
    
    sys.exit(0 if success else 1)