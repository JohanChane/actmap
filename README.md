# ActMap - Intelligent Command Mapping Tool

A powerful command-line tool for intelligently mapping commands between different package managers. Allows you to use familiar package manager syntax on any system!

## Languages

[中文](./README_ZH.md)

## Project Status

Currently under development, it's a work in progress. Many things are not yet finalized, and significant changes may occur later.

## 🌟 Features

- **Multi-Package Manager Support**: pacman, apt, dnf, brew, zypper
- **Intelligent Command Parsing**: Automatically recognizes command intent (install, search, update, etc.)
- **Flexible Mapping**: Maps commands from any package manager to a target package manager
- **Safe Execution**: Interactive confirmation and force execution modes
- **Easy Extensibility**: Modular design based on configuration files (command mapping implemented via configuration)
- **Detailed Debugging**: Rich log output and debug information

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/your-username/actmap.git
cd actmap
pip install -e .
```

### Basic Usage

```bash
# Initialize user configuration (first-time use)
actmap-generate --init-config

# Configure ~/.config/actmap/config.toml
default_target_action = "<your system's package manager>"  # Default target package manager

# Map apt command to default target (default_target_action from config file)
actmap map -- apt install vim git
# If default_target_action = "pacman", outputs: pacman -S vim git

# Map pacman command to default target
actmap map -- pacman -Syu
# If default_target_action = "apt", outputs: apt update && apt upgrade

# Directly execute the mapped command (using default target)
actmap-execute -- apt search python

# View mapping configuration
actmap map --output-actmap pacman apt
```

## 📖 Detailed Usage

### Command Mapping

```bash
# Basic syntax
actmap map [options] -- <source command>

# Map using default target (read from config file)
actmap map -- apt install vim
actmap map -- pacman -S vim
actmap map --debug -- apt remove python3

# Specify target package manager (overrides default configuration)
actmap map -t apt -- pacman -S vim
# Output: apt install vim

actmap map -t dnf -- apt update
# Output: dnf check-update

actmap map -t brew -- pacman -Ss editor
# Output: brew search editor

# Specify configuration file
actmap map --config my_config.toml -t apt -- pacman -S vim
```

### Direct Execution

```bash
# Execute using default target
actmap-execute -- apt install vim

# Interactive execution (recommended for dangerous operations)
actmap-execute -i -- pacman -Rns vim

# Force execution (skip confirmation)
actmap-execute -f -- apt remove python3

# Debug mode
actmap-execute -d -- apt search python

# Specify target package manager
actmap-execute -t pacman -- apt update
actmap-execute -t dnf -- brew install git
```

### Configuration Management

```bash
# Initialize user configuration (creates ~/.config/actmap/)
actmap-generate --init-config

# Generate custom configuration file
actmap-generate -o custom.toml -m pacman -m apt -m dnf

# View supported package managers
actmap-generate --list-actmaps
```

## 🔧 Configuration Explanation

ActMap uses TOML configuration files to define package manager behavior. The default configuration file is located at `~/.config/actmap/config.toml`.

### Default Target Configuration
```toml
[config]
default_target_action = "pacman"  # Default target package manager
```

### Action Definition Example
```toml
[actions.install]
description = "Install packages"
args = ["pkgs"]

[actions.install.pacman]
cmd_format = "pacman -S {pkgs}"

[actions.install.apt]
cmd_format = "apt install {pkgs}"

[actions.install.dnf]
cmd_format = "dnf install {pkgs}"
```

### Configuration Priority
1. Command line `-t/--target` option (highest priority)
2. `default_target_action` in configuration file
3. Default value `pacman` (lowest priority)

## 🎯 Usage Examples

### Scenario 1: Using apt habits on Arch Linux
```bash
# Configure default_target_action = "pacman"
actmap map -- apt install vim git
# Output: pacman -S vim git

actmap map -- apt search python
# Output: pacman -Ss python

actmap map -- apt update
# Output: pacman -Sy
```

### Scenario 2: Using pacman habits on Ubuntu
```bash
# Configure default_target_action = "apt"
actmap map -- pacman -S vim
# Output: apt install vim

actmap map -- pacman -Syu
# Output: apt update && apt upgrade

actmap map -- pacman -Ss editor
# Output: apt search editor
```

### Scenario 3: Temporarily switching targets
```bash
# Temporarily map to a different target
actmap map -t dnf -- apt install vim
# Output: dnf install vim

actmap map -t brew -- pacman -S git
# Output: brew install git
```

## 🗂️ Project Structure

```
actmap/
├── actmap/                 # Core modules
│   ├── core/              # Core engine
│   │   ├── actmap.py      # Main mapping class
│   │   ├── factory.py     # Parser factory
│   │   └── parsers/       # Argument parsers
│   ├── config/            # Configuration loading
│   └── cli.py             # Command-line interface
├── pkg_actmap/            # Package manager configurations
│   ├── actmap_config/     # Individual package manager configs
│   │   ├── pacman.toml
│   │   ├── apt.toml
│   │   └── ...
│   └── generate_config.py # Configuration generation tool
├── test/                  # Test suite
│   ├── test_basic/        # Basic functionality tests
│   ├── test_actions/      # Action tests
│   └── test_repeats/      # Repeat option tests
└── config.toml           # Main configuration file
```

## 🔍 Currently Configured Package Managers

| Package Manager | System | Status |
|---------|------|------|
| Pacman | Arch Linux | ✅ Fully Supported |
| APT | Debian/Ubuntu | ✅ Fully Supported |
| DNF | Fedora | ✅ Fully Supported |
| Brew | macOS | ✅ Fully Supported |
| Zypper | openSUSE | ✅ Fully Supported |

Command mapping is implemented based on configuration. If you understand ActMap's command mapping configuration, it can theoretically support any package manager.

## 🛠️ Development

### Adding New Package Managers

1. Create a new `.toml` file in `pkg_actmap/actmap_config/`
2. Define command formats and parsing rules
3. Add trigger rules
4. Test the new configuration

### Running Tests

```bash
# Run all tests
python test/test_basic/test.py
python test/test_actions/test.py  
python test/test_repeats/test.py

# Debug mode
python -m actmap.cli -d map -- apt install vim
```

### Debugging Tips

```bash
# Enable debug output
actmap -d map -- apt install vim

# View detailed parsing process
actmap -d map -- pacman -Syyu

# View mapping relationships
actmap map --output-actmap apt pacman
```