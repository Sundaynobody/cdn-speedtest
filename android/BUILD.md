# CDN SpeedTest - Android Build Guide

## Requirements

- **Linux** (or WSL2 on Windows) with Python 3.8+
- **Java JDK 8+** (`openjdk-17-jdk`)
- **Buildozer** (`pip install buildozer`)
- Internet connection (first build downloads Android SDK/NDK ~1.5 GB)

## Build Steps

```bash
# 1. Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3-pip build-essential git \
    openjdk-17-jdk libssl-dev libffi-dev python3-dev \
    autoconf automake libtool pkg-config

# 2. Install Python dependencies
pip install --user buildozer cython

# 3. Build APK
cd android/
buildozer android debug

# 4. Find APK in bin/
ls -lh bin/*.apk
```

## Build with Docker (no system dependency installation)

```bash
cd android/
docker run --rm -v "$PWD":/app -w /app \
    kivy/buildozer:latest buildozer android debug
```

## Install on Device

```bash
# Connect device via USB (enable Developer options + USB debugging)
buildozer android deploy run

# Or manually copy bin/CDNSpeedTest-1.0.0-*.apk to device and install
```

## Architecture

- arm64-v8a (64-bit ARM)
- armeabi-v7a (32-bit ARM)

Both are included in a single APK.

## Notes

- First build takes 20-60 minutes (downloads SDK/NDK)
- Subsequent builds are faster (~2-5 minutes)
- The config file is stored at `{app_storage_path}/.cdn_speedtest/cdn_nodes.json`
