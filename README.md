# 🎯 WinSet - Windows Configuration Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)](https://www.microsoft.com/windows)
[![Downloads](https://img.shields.io/github/downloads/enricjake/winset/total)](https://github.com/enricjake/winset/releases)
[![Stars](https://img.shields.io/github/stars/enricjake/winset)](https://github.com/enricjake/winset/stargazers)

<p align="center">
  <img src="docs/images/winset_logo.png" alt="WinSet Logo" width="200"/>
</p>

<p align="center">
  <b>Your Windows, Perfectly Configured — Whether it's a fresh install or your daily driver</b>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-presets">Presets</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-building-from-source">Build</a> •
  <a href="#-contributing">Contribute</a>
</p>

---

## ✨ **Why WinSet?**

**New PC?** Apply a preset and get your perfect Windows setup in seconds.  
**Reinstalling?** Export your settings and restore them instantly.  
**Tweaker?** Compare configurations, discover optimal settings, share with friends.

WinSet isn't just a backup tool — it's a complete **Windows configuration ecosystem** that helps you:

- 🚀 **Optimize** for gaming, performance, or battery life
- 🔒 **Lock down** privacy with one click
- 💼 **Configure** for work or creative work
- 👥 **Share** your perfect setup with others
- 🔄 **Migrate** settings between PCs effortlessly

---

## 🎨 **Features**

### **Two Powerful Modes**

```
┌─────────────────────────────────────────────────────────────┐
│                      WINSET WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🖥️  EXISTING PC                     💻  NEW PC             │
│      ↓                                    ↓                  │
│  Export your current settings      Choose a preset          │
│      ↓                                    ↓                  │
│  Save as profile                    Preview changes         │
│      ↓                                    ↓                  │
│  Share / Backup                      Apply with 1 click     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **What You Can Configure**

| Category | Settings |
|----------|----------|
| 🎨 **System Appearance** | Themes, colors, wallpaper, transparency, dark/light mode |
| 📁 **File Explorer** | Hidden files, extensions, navigation pane, Quick Access |
| 🖱️ **Taskbar & Start** | Alignment, icons, search, widgets, pinned apps |
| ⚡ **Power & Performance** | Power plans, sleep timers, processor settings, cooling |
| 🔒 **Privacy & Security** | Telemetry, camera/mic access, location, advertising ID |
| 🎮 **Gaming** | Game Mode, Game Bar, captures, TruePlay |
| 🖱️ **Mouse & Keyboard** | Speed, acceleration, button mapping, touchpad |
| 🌐 **Regional** | Date/time formats, currency, measurement units |
| ♿ **Accessibility** | Narrator, magnifier, high contrast, sticky keys |
| 🔧 **Advanced System** | Visual effects, virtual memory, DEP, performance options |

---

## 🎯 **Built-in Presets**

WinSet comes with **10 ready-to-use presets** for every scenario:

### 🚀 **Performance Mode**
*"Maximum speed, minimal eye candy"*
- Disables visual effects and animations
- Enables Game Mode
- Sets High Performance power plan
- Optimizes for foreground programs
- Perfect for gaming and power users

### 🛡️ **Privacy-Focused Mode**
*"Maximum privacy, minimal data sharing"*
- Sets telemetry to Security level (0)
- Disables advertising ID
- Blocks camera/mic by default
- Turns off activity history
- Perfect for privacy enthusiasts

### 🎮 **Gaming Mode**
*"Optimized for the best gaming experience"*
- Enables Game Mode and Game Bar
- Hardware-accelerated GPU scheduling
- Ultimate Performance power plan
- Pauses Windows updates during gameplay
- Perfect for gamers

### 👤 **Default Windows Mode**
*"Clean Windows install defaults"*
- Resets everything to out-of-box state
- Perfect for troubleshooting
- Benchmark baseline
- Starting point for custom configs

### 🏢 **Work/Business Mode**
*"Productivity optimized"*
- Enables snap layouts and virtual desktops
- Maximum security settings
- Focus Assist on during work hours
- Clipboard history enabled
- Perfect for office workers

### 💡 **Battery Saver Mode**
*"Maximize laptop battery life"*
- Power Saver plan active
- Reduced screen brightness
- Aggressive timeouts
- USB selective suspend on
- Perfect for laptops on the go

### ♿ **Accessibility Mode**
*"Easier to see, hear, and use"*
- Larger text and cursors
- Visual sound alerts
- Sticky/Filter/Toggle Keys on
- Narrator ready
- Perfect for accessibility needs

### 🎨 **Creator/Designer Mode**
*"Color accuracy & precision"*
- sRGB calibration
- HDR optimization
- Pen input optimized
- ClearType enabled
- Perfect for designers and artists

### 🔧 **Developer Mode**
*"For coders and power users"*
- Developer Mode enabled
- WSL and Hyper-V ready
- File extensions always visible
- PowerShell unrestricted
- Perfect for developers

### ⭐ **Custom Presets**
*"Save your perfect combination"*
- Create your own presets
- Mix and match settings
- Share with the community
- Export/import anytime

---

## 🚀 **Quick Start**

### **For New PC Users**
```bash
# 1. Download WinSet
# 2. Run as Administrator
# 3. Click "Apply Preset"
# 4. Choose your style (Gaming? Privacy? Performance?)
# 5. Done! Your PC is configured perfectly
```

### **For Existing PC Users**
```bash
# 1. Run WinSet as Administrator
# 2. Click "Export Settings"
# 3. Save your profile
# 4. On new PC, click "Import Settings"
# 5. Done! All settings restored
```

---

## 💻 **Installation**

### **Option 1: Download EXE (Recommended)**
1. Go to [Releases](https://github.com/enricjake/winset/releases)
2. Download `WinSetup.exe`
3. Right-click → Run as Administrator
4. That's it!

### **Option 2: Install via pip**
```bash
pip install winset
winset --gui
```

### **Option 3: Run from Source**
```bash
git clone https://github.com/enricjake/winset.git
cd winset
pip install -r requirements.txt
python src/main.py
```

---

## 🔧 **Building from Source**

```bash
# Clone the repository
git clone https://github.com/enricjake/winset.git
cd winset

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --icon=icon.ico --name=WinSet src/main.py

# Find your EXE in the 'dist' folder!
```

---

## 📸 **Screenshots**

<div align="center">
  <img src="docs/images/main_window.png" alt="Main Window" width="400"/>
  <img src="docs/images/presets.png" alt="Presets" width="400"/>
  <img src="docs/images/compare.png" alt="Compare" width="400"/>
</div>

---

## 🎯 **Use Cases**

### **Scenario 1: Fresh Windows Install**
*"I just installed Windows on my new SSD. Instead of spending 2 hours tweaking settings, I ran WinSet, clicked 'Gaming Mode', and everything was perfect in 30 seconds."*

### **Scenario 2: Privacy Cleanup**
*"I wanted to lock down Windows privacy but didn't know where to start. WinSet's Privacy Mode handled everything with one click."*

### **Scenario 3: Work Laptop Setup**
*"My company issued me a new laptop. I applied my 'Work Mode' preset and all my preferences were there — taskbar, Explorer view, everything."*

### **Scenario 4: Sharing with Friends**
*"My friend wanted their PC set up exactly like mine. I exported my config, sent the file, and they imported it. Perfect clone!"*

---

## 🤝 **Contributing**

We welcome contributions! Here's how you can help:

### **Add New Settings**
Found a registry key we missed? Add it to `docs/registry_keys.md`!

### **Create Presets**
Have a unique configuration? Export it and share as a preset!

### **Report Bugs**
Found an issue? [Open an issue](https://github.com/enricjake/winset/issues)

### **Translate**
Help translate WinSet to other languages!

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📊 **Roadmap**

### **Version 1.0 (Current)**
- ✅ Registry reading/writing
- ✅ 10 built-in presets
- ✅ Export/import functionality
- ✅ Basic GUI

### **Version 1.5 (Coming Soon)**
- 🔄 Preset comparison tool
- 🔄 Preset editor
- 🔄 Command-line interface

### **Version 2.0 (Future)**
- 🌐 Online preset gallery
- ☁️ Cloud sync
- 📱 Remote configuration
- 🤖 AI-powered recommendations

---

## 📝 **License**

MIT License - use freely, modify, distribute, even commercially. Just keep the attribution.

```
Copyright (c) 2024 enricjake

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## 🙏 **Acknowledgments**

- Windows Registry insights from the open-source community
- Icon design by [none]
- Beta testers who broke their PCs so you don't have to

---

## 📬 **Contact**

- **GitHub**: [@enricjake](https://github.com/enricjake)
- **Twitter**: [@enricjake](https://twitter.com/enricjake)
- **Email**: [dorkyman@tutamail.com]

---

<p align="center">
  Made with ❤️ for the Windows community
</p>

<p align="center">
  <b>Star ⭐ this repo if you find it useful!</b>
</p>
