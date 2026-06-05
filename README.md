# Refactored Bassoon — Unified Launcher

> *One launcher to rule them all — game platforms, browsers, live-streaming tools, and VM systems in a single interactive menu, with zero double-launching.*

A modular Python launcher system that opens all your installed game launchers, web browsers, streaming/recording apps, and virtualization systems from one interactive CLI menu. Built with a centralized launch tracker to guarantee no program opens more than once per session.

## 🎯 Features

- **Game Launchers** — Steam, Epic Games, GOG Galaxy, Battle.net, EA Desktop, Ubisoft Connect, Amazon Games, Xbox Game Pass, itch.io, PlayStation PC
- **Web Browsers** — Chrome, Firefox, Edge, Brave, Opera, Cursor (cross-platform)
- **Live & Recording Kit** — Warudo, OBS Studio, OneNote, Sticky Notes, Perplexity
- **VM System** — Docker Desktop, WSL
- **Site Runner** — Opens all URLs from `config.json` in browser tabs (supports Windows, macOS, Linux, and WSL)
- **Duplicate Prevention** — Centralized `LaunchTracker` ensures no program opens twice, even across categories
- **Startup Cleaner** — Remove startup programs from Windows folders and registry

## 🛠️ Technology Stack

- **Python 3.x** — No external dependencies (standard library only)
- Cross-platform support for Windows, macOS, and Linux
- WSL-aware site runner with automatic `wsl-open` detection

## 📁 Project Structure

```text
refactored-bassoon/
├── launcher.py                    # Main interactive menu (Unified Launcher)
├── utils.py                       # Shared helpers + LaunchTracker singleton
├── config.json                    # Browser preference + URL list for site runner
│
├── launch_all_game_launchers.py   # Standalone: game launchers only
├── Browser launcher.py            # Standalone: browsers only
├── launch_live_and_rec_kit.py     # Standalone: live/recording kit
├── vm_system_launcher.py          # Standalone: Docker + WSL
├── vm_system.py                   # Standalone: Docker + WSL (legacy)
│
├── run_sites.py                   # Standalone: open URLs from config.json
├── stop_startup_programs.py       # Standalone: Windows startup cleaner
│
├── Hello World.py                 # Sanity check
└── README.md
```

## 🚀 Getting Started

### Run the Unified Launcher

```bash
python launcher.py
```

You'll see an interactive menu:

```
========================================================
          UNIFIED LAUNCHER
========================================================
  Game Launchers | Browsers | Live Kit | VM System
========================================================

  [1] Game Launchers (Steam, Epic, GOG, Battle.net, EA, ...)

  [2] Web Browsers (Chrome, Firefox, Edge, Brave, Opera, Cursor)

  [3] Live & Recording Kit (Warudo, OBS, OneNote, Sticky Notes, ...)

  [4] Launch ALL

  [5] VM System (Docker Desktop, WSL)

  [0] Exit

  Enter your choice [0-5]:
```

### Run Individual Launchers

Each component can also be run standalone:

```bash
python launch_all_game_launchers.py   # Game launchers only
python "Browser launcher.py"          # Browsers only
python launch_live_and_rec_kit.py     # Live kit only
python vm_system_launcher.py          # VM systems only
```

### Open Websites from Config

```bash
# Uses browser specified in config.json
python run_sites.py

# Override browser
python run_sites.py chrome
python run_sites.py firefox
```

Edit `config.json` to customize the URL list and default browser:

```json
{
    "default_browser": "opera",
    "social_media_urls": [
        "https://app.hootsuite.com/",
        "https://app.sproutsocial.com/"
    ]
}
```

## 🔒 Duplicate Prevention

The `utils.py` module includes a `LaunchTracker` singleton that tracks every program launched during a session. Key design decisions:

- **Steam** is launched only by the Game Launchers category — it was intentionally removed from Live Kit to prevent double-opening
- Selecting "Launch ALL" calls `reset_tracker()` once, then all categories share the same tracker
- Each standalone script starts with a fresh tracker

---

*Built for efficient, one-click system startup.*
