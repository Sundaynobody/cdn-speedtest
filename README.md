# CDN SpeedTest

A cross-platform desktop tool for measuring CDN download speeds with real-time network interface detection.

## Features

- **CDN Speed Testing** — Downloads test files from configurable nodes and displays real-time, max, and average speeds
- **Network Info Display** — Auto-detects active network adapter: WiFi (SSID, link rate, band, signal quality) or Ethernet (link speed)
- **Multi-Platform** — Windows (packaged .exe), macOS, Linux
- **Multi-Language** — English, 简体中文, Français, Deutsch, Español, Português, Italiano, Русский, Polski, العربية
- **DPI-Aware** — Properly scales on high-DPI displays (Windows)
- **Node Manager** — Add/edit/delete/move CDN test nodes with default selection
- **Auto-Refresh** — Network info refreshes every 10s in background

## Screenshots

<!-- Consider adding screenshots: ![main](screenshots/main.png) -->

## Prerequisites

- **Windows**: No prerequisites — the packaged `.exe` bundles all dependencies.
- **macOS / Linux**: Python 3.9+ with the packages listed in `requirements.txt`.

### Dependencies

| Package      | Version | Purpose                  |
|--------------|---------|--------------------------|
| `requests`   | any     | HTTP download & IP geolocation |
| `Pillow`     | any     | Window icon support      |
| `ttkbootstrap` | any  | Modern themed Tkinter UI |

## Installation

### Windows (packaged binary)

Download `CDNSpeedTest_x86_64.exe` from the [Releases](../../releases) page and run it directly — no installation required.

Configuration is auto-saved to `%LOCALAPPDATA%\CDNSpeedTest\cdn_nodes.json`.

### From source

```bash
git clone <repo-url>
cd cdn-speedtest
pip install -r requirements.txt
python main.py
```

## Usage

1. **Start a test** — Click **Start Test** to download from the selected node
2. **Stop** — Click **Stop** to abort
3. **Manage nodes** — Click **Settings** to add/edit/delete CDN test URLs
4. **Switch language** — Use the dropdown in Settings to change UI language

The network interface panel shows:
- WiFi: 📶 `SSID · 72 Mbps · 2.4 GHz · 100% ████`
- Ethernet: 🖧 `1000 Mbps`

## Build

Build a standalone executable for the current platform:

```bash
python build.py
```

### Windows

```bash
# 64-bit (default)
python build.py

# 32-bit (requires separate 32-bit Python install)
python build.py --arch x86
```

### macOS

```bash
# Native arch
python build.py

# Universal binary (Intel + Apple Silicon)
python build.py --arch universal2
```

Output: `dist/CDNSpeedTest_<arch>[.exe]`

> **Note**: The build script auto-detects architecture. On Windows, use separate Python installs for x86/x64 builds and pass `--python <path>`.

## Project Structure

```
cdn-speedtest/
├── main.py              # Application entry point
├── build.py             # PyInstaller build script
├── requirements.txt     # Python dependencies
├── icon.ico             # Window icon (Windows)
├── icon.png             # Window icon (macOS/Linux)
├── gen_icon.py          # Icon generator helper
├── dist/                # Build output directory
└── .github/workflows/   # CI/CD workflows
```

## Architecture

The app uses **Tkinter** with **ttkbootstrap** for the UI. Network detection strategies differ by OS:

| OS      | Method |
|---------|--------|
| Windows | Single PowerShell call combining `Get-NetRoute`, `Get-NetAdapter`, and `netsh wlan` |
| macOS   | `airport -I` for WiFi, `ifconfig` for Ethernet |
| Linux   | `/sys/class/net/*` sysfs + `iw dev link` for WiFi |

All network queries run in a background thread to avoid blocking the UI.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
