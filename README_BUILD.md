# Jarvis Gaming Assistant - APK Build & Deployment Guide

Complete step-by-step instructions to build the Android APK and deploy to your device.

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **Python**: 3.8 or higher

### Required Tools

```bash
# Install system dependencies
sudo apt update
sudo apt install -y \
    git \
    zip \
    unzip \
    openjdk-17-jdk \
    python3-pip \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    automake

# Install Python packages
pip3 install --user buildozer cython

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### Android SDK Setup

```bash
# Download command line tools
mkdir -p ~/android-sdk/cmdline-tools
cd ~/android-sdk/cmdline-tools
wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
unzip commandlinetools-linux-9477386_latest.zip
mv cmdline-tools latest

# Set environment variables
export ANDROIDSDK="$HOME/android-sdk"
export ANDROIDNDK="$HOME/android-sdk/ndk/25c"
export PATH="$ANDROIDSDK/cmdline-tools/latest/bin:$PATH"

# Install SDK components
sdkmanager "platforms;android-34"
sdkmanager "build-tools;34.0.0"
sdkmanager "ndk;25.2.9519653"  # NDK 25c
```

---

## Build Instructions

### Step 1: Prepare Project

```bash
# Navigate to project directory
cd /home/dipesh-patel/Documents/AI-Mobile-Assistant

# Verify project structure
ls -la
# Should show: main.py, buildozer.spec, jarvis/, assets/, recipes/
```

### Step 2: Download Required Assets

#### 2.1 Minicap Binaries
```bash
# Download from https://github.com/openstf/minicap/releases
# For arm64 devices (most modern phones)
cd assets/minicap/arm64-v8a
wget https://github.com/openstf/minicap/releases/download/v2.0/minicap-arm64-v8a
mv minicap-arm64-v8a minicap
chmod +x minicap

cd ../armeabi-v7a
wget https://github.com/openstf/minicap/releases/download/v2.0/minicap-armeabi-v7a
mv minicap-armeabi-v7a minicap
chmod +x minicap
```

#### 2.2 Game Templates (Create from Screenshots)
```bash
# Create game templates directory
mkdir -p assets/game_templates

# You need to capture these from actual gameplay at 1080x2340:
# - red_hp_20percent.png (200x50px) - Low HP bar
# - yellow_hp_50percent.png (200x50px) - Medium HP bar
# - green_hp_high.png (200x50px) - Full HP bar
# - enemy_headshot.png (64x64px) - Enemy marker
# - enemy_scope_glint.png (64x64px) - Scope reflection
# - blue_zone_edge.png (100x100px) - Safe zone boundary
# - ammo_counter_bg.png (150x40px) - Ammo display

# Place all PNG files in assets/game_templates/
```

### Step 3: Configure Buildozer

```bash
# Verify buildozer.spec exists and is configured
cat buildozer.spec | head -50

# Key settings to verify:
# - title = Jarvis Gaming Assistant
# - package.name = jarvisgameassist
# - android.api = 34
# - android.minapi = 24
# - android.ndk = 25c
```

### Step 4: Build Debug APK

```bash
# Clean previous builds (optional)
buildozer android clean

# Build debug APK
buildozer android debug

# Build output will be in:
# ./bin/jarvisgameassist-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

**Expected build time**: 15-30 minutes (first build)

### Step 5: Build Release APK (Optional)

```bash
# Generate keystore for signing
keytool -genkey -v -keystore jarvis.keystore -alias jarvis \
    -keyalg RSA -keysize 2048 -validity 10000

# Configure signing in buildozer.spec
# Add to [app] section:
# android.keystore = jarvis.keystore
# android.keyalias = jarvis

# Build release
buildozer android release
```

---

## Deployment Instructions

### Method 1: Direct Install (USB)

```bash
# Enable USB debugging on your Android device
# Settings > Developer Options > USB Debugging

# Connect device and verify
adb devices

# Install APK
adb install -r bin/jarvisgameassist-1.0.0-arm64-v8a_armeabi-v7a-debug.apk

# Launch app
adb shell am start -n com.yourname.jarvisgameassist/org.kivy.android.PythonActivity
```

### Method 2: Buildozer Deploy

```bash
# Connect device via USB
# Deploy and run in one command
buildozer android debug deploy run
```

### Method 3: Manual Transfer

