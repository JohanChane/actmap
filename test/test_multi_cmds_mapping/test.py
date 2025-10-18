#!/usr/bin/env python3

import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from actmap.core.actmap import ActMap
from actmap.log import set_debug, info, success, error, debug


def test_dnf_rpm_pacman_mapping():
    """Test complex command mapping between DNF/RPM and Pacman"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
    info(f"🧪 Using configuration file: {config_path}")
    print("=" * 80)
    
    try:
        # Set debug mode
        set_debug(True)
        
        # Test ActMap functionality
        actmap = ActMap(config_path)
        actmap.set_debug(True)
        
        # Test basic functionality
        print("✅ ActMap initialization successful")
        print(f"✅ Supported actions: {actmap.get_supported_actions()}")
        print(f"✅ Supported interfaces: {actmap.get_supported_interfaces()}")
        
        # Complex mapping test cases - focusing on file-related operations
        # Column descriptions:
        # Column 1: Source interface - which package manager's configuration to use for parsing commands
        # Column 2: Source command - actual command line arguments list
        # Column 3: Target interface - which package manager to map to
        # Column 4: Expected parameters - parameter values expected to appear in target command
        # Column 5: Description - human-readable description of test case
        test_cases = [
            # ==================== DNF/RPM → Pacman mapping ====================
            # File-related operations - focus on parameter mapping
            ("dnf", ["dnf", "provides", "/usr/bin/vim"], "pacman", ["/usr/bin/vim"], "DNF remote file lookup → Pacman"),
            ("dnf", ["rpm", "-qf", "/usr/bin/bash"], "pacman", ["/usr/bin/bash"], "RPM local file lookup → Pacman"),
            ("dnf", ["rpm", "-ql", "vim"], "pacman", ["vim"], "RPM file list → Pacman"),
            ("dnf", ["rpm", "-qi", "git"], "pacman", ["git"], "RPM package info → Pacman"),
            ("dnf", ["dnf", "search", "editor"], "pacman", ["editor"], "DNF search → Pacman"),
            ("dnf", ["dnf", "info", "kernel"], "pacman", ["kernel"], "DNF package info → Pacman"),
            
            # ==================== Pacman → DNF/RPM mapping ====================
            # File-related operations - focus on parameter mapping
            ("pacman", ["pacman", "-F", "/usr/bin/gcc"], "dnf", ["/usr/bin/gcc"], "Pacman remote file lookup → DNF"),
            ("pacman", ["pacman", "-Qo", "/usr/bin/python"], "dnf", ["/usr/bin/python"], "Pacman local file lookup → RPM"),
            ("pacman", ["pacman", "-Ql", "git"], "dnf", ["git"], "Pacman file list → RPM"),
            ("pacman", ["pacman", "-Si", "firefox"], "dnf", ["firefox"], "Pacman package info → DNF"),
            ("pacman", ["pacman", "-Ss", "browser"], "dnf", ["browser"], "Pacman search → DNF"),
        ]
        
        print("\n🧪 DNF/RPM ↔ Pacman file operation mapping test:")
        print("📋 Column descriptions:")
        print("  Column 1: Source interface (parser selection)")
        print("  Column 2: Source command (actual parameters)") 
        print("  Column 3: Target interface (mapping target)")
        print("  Column 4: Expected parameters (validation values)")
        print("  Column 5: Description")
        print("-" * 80)
        
        passed = 0
        total = len(test_cases)
        
        for source_interface, source_args, target_interface, expected_values, description in test_cases:
            print(f"\n  🧪 {description}")
            print(f"     📥 Input: {' '.join(source_args)}")
            print(f"     🎯 Target: {target_interface}")
            
            try:
                # Parse source command parameters
                parse_result = actmap.parse_arguments(source_interface, source_args)
                
                # Detect action
                action = actmap.detect_action(source_interface, parse_result)
                
                if action:
                    print(f"     🔍 Detected action: {action}")
                    
                    # Execute command mapping
                    mapped_command = actmap.map_command(source_interface, target_interface, action, parse_result)
                    print(f"     🔄 Mapped command: {mapped_command}")
                    
                    # Check if parameters are effective
                    test_success = True
                    missing_values = []
                    
                    # Check if expected values appear in mapped command
                    for value in expected_values:
                        if value not in mapped_command:
                            missing_values.append(value)
                            test_success = False
                    
                    if test_success:
                        print(f"     ✅ Validation successful: all parameters correctly mapped")
                        passed += 1
                    else:
                        print(f"     ❌ Validation failed: parameters {missing_values} not found in target command")
                        
                else:
                    print(f"     ❌ Action detection failed")
                    print(f"       Parse result: {parse_result}")
                    
            except Exception as e:
                print(f"     ❌ Test exception: {e}")
        
        print("\n" + "=" * 80)
        print(f"📊 Test results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All file operation mapping tests passed!")
        else:
            print("❌ Some tests failed")
        
        return passed == total
        
    except Exception as e:
        error(f"❌ File operation mapping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_dnf_rpm_pacman_mapping()