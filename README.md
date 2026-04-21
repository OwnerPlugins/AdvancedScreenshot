<h1 align="center">📸 Advanced Screenshot Plugin for Enigma2</h1>

![Visitors](https://komarev.com/ghpvc/?username=Belfagor2005&label=Repository%20Views&color=blueviolet)
[![Version](https://img.shields.io/badge/Version.-1.2-blue.svg)](https://github.com/Belfagor2005/AdvancedScreenshot)
[![Enigma2](https://img.shields.io/badge/Enigma2-Plugin-ff6600.svg)](https://www.enigma2.net)
[![Python](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python package](https://github.com/Belfagor2005/AdvancedScreenshot/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/AdvancedScreenshot/actions/workflows/pylint.yml) 
[![Ruff Status](https://github.com/Belfagor2005/AdvancedScreenshot/actions/workflows/ruff.yml/badge.svg)](https://github.com/Belfagor2005/AdvancedScreenshot/actions/workflows/ruff.yml)
[![GitHub stars](https://img.shields.io/github/stars/Belfagor2005/AdvancedScreenshot?style=social)](https://github.com/Belfagor2005/AdvancedScreenshot/stargazers)
[![Donate](https://img.shields.io/badge/_-Donate-red.svg?logo=githubsponsors&labelColor=555555&style=for-the-badge)](https://ko-fi.com/lululla)


---

<p align="center">
  <img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/usr/lib/enigma2/python/Plugins/Extensions/AdvancedScreenshot/plugin.png?raw=true" height="120">
</p>

---

## 📺 Screenshots

<p align="center">
  <img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/screen/config.png?raw=true" height="220">
  <img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/screen/galery.png?raw=true" height="220">
</p>

<p align="center">
  <img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/screen/list.png?raw=true" height="220">
</p>

---

**Enigma2 project**


## 🧩 Description

**Advanced Screenshot** is a powerful plugin for Enigma2-based devices that lets you:

- Take instant screenshots directly from your receiver
- Browse captured images with a built-in thumbnail gallery
- View full-screen previews
- Use slideshow mode for automated image browsing
- Navigate using remote control shortcuts

## ⚙️ Features

- 📸 Quick screenshot capture
- 📁 File browser with image listing
- 🖥️ Fullscreen image preview
- 🔁 Slideshow mode with timer
- 🎨 Responsive skin, adjusts to screen size
- 🕹️ Remote control navigation

---

## 📦 Requirements

- Enigma2-based receiver (OE-A / OpenATV / OpenPLI compatible)
- Python > 3.x
- PNG/JPG image rendering support
- Compatible skin with GUI widgets

---

## 🚀 Installation

1. Copy the plugin directory:

```bash
/Plugins/Extensions/AdvancedScreenshot/
````

to your receiver path:

```bash
/usr/lib/enigma2/python/Plugins/Extensions/
```

2. Restart the GUI:

```bash
Menu > Standby / Restart > Restart GUI
```

3. Access the plugin from:

```bash
Menu > Plugins > Advanced Screenshot
```

---

## 🎮 Remote Control Shortcuts

| Button    | Action                 |
| --------- | ---------------------- |
| 🔴 Red    | Previous image         |
| 🔵 Blue   | Next image             |
| 🟡 Yellow | Play / Pause slideshow |
| 🟢 Green  | Play / Pause slideshow |
| ◀️ Left   | Previous image         |
| ▶️ Right  | Next image             |
| ❌ Exit    | Close viewer           |

---

## 📁 Directory Structure

```
AdvancedScreenshot/
├── plugin.py
├── picplayer.py
├── MyConsole.py
├── plugin.png
├── locale/
├── images/
│   ├── pic_frame.png
│   └── pic_framehd.png
└── README.md
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 💡 Credits

Developed and maintained by Lululla(https://github.com/Belfagor2005)
Contributions, bug reports, and suggestions are welcome!

```

---

```