```bash
# Copy APK to device
adb push bin/jarvisgameassist-1.0.0-arm64-v8a_armeabi-v7a-debug.apk /sdcard/Download/

# Install using device file manager
# Navigate to Download folder and tap APK
```

---

## Post-Installation Setup

### Grant Required Permissions

1. **Open Jarvis app**
2. **Tap "Check Permissions" button**
3. **Grant each permission when prompted:**
   - Microphone - For voice commands
   - Display over other apps - For floating overlay
   - Storage - For screen capture

### Manual Permission Grant (if needed)

```bash
# Grant permissions via ADB
adb shell pm grant com.yourname.jarvisgameassist android.permission.RECORD_AUDIO
adb shell pm grant com.yourname.jarvisgameassist android.permission.SYSTEM_ALERT_WINDOW
adb shell pm grant com.yourname.jarvisgameassist android.permission.WRITE_EXTERNAL_STORAGE
```

---

## Testing on Device

### 1. Start Jarvis
```
1. Open Jarvis Gaming Assistant app
2. Tap "START JARVIS" button
3. You should hear: "Jarvis online. Ready to assist, boss!"
```

### 2. Test Voice Commands
```
Say: "Jarvis health"
Expected: "Your HP is X%, ..." or "Can't read your HP right now"

Say: "Jarvis enemies"
Expected: "No enemies detected..." or "X enemies at Y o'clock"

Say: "Jarvis status"
Expected: Full status report
```

### 3. Test Screen Capture
```
1. Open PUBG/Free Fire/COD Mobile
2. Verify overlay appears with stats
3. Check that HP bar detection works
```

---

## Troubleshooting

### Build Errors

#### Error: "NDK not found"
```bash
# Verify NDK path
export ANDROIDNDK="$HOME/android-sdk/ndk/25.2.9519653"
# Update buildozer.spec with correct path
```

#### Error: "Command not found: buildozer"
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
# Or reinstall
pip3 install --user --force-reinstall buildozer
```

#### Error: "AAPT2 error"
```bash
# Clean and rebuild
buildozer android clean
buildozer android debug
```

### Runtime Errors

#### Overlay not showing
```bash
# Grant permission manually
adb shell appops set com.yourname.jarvisgameassist SYSTEM_ALERT_WINDOW allow
```

#### Screen capture not working
- Minicap requires Android 10+ or root access
- Use fallback screencap method (automatic)
- Check if templates are in correct directory

#### Voice not working
- Verify microphone permission granted
- Test in quiet environment
- Use offline STT if available

---

## Performance Optimization

### Battery Optimization

```bash
# Disable battery optimization for Jarvis
adb shell dumpsys deviceidle whitelist +com.yourname.jarvisgameassist
```

### FPS Tuning

Edit `jarvis/screen.py` to adjust:
```python
fps=10  # Reduce from 15 for better battery
```

---

## File Structure Verification

Before building, verify this structure:

```
AI-Mobile-Assistant/
├── main.py                          ✓ Entry point
├── buildozer.spec                   ✓ Build config
├── jarvis/
│   ├── __init__.py                 ✓ Package init
│   ├── voice.py                    ✓ Voice pipeline
│   ├── screen.py                   ✓ Screen capture
│   ├── brain.py                    ✓ Game analysis
│   └── overlay.py                  ✓ Floating UI
├── assets/
│   ├── minicap/
│   │   ├── arm64-v8a/minicap       ✓ Required
│   │   └── armeabi-v7a/minicap     ✓ Required
│   ├── game_templates/             ✓ PNG templates
│   └── sounds/                     ✓ Optional audio
└── tests/
    ├── validate.py                 ✓ Test suite
    └── test_jarvis.py              ✓ Unit tests
```

---

## Quick Reference Commands

```bash
# Full build and deploy
buildozer android debug deploy run

# Clean build
buildozer android clean

# Check logs
adb logcat -s "python" | grep -i jarvis

# Uninstall
adb uninstall com.yourname.jarvisgameassist

# Reinstall
adb install -r bin/*.apk
```

---

## Support

- **Buildozer docs**: https://buildozer.readthedocs.io/
- **Kivy on Android**: https://kivy.org/doc/stable/guide/android.html
- **Minicap**: https://github.com/openstf/minicap

---

**Build Date**: 2024-02-24  
**Version**: 1.0.0  
**Target**: Android 11+ (API 30+)
