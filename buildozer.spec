[app]
# Title of the application
title = Jarvis Gaming Assistant

# Package name
package.name = jarvisgameassist

# Package domain
package.domain = com.yourname

# Source code directory
source.dir = .

# Version
version = 1.0.0

# Requirements - Python packages
requirements = python3,kivy==2.3.0,opencv,pillow,numpy,pvporcupine,pykivdroid,android_screen_buffer,pytesseract,jnius,android

# Android API versions
android.api = 34
android.minapi = 24
android.ndk = 25c
android.sdk = 34

# Android permissions
android.permissions = INTERNET,RECORD_AUDIO,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,MANAGE_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,ACCESS_MEDIA_LOCATION

# Android features
android.feature = android.hardware.microphone

# Application orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Services
# android.services = JarvisService:jarvis/overlay.py

# Add source files (minicap binaries)
android.add_src = assets/minicap/arm64-v8a/minicap,assets/minicap/armeabi-v7a/minicap

# Add assets (game templates and sounds)
android.add_assets = assets/game_templates/*:game_templates/,assets/sounds/*:sounds/

# Build options
android.gradle_dependencies = 
android.enable_androidx = True

# Presplash (loading screen)
presplash.filename = %(source.dir)s/assets/presplash.png

# Icon
icon.filename = %(source.dir)s/assets/icon.png

# Window flags
android.window_flags = FLAG_KEEP_SCREEN_ON,FLAG_NOT_FOCUSABLE

# Allowed host paths for file access (Android 11+)
android.allowed_hosts = localhost,127.0.0.1

# Buildozer specific
buildozer.build_dir = ./.buildozer
buildozer.bin_dir = ./bin

[buildozer]
# Buildozer log level
log_level = 2

# Warn on root
warn_on_root = 1

# iOS build (disabled)
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0
ios.codesign.allowed = false

[formatters]
keys = generic

[formatter_generic]
format = %(message)s

[handlers]
keys = console

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[loggers]
keys = root

[logger_root]
level = INFO
handlers = console
