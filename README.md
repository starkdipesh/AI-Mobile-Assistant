# Jarvis Gaming Assistant

Real-time AI game assistant for PUBG Mobile, Free Fire, and COD Mobile with voice commands and floating overlay.

## Features

- **Voice Commands**: "Jarvis health", "Jarvis enemies", "Jarvis ammo", "Jarvis zone", "Jarvis status"
- **Wake Word Detection**: "Jarvis" triggers listening mode
- **Screen Analysis**: Real-time HP, ammo, enemy detection at 15 FPS
- **Floating Overlay**: Draggable stats window with live game data
- **Offline Operation**: No internet required after setup

## Project Structure

```
jarvis-game-assistant/
├── main.py              # Kivy App entrypoint
├── buildozer.spec       # APK build configuration
├── jarvis/              # Core modules
│   ├── __init__.py
│   ├── voice.py         # Wake word + STT + TTS
│   ├── screen.py        # Screen capture + CV analysis
│   ├── brain.py         # Command processing + game logic
│   └── overlay.py       # Floating UI
├── assets/              # Assets
│   ├── minicap/         # Screen capture binaries
│   ├── game_templates/  # Template images for CV
│   └── sounds/          # Alert sounds
└── README.md
```

## Build Instructions

### Prerequisites
- Python 3.9+
- Buildozer
- Android SDK/NDK
- Linux build environment (or WSL on Windows)

### Install Dependencies
```bash
pip install kivy opencv-python pillow numpy pvporcupine pytesseract
```

### Build APK
```bash
# Build debug APK
buildozer android debug

# Build and deploy to connected device
buildozer android debug deploy run
```

## Game Templates

Create these templates from 1080x2340 gameplay screenshots:

| Template | Size | Description |
|----------|------|-------------|
| red_hp_20percent.png | 200x50px | Low HP indicator |
| yellow_hp_50percent.png | 200x50px | Medium HP |
| green_hp_high.png | 200x50px | Full HP |
| enemy_headshot.png | 64x64px | Enemy head marker |
| enemy_scope_glint.png | 64x64px | Scope reflection |
| blue_zone_edge.png | 100x100px | Safe zone boundary |
| ammo_counter_bg.png | 150x40px | Ammo display |

## Voice Commands

| Command | Response |
|---------|----------|
| "Jarvis health" | Current HP % + urgency warning if low |
| "Jarvis enemies" | Enemy count + direction/distance |
| "Jarvis ammo" | Current ammo count |
| "Jarvis zone" | Safe zone position + time |
| "Jarvis status" | Full report (HP+ammo+kills+enemies+zone) |

## Permissions Required

- **Microphone**: Voice commands
- **System Alert Window**: Floating overlay
- **Foreground Service**: Background operation
- **Storage**: Screen capture access

## Battery & Performance

- Target: <10% battery drain per hour
- Screen analysis: <100ms per frame (15 FPS)
- CPU usage: <5% for voice, <15% for CV

## License

MIT License - Use at your own risk for gaming assistance.

## Disclaimer

This tool is for educational purposes. Use in accordance with game terms of service.
