# ActMap - Intelligent Command Mapping Tool

A powerful command-line tool for intelligently mapping commands between different package managers. Allows you to use familiar package manager syntax on any system!

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

```sh
# Install from source
git clone https://github.com/your-username/actmap.git
cd actmap
pipx install .
```

Command Completion:

```sh
# ## zsh
if command -v actmap &>/dev/null; then
  eval "$(_ACTMAP_COMPLETE=zsh_source actmap)"
fi

if command -v actmap-execute &>/dev/null; then
  eval "$(_ACTMAP_EXECUTE_COMPLETE=zsh_source actmap-execute)"
fi
```

### Basic Usage

init-config and set default target actmap:

```sh
# Initialize user configuration (first-time use)
actmap-generate --init-config

# Edit ~/.config/actmap/config.toml, configure default
default_target_actmap = "<your default target>"  # `actmap -t, --target` will override this option
```

actmap map (automatically detects commands after map to map to target actmap):

```sh
# Map apt command to target actmap
actmap map -- apt install vim git
# If target_actmap is "pacman", maps to: pacman -S vim git

# Map pacman command to apt actmap
actmap -t apt map -- pacman -S vim git  # Maps to: apt install vim git

# View mapping from pacman actmap to apt actmap
actmap --output-actmap pacman apt
```

actmap act (map commands based on specified action):

```sh
actmap act install vim git
# If target_actmap is "pacman", executes: pacman -S vim git
```

actmap-execute (execute mapped commands) map:

```sh
actmap-execute map -- pacman -S vim git

# Interactive execution (recommended for dangerous operations)
actmap-execute -i map -- pacman -Rns vim

# Force execution (skip confirmation)
actmap-execute -f map -- apt remove python3
```

actmap-execute act:

```sh
actmap-execute install vim git

# If there's an action grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
actmap-execute -- grep_log foo.log bar.log == ERROR == write
# Will execute: cat foo.log bar.log | grep -i 'ERROR' | grep -i 'write'
```

## Using actmap-generate to Manage actmap Configuration

```sh
# Initialize user configuration (creates ~/.config/actmap/)
actmap-generate --init-config

# Use actmaps
actmap-generate --use-actmaps pacman,apt,dnf,brew,zypper,scoop,winget,chocolatey

# Add actmaps
actmap-generate --add-actmaps brew,scoop,winget

# View supported actmaps
actmap-generate --list-actmaps
```

## 🎯 Usage Examples

### Use Your Familiar Package Manager to Install vim git

```sh
# debian
actmap map -- apt install vim git
# arch
actmap map -- pacman -S search vim git
```

### Use Your Familiar Action to Install vim git

```sh
# use `install` action
actmap act install vim git
```

### Temporarily Switch Targets

```sh
# If you forget pip command to show package info, you can use any familiar way to execute
actmap-execute -t pip map -- pacman -Si <pkg>   # Will map to: pip show <pkg>
# OR
actmap-execute -t pip map -- brew info <pkg>
```

## output-actmap examples

pacman -> apt:

```sh
actmap --output-actmap pacman apt
```

```
================================================================================
状态   动作              源命令                       目标命令                          
--------------------------------------------------------------------------------
✅    install         pacman -S {pkgs}          apt install {pkgs}            
✅    remove          pacman -R {pkgs}          apt remove {pkgs}             
✅    search          pacman -Ss {pkgs}         apt search {pkgs}             
✅    update          pacman -Sy                apt update                    
✅    upgrade         pacman -Syu               apt upgrade                   
✅    force_update    pacman -Syy               apt update --refresh-all      
✅    force_upgrade   pacman -Syyu              apt update --refresh-all && apt upgrade
✅    info            pacman -Si {pkgs}         apt show {pkgs}               
✅    list_installed  pacman -Q                 apt list --installed          
✅    clean           pacman -Sc                apt autoclean                 
✅    help            pacman -h                 apt --help                    
✅    list_files      pacman -Ql {pkgs}         dpkg -L {pkgs}                
✅    find_file_owner pacman -Qo {files}        dpkg -S {files}               
✅    find_file_owner_remote pacman -F {files}         apt-file search {files}       
✅    download_source asp export {pkgs}         apt source {pkgs}             
================================================================================
```

## ActMap Configuration Format Reference

See [ref](./doc/actmap_config.md)