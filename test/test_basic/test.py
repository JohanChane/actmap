#!/usr/bin/env python3

import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug, info, success, error, debug


def test_basic():
    """Basic functionality test"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    info(f"🧪 Using configuration file: {config_path}")
    print("=" * 60)
    
    try:
        # Set debug mode
        set_debug(True)
        
        # Test ActMap functionality
        actmap = ActMap(config_path)
        actmap.set_debug(True)  # Enable ActMap debug mode
        
        # Test basic functionality
        print("✅ ActMap initialization successful")
        print(f"✅ Supported actions: {actmap.get_supported_actions()}")
        print(f"✅ Supported interfaces: {actmap.get_supported_interfaces()}")
        
        # Basic test cases - updated expected values
        test_cases = [
            # (interface, full_args, expected_action, description)
            ("pacman", ["pacman", "vim"], "install", "Basic installation"),
            ("pacman", ["pacman", "-S", "vim"], "install", "Installation with options"),
            ("pacman", ["pacman", "-Ss", "vim"], "search", "Search package"),
            ("pacman", ["pacman", "-s", "vim", "-S"], "search", "Reverse order search"),
            ("pacman", ["pacman", "-Ss"], None, "No parameters specified"),  # Modified: expect None
            ("pacman", ["pacman", "-S"], None, "No parameters specified"),   # Modified: expect None
            ("pacman", ["pacman", "-Qs", "vim"], "search", "Query search"),
            ("pacman", ["pacman", "-h"], "help", "Help"),
            
            ("apt", ["apt", "install", "vim"], "install", "APT installation"),
            ("apt", ["apt", "install"], None, "No parameters specified"),    # Modified: expect None
            ("apt", ["apt", "search", "vim"], "search", "APT search"),
            ("apt", ["apt", "search"], None, "No parameters specified"),     # Modified: expect None
            ("apt", ["apt", "--help"], "help", "APT help"),
        ]
        
        print("\n🧪 Basic functionality tests:")
        passed_basic = 0
        total_basic = len(test_cases)
        
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
                    
                    # Test command mapping (only when action exists)
                    if action:
                        target = "apt" if interface == "pacman" else "pacman"
                        mapped_cmd = actmap.map_command(interface, target, action, parse_result)
                        print(f"     🔄 Mapped to {target}: {mapped_cmd}")
                    else:
                        print(f"     ⏭️  No action, skipping mapping test")
                    
                    passed_basic += 1
                else:
                    print(f"     ❌ Action detection error: expected {expected_action}, got {action}")
                    
            except Exception as e:
                print(f"     ❌ Test failed: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Basic test results: {passed_basic}/{total_basic} passed")
        
        if passed_basic == total_basic:
            print("🎉 All basic tests passed!")
        else:
            print("❌ Some basic tests failed")
        
        return passed_basic == total_basic
        
    except Exception as e:
        error(f"❌ Basic test failed: {e}")
        debug(f"Detailed error: {str(e)}")
        return False


if __name__ == '__main__':
    test_basic()