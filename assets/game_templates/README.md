# Game Templates Setup

These template images are used for computer vision analysis of game screens.

## Required Templates (1080x2340 screenshots)

Create these by cropping screenshots from actual gameplay:

### 1. red_hp_20percent.png (200x50px)
Capture when your HP is critically low (red bar, ~20%)
Location: Bottom-left of screen

### 2. yellow_hp_50percent.png (200x50px)
Capture when HP is medium (yellow bar, ~50%)
Location: Bottom-left of screen

### 3. green_hp_high.png (200x50px)
Capture when HP is full/near-full (green bar, 80%+)
Location: Bottom-left of screen

### 4. enemy_headshot.png (64x64px)
Capture enemy head marker when scoped in
Location: Center screen during ADS

### 5. enemy_scope_glint.png (64x64px)
Capture scope reflection/glint from enemy snipers
Location: Center screen when enemy is scoped

### 6. blue_zone_edge.png (100x100px)
Capture blue storm circle edge on minimap
Location: Top-right minimap area

### 7. ammo_counter_bg.png (150x40px)
Capture ammo count display background
Location: Bottom-right of screen

## Tips for Capturing

1. Play at 1080x2340 resolution (common on mobile)
2. Take clean screenshots without UI clutter
3. Use consistent lighting conditions
4. Save as PNG with transparency where applicable
5. Test templates work with cv2.matchTemplate()

## Testing Templates

```python
import cv2

# Load template
template = cv2.imread('red_hp_20percent.png')
screen = cv2.imread('screenshot.png')

# Test matching
result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(result)
print(f"Match confidence: {max_val}")  # Should be >0.8
```
