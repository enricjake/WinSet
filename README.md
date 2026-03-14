# 🔧 WinSet - Windows Settings Configuration Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://img.shields.io/github/downloads/yourusername/tweakbackup/total)](https://github.com/enricjake/WinSet/releases)

**Never manually reconfigure Windows after reinstall again!**

WinSet exports ALL your Windows settings to a single file. After reinstalling Windows, import that file and all your preferences are back in seconds.

## ✨ Features

- 🎨 **System Appearance** - Theme, wallpaper, accent colors, icons
- 📁 **File Explorer** - Hidden files, extensions, folder views
- 🖱️ **Taskbar & Start Menu** - Pinned apps, layout, search settings
- ⚡ **Power Settings** - Plans, sleep timers, lid actions
- 🔒 **Privacy Options** - Permissions, telemetry, location
- 💾 **One-Click Export/Import** - Single JSON file
- 🔄 **Profile Manager** - Save multiple configurations
- 🛡️ **Safe Mode** - Registry backup before changes

## 🚀 Quick Start

1. Download the latest `WinSet.exe` from [Releases](https://github.com/enricjake/WinSet/releases)
2. Run as Administrator (required for registry access)
3. Click "Export" to save your settings
4. On new PC, run and click "Import"

---

## 🎯 Built-in Presets

WinSet comes with **10 ready-to-use presets** for every scenario:

### 🚀 Performance Mode
*"Maximum speed, minimal eye candy"*
- Disables visual effects and animations
- Enables Game Mode
- Sets High Performance power plan
- Optimizes for foreground programs

### 🛡️ Privacy-Focused Mode
*"Maximum privacy, minimal data sharing"*
- Sets telemetry to Security level (0)
- Disables advertising ID
- Blocks camera/mic by default
- Turns off activity history

### 🎮 Gaming Mode
*"Optimized for the best gaming experience"*
- Enables Game Mode and Game Bar
- Hardware-accelerated GPU scheduling
- Ultimate Performance power plan
- Pauses Windows updates during gameplay

### 👤 Default Windows Mode
*"Clean Windows install defaults"*
- Resets everything to out-of-box state
- Perfect for troubleshooting
- Benchmark baseline

### 🏢 Work/Business Mode
*"Productivity optimized"*
- Enables snap layouts and virtual desktops
- Maximum security settings
- Focus Assist on during work hours
- Clipboard history enabled

### 💡 Battery Saver Mode
*"Maximize laptop battery life"*
- Power Saver plan active
- Reduced screen brightness
- Aggressive timeouts
- USB selective suspend on

### ♿ Accessibility Mode
*"Easier to see, hear, and use"*
- Larger text and cursors
- Visual sound alerts
- Sticky/Filter/Toggle Keys on
- Narrator ready

### 🎨 Creator/Designer Mode
*"Color accuracy & precision"*
- sRGB calibration
- HDR optimization
- Pen input optimized
- ClearType enabled

### 🔧 Developer Mode
*"For coders and power users"*
- Developer Mode enabled
- WSL and Hyper-V ready
- File extensions always visible
- PowerShell unrestricted

### ⭐ Custom Presets
*"Save your perfect combination"*
- Create your own presets
- Mix and match settings
- Share with the community

---

## 🔀 Hybrid Mode: Mix & Match Presets

*"I want Gaming performance with Privacy protection"*  
*"I need Work productivity with Accessibility features"*  
*"I love Creator colors with Battery saving"*  

**Now you can have it all.**

### ⚙️ How Hybrid Mode Works

**Step 1:** Select a base preset (e.g., Gaming Mode)  
**Step 2:** Add additional presets (e.g., Privacy + Battery)  
**Step 3:** Review conflicts and choose winners  
**Step 4:** Apply your perfect custom configuration

### 🔄 Conflict Resolution

When presets disagree, WinSet lets you decide:

- **Order Matters** - Last preset selected wins by default
- **Manual Override** - Choose winners for each conflict
- **Priority Groups** - Assign importance to categories

---

## 📸 Screenshots

*[Screenshots coming soon]*

---

## 🛠️ Building from Source

```bash
git clone https://github.com/enricjake/WinSet.git
cd WinSet
pip install -r requirements.txt
python WinSet.py
