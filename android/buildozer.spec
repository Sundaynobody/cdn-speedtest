[app]
title = CDN SpeedTest
package.name = cdnspeedtest
package.domain = org.cdnspeedtest
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 4.4.0
requirements = python3,kivy==2.3.0,requests
orientation = portrait
fullscreen = 0
presplash_color = #2c3e50
icon = assets/icon.png
android.api = 33
android.minapi = 21
android.ndk = 26c
android.build_tools = 33.0.2
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.private_storage = True
android.wakelock = True
android.wifi = True
android.english_name = CDN SpeedTest
android.copy_libs = 1
android.entrypoint = main.py
android.manifest.permissions = android.permission.INTERNET,android.permission.ACCESS_NETWORK_STATE,android.permission.ACCESS_WIFI_STATE,android.permission.WAKE_LOCK

[buildozer]
log_level = 2
warn_on_root = 1
