# ActMap - Intelligent Command Mapping Tool

A powerful command-line tool for intelligently mapping commands between different package managers. Allows you to use familiar package manager syntax on any system!

## Languages

[中文](./README_ZH.md)

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

Alias (optional):

```sh
alias am="actmap"
alias ame="actmap-execute"
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
actmap map apt install vim git
# If target_actmap is "pacman", maps to: pacman -S vim git

# Map pacman command to apt actmap
actmap -t apt map pacman -S vim git  # Maps to: apt install vim git

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
actmap-execute map pacman -S vim git

# Interactive execution (recommended for dangerous operations)
actmap-execute -i map pacman -Rns vim

# Force execution (skip confirmation)
actmap-execute -f map apt remove python3
```

actmap-execute act:

```sh
actmap-execute act install vim git

# If there's an action grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
actmap-execute act grep_log foo.log bar.log == ERROR == write
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
actmap map apt install vim git
# arch
actmap map pacman -S search vim git
```

### Use Your Familiar Action to Install vim git

```sh
# use `install` action
actmap act install vim git
```

### Temporarily Switch Targets

```sh
# If you forget pip command to show package info, you can use any familiar way to execute
actmap-execute -t pip map pacman -Si <pkg>   # Will map to: pip show <pkg>
# OR
actmap-execute -t pip map brew info <pkg>
```

## `actmap-generate` actmap Configuration

### Configured actmaps

```sh
actmap --list-actmaps
```

```
ℹ️ INFO: 📦 Package managers in current configuration:
  ✅ apt - supports 15 actions
  ✅ brew - supports 15 actions
  ✅ cargo - supports 8 actions
  ✅ chocolatey - supports 15 actions
  ✅ dnf - supports 15 actions
  ✅ npm - supports 8 actions
  ✅ pacman - supports 15 actions
  ✅ pip - supports 10 actions
  ✅ scoop - supports 15 actions
  ✅ winget - supports 15 actions
  ✅ zypper - supports 15 actions
```

### output-actmap examples

pacman -> apt:

```sh
actmap --output-actmap pacman apt
```

```
================================================================================
Status Action          Source Command            Target Command
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

pacman -> pip:

```sh
actmap --output-actmap pacman pip
```

```
================================================================================
Status Action          Source Command            Target Command
--------------------------------------------------------------------------------
✅    install         pacman -S {pkgs}          pip install {pkgs}
✅    remove          pacman -R {pkgs}          pip uninstall {pkgs}
✅    search          pacman -Ss {pkgs}         pip search {pkgs}
✅    update          pacman -Sy                pip install --upgrade pip
✅    upgrade         pacman -Syu               pip install --upgrade {pkgs}
❌    force_update    pacman -Syy               Not supported
❌    force_upgrade   pacman -Syyu              Not supported
✅    info            pacman -Si {pkgs}         pip show {pkgs}
✅    list_installed  pacman -Q                 pip list
✅    clean           pacman -Sc                pip cache purge
✅    help            pacman -h                 pip --help
❌    list_files      pacman -Ql {pkgs}         Not supported
❌    find_file_owner pacman -Qo {files}        Not supported
❌    find_file_owner_remote pacman -F {files}         Not supported
✅    download_source asp export {pkgs}         pip download {pkgs}
================================================================================
```

## ActMap Configuration Format Reference

See [ref](./doc/actmap_config.md)