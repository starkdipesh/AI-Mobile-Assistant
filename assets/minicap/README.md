# Minicap Binary Setup

Minicap provides high-performance screen capture for Android devices.

## Download Instructions

1. Visit: https://github.com/openstf/minicap/releases
2. Download minicap for your target architectures:
   - `arm64-v8a` - Modern 64-bit ARM devices (most phones 2018+)
   - `armeabi-v7a` - Older 32-bit ARM devices

3. Place binaries in respective directories:
   - `assets/minicap/arm64-v8a/minicap`
   - `assets/minicap/armeabi-v7a/minicap`

## Alternative: Build from Source

```bash
git clone https://github.com/openstf/minicap.git
cd minicap
ndk-build  # Requires Android NDK
```

## Runtime

The app will automatically extract and use the correct binary for the device's architecture at runtime.

## Note

Minicap requires root on some devices or Android 10+ may need alternative screen capture methods. The app includes fallback to screencap command if minicap fails.
