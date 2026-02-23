"""
Jarvis Gaming Assistant - Game Analysis & Command Processing
Phase 3 & 4: Computer Vision + Command Logic
"""
import cv2
import numpy as np
import os
import re
import logging
from collections import deque
from kivy.clock import Clock

logger = logging.getLogger(__name__)


class GameAnalyzer:
    """
    Computer Vision analysis for PUBG/Free Fire/COD Mobile:
    - HP bar detection (red/yellow/green)
    - Enemy detection via template matching
    - Blue zone detection
    - Ammo/Kill count OCR
    """
    
    def __init__(self, templates_dir='assets/game_templates'):
        self.templates_dir = templates_dir
        self.templates = {}
        self.stats_history = deque(maxlen=30)  # 2 seconds at 15 FPS
        
        # Detection thresholds
        self.hp_threshold_low = 0.20
        self.hp_threshold_medium = 0.50
        self.enemy_match_threshold = 0.8
        self.zone_match_threshold = 0.7
        
        # Screen regions (for 1080x2340)
        self.regions = {
            'hp_bar': (50, 1950, 400, 2100),      # Bottom-left HP
            'ammo': (800, 2100, 1050, 2250),      # Bottom-right ammo
            'kills': (50, 100, 200, 200),          # Top-left kills
            'time': (900, 100, 1050, 200),        # Top-right timer
            'minimap': (850, 150, 1050, 450),     # Top-right minimap
            'center': (300, 900, 780, 1500),      # Center screen (enemies)
        }
        
        # Initialize OCR
        self.ocr_engine = None
        self._init_ocr()
        
        # Load templates
        self._load_templates()
    
    def _init_ocr(self):
        """Initialize Tesseract OCR for numbers"""
        try:
            import pytesseract
            self.ocr_engine = pytesseract
            # Configure for digits only
            self.ocr_config = '--psm 7 -c tessedit_char_whitelist=0123456789/:'
            logger.info("OCR initialized")
        except ImportError:
            logger.warning("pytesseract not available, OCR disabled")
            self.ocr_engine = None
    
    def _load_templates(self):
        """Load game template images for matching"""
        template_files = {
            'hp_red': 'red_hp_20percent.png',
            'hp_yellow': 'yellow_hp_50percent.png',
            'hp_green': 'green_hp_high.png',
            'enemy_head': 'enemy_headshot.png',
            'enemy_scope': 'enemy_scope_glint.png',
            'blue_zone': 'blue_zone_edge.png',
            'ammo_bg': 'ammo_counter_bg.png',
        }
        
        for name, filename in template_files.items():
            path = os.path.join(self.templates_dir, filename)
            if os.path.exists(path):
                template = cv2.imread(path)
                if template is not None:
                    self.templates[name] = template
                    logger.info(f"Loaded template: {name}")
                else:
                    logger.warning(f"Failed to load template: {path}")
            else:
                logger.warning(f"Template not found: {path}")
    
    def analyze_frame(self, frame):
        """
        Full frame analysis - returns game state dict
        """
        if frame is None:
            return None
        
        state = {
            'hp_percent': None,
            'hp_urgency': 'unknown',
            'ammo_count': None,
            'kills': None,
            'time_remaining': None,
            'enemies': [],
            'zone_info': None,
            'timestamp': Clock.get_time()
        }
        
        try:
            # HP Analysis
            hp_data = self._analyze_hp(frame)
            state.update(hp_data)
            
            # Ammo OCR
            state['ammo_count'] = self._read_ammo(frame)
            
            # Kill count
            state['kills'] = self._read_kills(frame)
            
            # Time remaining
            state['time_remaining'] = self._read_time(frame)
            
            # Enemy detection
            state['enemies'] = self._detect_enemies(frame)
            
            # Zone detection
            state['zone_info'] = self._analyze_zone(frame)
            
            # Store in history
            self.stats_history.append(state)
            
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
        
        return state
    
    def _analyze_hp(self, frame):
        """
        Detect HP bar and calculate percentage
        Uses color masking for red HP bars
        """
        result = {'hp_percent': None, 'hp_urgency': 'unknown'}
        
        try:
            x1, y1, x2, y2 = self.regions['hp_bar']
            hp_region = frame[y1:y2, x1:x2]
            
            if hp_region.size == 0:
                return result
            
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(hp_region, cv2.COLOR_BGR2HSV)
            
            # Red color mask (HP bar is typically red when low)
            # Red spans two ranges in HSV: 0-10 and 170-180
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 | mask2
            
            # Find contours
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Largest contour is likely the HP bar
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                
                # Area threshold - ignore small detections
                if area > 5000:  # Minimum 5000 pixels
                    x, y, w, h = cv2.boundingRect(largest)
                    
                    # Calculate HP percentage based on bar width
                    hp_percent = min(100, max(0, (w / hp_region.shape[1]) * 100))
                    result['hp_percent'] = round(hp_percent, 1)
                    
                    # Determine urgency
                    if hp_percent <= 20:
                        result['hp_urgency'] = 'critical'
                    elif hp_percent <= 50:
                        result['hp_urgency'] = 'low'
                    elif hp_percent <= 80:
                        result['hp_urgency'] = 'medium'
                    else:
                        result['hp_urgency'] = 'high'
            
            # Try template matching for HP bar shape
            for template_name in ['hp_red', 'hp_yellow', 'hp_green']:
                if template_name in self.templates:
                    template = self.templates[template_name]
                    match = cv2.matchTemplate(hp_region, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(match)
                    
                    if max_val > 0.8:
                        if template_name == 'hp_red' and result['hp_urgency'] == 'unknown':
                            result['hp_urgency'] = 'critical'
                            result['hp_percent'] = 20
                        break
            
        except Exception as e:
            logger.error(f"HP analysis error: {e}")
        
        return result
    
    def _read_ammo(self, frame):
        """OCR ammo count from bottom-right corner"""
        if not self.ocr_engine:
            return None
        
        try:
            x1, y1, x2, y2 = self.regions['ammo']
            ammo_region = frame[y1:y2, x1:x2]
            
            if ammo_region.size == 0:
                return None
            
            # Preprocess for OCR
            gray = cv2.cvtColor(ammo_region, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # OCR
            text = self.ocr_engine.image_to_string(binary, config=self.ocr_config)
            digits = re.findall(r'\d+', text)
            
            if digits:
                return int(digits[0])
            
        except Exception as e:
            logger.error(f"Ammo OCR error: {e}")
        
        return None
    
    def _read_kills(self, frame):
        """OCR kill count from top-left"""
        if not self.ocr_engine:
            return None
        
        try:
            x1, y1, x2, y2 = self.regions['kills']
            kills_region = frame[y1:y2, x1:x2]
            
            if kills_region.size == 0:
                return None
            
            gray = cv2.cvtColor(kills_region, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            text = self.ocr_engine.image_to_string(binary, config=self.ocr_config)
            digits = re.findall(r'\d+', text)
            
            if digits:
                return int(digits[0])
            
        except Exception as e:
            logger.error(f"Kills OCR error: {e}")
        
        return None
    
    def _read_time(self, frame):
        """OCR time remaining from top-right"""
        if not self.ocr_engine:
            return None
        
        try:
            x1, y1, x2, y2 = self.regions['time']
            time_region = frame[y1:y2, x1:x2]
            
            if time_region.size == 0:
                return None
            
            gray = cv2.cvtColor(time_region, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            # Allow : for time format
            config = '--psm 7 -c tessedit_char_whitelist=0123456789:'
            text = self.ocr_engine.image_to_string(binary, config=config)
            
            return text.strip() if text.strip() else None
            
        except Exception as e:
            logger.error(f"Time OCR error: {e}")
        
        return None
    
    def _detect_enemies(self, frame):
        """
        Detect enemies using template matching
        Returns list of enemy positions with directions
        """
        enemies = []
        
        try:
            x1, y1, x2, y2 = self.regions['center']
            center_region = frame[y1:y2, x1:x2]
            
            if center_region.size == 0:
                return enemies
            
            # Search for enemy templates
            for template_name in ['enemy_head', 'enemy_scope']:
                if template_name not in self.templates:
                    continue
                
                template = self.templates[template_name]
                
                # Template matching
                result = cv2.matchTemplate(center_region, template, cv2.TM_CCOEFF_NORMED)
                
                # Find matches above threshold
                locations = np.where(result >= self.enemy_match_threshold)
                
                for pt in zip(*locations[::-1]):
                    # Calculate relative position
                    rel_x = (pt[0] + template.shape[1] / 2) / center_region.shape[1]
                    rel_y = (pt[1] + template.shape[0] / 2) / center_region.shape[0]
                    
                    # Convert to direction
                    direction = self._calculate_direction(rel_x, rel_y)
                    distance = self._estimate_distance(rel_y)
                    
                    enemy = {
                        'position': (int(pt[0] + x1), int(pt[1] + y1)),
                        'direction': direction,
                        'distance': distance,
                        'confidence': float(result[pt[1], pt[0]])
                    }
                    enemies.append(enemy)
            
            # Non-maximum suppression to remove duplicates
            enemies = self._nms_enemies(enemies)
            
        except Exception as e:
            logger.error(f"Enemy detection error: {e}")
        
        return enemies
    
    def _calculate_direction(self, rel_x, rel_y):
        """Convert relative position to compass direction"""
        # rel_x: 0=left, 1=right
        # rel_y: 0=top, 1=bottom
        
        angle = np.degrees(np.arctan2(rel_y - 0.5, rel_x - 0.5))
        
        # Convert to clock face direction
        if -22.5 <= angle < 22.5:
            return "3 o'clock"
        elif 22.5 <= angle < 67.5:
            return "4 o'clock"
        elif 67.5 <= angle < 112.5:
            return "6 o'clock"
        elif 112.5 <= angle < 157.5:
            return "7 o'clock"
        elif angle >= 157.5 or angle < -157.5:
            return "9 o'clock"
        elif -157.5 <= angle < -112.5:
            return "10 o'clock"
        elif -112.5 <= angle < -67.5:
            return "12 o'clock"
        else:
            return "2 o'clock"
    
    def _estimate_distance(self, rel_y):
        """Estimate distance based on vertical position (lower = closer)"""
        if rel_y < 0.3:
            return "far"
        elif rel_y < 0.6:
            return "medium"
        else:
            return "close"
    
    def _nms_enemies(self, enemies, threshold=50):
        """Non-maximum suppression for enemy detections"""
        if not enemies:
            return []
        
        # Sort by confidence
        enemies = sorted(enemies, key=lambda x: x['confidence'], reverse=True)
        
        filtered = []
        for enemy in enemies:
            # Check if too close to existing detection
            too_close = False
            for kept in filtered:
                dist = np.sqrt(
                    (enemy['position'][0] - kept['position'][0]) ** 2 +
                    (enemy['position'][1] - kept['position'][1]) ** 2
                )
                if dist < threshold:
                    too_close = True
                    break
            
            if not too_close:
                filtered.append(enemy)
        
        return filtered
    
    def _analyze_zone(self, frame):
        """
        Detect blue zone (storm/circle) and its position
        """
        zone_info = {'active': False, 'direction': None, 'closing': False}
        
        try:
            # Check minimap for zone indicator
            x1, y1, x2, y2 = self.regions['minimap']
            minimap = frame[y1:y2, x1:x2]
            
            if minimap.size == 0:
                return zone_info
            
            # Look for blue zone template
            if 'blue_zone' in self.templates:
                template = self.templates['blue_zone']
                result = cv2.matchTemplate(minimap, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > self.zone_match_threshold:
                    zone_info['active'] = True
                    
                    # Calculate zone direction from minimap position
                    rel_x = max_loc[0] / minimap.shape[1]
                    rel_y = max_loc[1] / minimap.shape[0]
                    zone_info['direction'] = self._calculate_direction(rel_x, rel_y)
        
        except Exception as e:
            logger.error(f"Zone analysis error: {e}")
        
        return zone_info
    
    def get_smoothed_stats(self):
        """Get time-averaged stats to reduce noise"""
        if not self.stats_history:
            return None
        
        # Simple average over last few frames
        hp_values = [s['hp_percent'] for s in self.stats_history if s['hp_percent'] is not None]
        enemy_counts = [len(s['enemies']) for s in self.stats_history]
        
        return {
            'avg_hp': np.mean(hp_values) if hp_values else None,
            'max_enemies': max(enemy_counts) if enemy_counts else 0,
            'latest': self.stats_history[-1]
        }


class CommandProcessor:
    """
    Process voice commands and generate responses
    """
    
    def __init__(self, analyzer, voice_engine):
        self.analyzer = analyzer
        self.voice = voice_engine
        self.last_command_time = 0
        self.command_cooldown = 1.0  # seconds
        
        # Command handlers
        self.commands = {
            'health': self.cmd_health,
            'hp': self.cmd_health,
            'enemies': self.cmd_enemies,
            'enemy': self.cmd_enemies,
            'ammo': self.cmd_ammo,
            'bullets': self.cmd_ammo,
            'zone': self.cmd_zone,
            'circle': self.cmd_zone,
            'status': self.cmd_status,
            'report': self.cmd_status,
            'help': self.cmd_help,
        }
    
    def process_command(self, text):
        """Process voice command text"""
        current_time = Clock.get_time()
        
        # Cooldown check
        if current_time - self.last_command_time < self.command_cooldown:
            return
        
        self.last_command_time = current_time
        
        # Parse command
        text = text.lower().strip()
        
        # Check for Jarvis prefix
        if not text.startswith('jarvis'):
            # Try to find command keyword anyway
            for keyword in self.commands:
                if keyword in text:
                    self.commands[keyword](text)
                    return
            return
        
        # Extract command after "Jarvis"
        command_text = text.replace('jarvis', '').strip()
        
        if not command_text:
            self.voice.speak("Yes boss? What do you need?")
            return
        
        # Match command
        for keyword, handler in self.commands.items():
            if keyword in command_text:
                handler(command_text)
                return
        
        # Unknown command
        self.voice.speak("Sorry boss, I didn't understand that command.")
    
    def cmd_health(self, text):
        """Report current health status"""
        stats = self.analyzer.get_smoothed_stats()
        
        if not stats or stats['avg_hp'] is None:
            self.voice.speak("Can't read your HP right now, boss.")
            return
        
        hp = int(stats['avg_hp'])
        
        if hp <= 20:
            self.voice.speak(f"EMERGENCY! Your HP is {hp} percent! Heal immediately!", priority='emergency')
        elif hp <= 50:
            self.voice.speak(f"Warning, your HP is {hp} percent. Consider healing.", priority='high')
        elif hp <= 80:
            self.voice.speak(f"Your HP is {hp} percent. You're okay for now.")
        else:
            self.voice.speak(f"Your HP is {hp} percent. You're in good shape, boss!")
    
    def cmd_enemies(self, text):
        """Report detected enemies"""
        stats = self.analyzer.get_smoothed_stats()
        
        if not stats:
            self.voice.speak("Can't scan for enemies right now.")
            return
        
        latest = stats['latest']
        enemies = latest.get('enemies', [])
        
        if not enemies:
            self.voice.speak("No enemies detected. You're clear, boss.")
            return
        
        # Report most threatening enemy
        priority = 'high' if len(enemies) >= 2 else 'normal'
        
        if len(enemies) == 1:
            e = enemies[0]
            self.voice.speak(
                f"One enemy at {e['direction']}, {e['distance']} range!",
                priority=priority
            )
        else:
            directions = [e['direction'] for e in enemies[:3]]
            dir_text = ', '.join(directions)
            self.voice.speak(
                f"{len(enemies)} enemies detected! At {dir_text}!",
                priority=priority
            )
    
    def cmd_ammo(self, text):
        """Report ammo count"""
        stats = self.analyzer.get_smoothed_stats()
        
        if not stats:
            self.voice.speak("Can't read ammo count right now.")
            return
        
        ammo = stats['latest'].get('ammo_count')
        
        if ammo is None:
            self.voice.speak("Can't read your ammo counter, boss.")
        elif ammo <= 10:
            self.voice.speak(f"Only {ammo} bullets left! Reload soon!", priority='high')
        elif ammo <= 30:
            self.voice.speak(f"You have {ammo} bullets remaining.")
        else:
            self.voice.speak(f"{ammo} bullets. You're well stocked, boss.")
    
    def cmd_zone(self, text):
        """Report zone/circle status"""
        stats = self.analyzer.get_smoothed_stats()
        
        if not stats:
            self.voice.speak("Can't analyze the zone right now.")
            return
        
        zone = stats['latest'].get('zone_info', {})
        time_left = stats['latest'].get('time_remaining')
        
        if not zone.get('active'):
            self.voice.speak("No zone data available right now.")
            return
        
        direction = zone.get('direction', 'unknown')
        
        if time_left:
            self.voice.speak(f"Zone closing from {direction}! {time_left} remaining!", priority='high')
        else:
            self.voice.speak(f"Zone closing from {direction}! Move now!", priority='high')
    
    def cmd_status(self, text):
        """Full status report"""
        stats = self.analyzer.get_smoothed_stats()
        
        if not stats:
            self.voice.speak("Can't analyze game state right now.")
            return
        
        latest = stats['latest']
        
        # Build comprehensive report
        parts = []
        
        # HP
        hp = latest.get('hp_percent')
        if hp is not None:
            parts.append(f"HP {int(hp)} percent")
        
        # Ammo
        ammo = latest.get('ammo_count')
        if ammo is not None:
            parts.append(f"{ammo} bullets")
        
        # Kills
        kills = latest.get('kills')
        if kills is not None:
            parts.append(f"{kills} kills")
        
        # Enemies
        enemies = len(latest.get('enemies', []))
        if enemies > 0:
            parts.append(f"{enemies} enemies spotted")
        
        if parts:
            report = ", ".join(parts)
            self.voice.speak(f"Status: {report}.")
        else:
            self.voice.speak("Scanning in progress, check back in a moment.")
    
    def cmd_help(self, text):
        """List available commands"""
        self.voice.speak(
            "Available commands: health, enemies, ammo, zone, status. "
            "Just say Jarvis followed by the command, boss."
        )
    
    def check_auto_alerts(self):
        """Check for automatic alerts (critical HP, enemies, etc.)"""
        stats = self.analyzer.get_smoothed_stats()
        
        if not stats:
            return
        
        latest = stats['latest']
        
        # Critical HP alert
        hp = latest.get('hp_percent')
        if hp is not None and hp <= 20:
            # Check if we already alerted recently
            self.voice.speak(
                "CRITICAL WARNING! Your health is extremely low! Heal now!",
                priority='emergency'
            )
        
        # Enemy detection alert
        enemies = latest.get('enemies', [])
        if len(enemies) >= 3:
            self.voice.speak(
                f"ALERT! {len(enemies)} enemies detected nearby!",
                priority='high'
            )
