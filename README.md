
# 🎯 WinSet — Windows Configuration Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)  
[![Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)](https://www.microsoft.com/windows)  
[![Downloads](https://img.shields.io/github/downloads/enricjake/winset/total)](https://github.com/enricjake/winset/releases)  
[![Stars](https://img.shields.io/github/stars/enricjake/winset)](https://github.com/enricjake/winset/stargazers)

<p align="center">
  <img src="docs/images/winset_logo.png" width="200"/>
</p>

<p align="center">
<b>Your Windows, perfectly configured — fresh installs or daily drivers</b>
</p>

---

## ✨ Why WinSet?

**New PC?** Apply a preset instantly.  
**Reinstalling?** Export & restore your configuration.  
**Tweaker?** Compare and share optimal setups.

WinSet is a **complete Windows configuration ecosystem** that lets you:

- 🚀 Optimize performance or battery
- 🔒 Lock down privacy
- 🎮 Configure for gaming
- 💼 Configure for productivity
- 🔄 Migrate settings across PCs
- 👥 Share configs with others

---

## 🎨 Features

### Two Modes

```
Existing PC → Export → Save → Share
New PC      → Preset → Preview → Apply
```

### Configurable Areas

| Category | Settings |
|---------|----------|
| 🎨 Appearance | Themes, colors, wallpaper, transparency |
| 📁 Explorer | Hidden files, extensions, navigation |
| 🖱 Taskbar | Alignment, icons, widgets |
| ⚡ Power | Plans, CPU tuning, cooling |
| 🔒 Privacy | Telemetry, mic/camera, location |
| 🎮 Gaming | Game Mode, GPU scheduling |
| ⌨ Input | Mouse speed, keyboard |
| 🌐 Regional | Date, currency, measurement |
| ♿ Accessibility | Narrator, contrast |
| 🔧 Advanced | Virtual memory, DEP |

---

## 🎯 Built-in Presets

WinSet includes **10 presets**:

- 🚀 Performance
- 🛡 Privacy
- 🎮 Gaming
- 👤 Default Windows
- 🏢 Work
- 🔋 Battery Saver
- ♿ Accessibility
- 🎨 Creator
- 🔧 Developer
- ⭐ Custom

---

## 🔀 Hybrid Mode (Core Feature)

Combine presets into a **single optimized configuration**.

Example:

```
Base: Gaming
Add: Privacy
Add: Battery
```

Conflict example:

```
Telemetry:
Gaming → Full
Privacy → Security (WINNER)

Power Plan:
Gaming → Ultimate Performance
Battery → Power Saver (WINNER)
```

---

## 🚀 Quick Start

### New PC

```
1. Run WinSet as admin
2. Apply preset
3. Done
```

### Existing PC

```
1. Export settings
2. Import on new PC
```

---

## 💻 Installation

### Download EXE (Recommended)

https://github.com/enricjake/winset/releases

### pip

```
pip install winset
winset --gui
```

### From Source

```
git clone https://github.com/enricjake/winset.git
cd winset
pip install -r requirements.txt
python src/main.py
```

---

## 🔧 Build

```
pyinstaller --onefile --windowed --icon=icon.ico --name=WinSet src/main.py
```

---

## 📊 Roadmap

### 1.0
- Presets
- Export/import
- GUI

### 1.5
- Preset editor
- CLI

### 2.0
- Cloud sync
- Preset gallery
- AI recommendations

---

## 📝 License

MIT

---

## ⭐ Support

If you find WinSet useful, **star the repo**.
