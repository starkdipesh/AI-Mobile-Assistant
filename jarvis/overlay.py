"""
Jarvis Gaming Assistant - Floating Overlay UI
Phase 5: Draggable floating window with live game stats
"""
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.utils import platform
import logging

logger = logging.getLogger(__name__)


class JarvisOverlay(FloatLayout):
    """
    Floating overlay showing:
    - Status bar (draggable)
    - Live stats (HP, Ammo, Kills, Enemies, Zone)
    - Control buttons
    """
    
    active = BooleanProperty(True)
    opacity_value = NumericProperty(0.9)
    
    def __init__(self, voice_engine, analyzer, **kwargs):
        super().__init__(**kwargs)
        self.voice = voice_engine
        self.analyzer = analyzer
        
        # Stats
        self.current_stats = {
            'hp_percent': None,
            'hp_urgency': 'unknown',
            'ammo_count': None,
            'kills': None,
            'enemies': [],
            'zone_info': None
        }
        
        self._init_ui()
        self._start_update_loop()
        
        # Make window transparent and floating
        self._setup_window()
    
    def _init_ui(self):
        """Initialize overlay UI components"""
        self.size_hint = (None, None)
        self.size = (400, 200)
        self.pos = (50, 50)
        
        # Main container with background
        with self.canvas.before:
            Color(0.1, 0.12, 0.15, 0.95)  # Dark semi-transparent
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[15]
            )
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Root layout
        root = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Header - Draggable + Status
        header = BoxLayout(size_hint_y=0.25, spacing=5)
        
        self.status_label = Label(
            text='JARVIS: ACTIVE',
            font_size=14,
            bold=True,
            color=(0.2, 0.8, 1, 1),  # Cyan
            size_hint_x=0.7
        )
        
        self.drag_handle = Button(
            text='≡',
            font_size=18,
            size_hint_x=0.15,
            background_color=(0.2, 0.2, 0.3, 1)
        )
        self.drag_handle.bind(on_touch_move=self._on_drag)
        
        self.toggle_btn = ToggleButton(
            text='ON',
            state='down',
            size_hint_x=0.15,
            background_color=(0, 0.8, 0, 1)
        )
        self.toggle_btn.bind(on_press=self._on_toggle)
        
        header.add_widget(self.status_label)
        header.add_widget(self.drag_handle)
        header.add_widget(self.toggle_btn)
        
        # Stats display
        self.stats_grid = GridLayout(cols=2, size_hint_y=0.5, spacing=5)
        
        # HP stat
        self.hp_label = Label(
            text='HP: --',
            font_size=12,
            color=(0.5, 0.5, 0.5, 1)
        )
        
        # Ammo stat
        self.ammo_label = Label(
            text='Ammo: --',
            font_size=12,
            color=(0.5, 0.5, 0.5, 1)
        )
        
        # Kills stat
        self.kills_label = Label(
            text='Kills: --',
            font_size=12,
            color=(0.5, 0.5, 0.5, 1)
        )
        
        # Enemy stat
        self.enemy_label = Label(
            text='Enemies: 0',
            font_size=12,
            color=(0, 1, 0, 1)
        )
        
        self.stats_grid.add_widget(self.hp_label)
        self.stats_grid.add_widget(self.ammo_label)
        self.stats_grid.add_widget(self.kills_label)
        self.stats_grid.add_widget(self.enemy_label)
        
        # Zone info
        self.zone_label = Label(
            text='Zone: No data',
            font_size=11,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.15
        )
        
        # Control buttons
        controls = BoxLayout(size_hint_y=0.2, spacing=5)
        
        self.mute_btn = ToggleButton(
            text='🔊',
            state='down',
            font_size=12
        )
        self.mute_btn.bind(on_press=self._on_mute_toggle)
        
        settings_btn = Button(
            text='⚙️',
            font_size=12
        )
        settings_btn.bind(on_press=self._show_settings)
        
        hide_btn = Button(
            text='−',
            font_size=14,
            background_color=(0.8, 0.4, 0, 1)
        )
        hide_btn.bind(on_press=self._minimize)
        
        close_btn = Button(
            text='×',
            font_size=14,
            background_color=(0.8, 0, 0, 1)
        )
        close_btn.bind(on_press=self._close_overlay)
        
        controls.add_widget(self.mute_btn)
        controls.add_widget(settings_btn)
        controls.add_widget(hide_btn)
        controls.add_widget(close_btn)
        
        # Add all to root
        root.add_widget(header)
        root.add_widget(self.stats_grid)
        root.add_widget(self.zone_label)
        root.add_widget(controls)
        
        self.add_widget(root)
    
    def _update_rect(self, instance, value):
        """Update background rectangle position and size"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _setup_window(self):
        """Setup window as floating overlay"""
        try:
            if platform == 'android':
                from jnius import autoclass
                
                # Get activity and window
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                window = activity.getWindow()
                
                # Set as overlay type
                WindowManager = autoclass('android.view.WindowManager')
                LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                
                params = window.getAttributes()
                params.type = LayoutParams.TYPE_APPLICATION_OVERLAY
                params.flags = LayoutParams.FLAG_NOT_FOCUSABLE | LayoutParams.FLAG_NOT_TOUCH_MODAL
                window.setAttributes(params)
                
                # Set transparency
                window.setBackgroundDrawable(
                    autoclass('android.graphics.drawable.ColorDrawable')(0)
                )
                
                # Make window smaller/floating
                params.width = 400
                params.height = 200
                params.x = 50
                params.y = 50
                window.setAttributes(params)
                
        except Exception as e:
            logger.error(f"Window setup error: {e}")
    
    def _on_drag(self, touch):
        """Handle dragging the overlay"""
        if touch.grab_current is self.drag_handle:
            # Update position based on touch movement
            self.x += touch.dx
            self.y += touch.dy
            return True
        return False
    
    def _on_toggle(self, instance):
        """Toggle overlay on/off"""
        self.active = not self.active
        
        if self.active:
            instance.text = 'ON'
            instance.background_color = (0, 0.8, 0, 1)
            self.status_label.text = 'JARVIS: ACTIVE'
            self.status_label.color = (0.2, 0.8, 1, 1)
            self.opacity = self.opacity_value
        else:
            instance.text = 'OFF'
            instance.background_color = (0.8, 0, 0, 1)
            self.status_label.text = 'JARVIS: PAUSED'
            self.status_label.color = (0.8, 0.4, 0, 1)
            self.opacity = 0.3
    
    def _on_mute_toggle(self, instance):
        """Toggle voice alerts"""
        if instance.state == 'down':
            instance.text = '🔊'
            # Unmute voice
            if self.voice:
                self.voice.muted = False
        else:
            instance.text = '🔇'
            # Mute voice
            if self.voice:
                self.voice.muted = True
    
    def _show_settings(self, instance):
        """Show settings popup"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Scrollable content
        scroll = ScrollView()
        settings_box = BoxLayout(orientation='vertical', size_hint_y=None, height=400)
        
        # CV Confidence slider
        cv_box = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        cv_box.add_widget(Label(text='CV Detection Confidence', font_size=12))
        cv_slider = Slider(min=0.5, max=0.95, value=0.8)
        cv_box.add_widget(cv_slider)
        settings_box.add_widget(cv_box)
        
        # TTS Volume slider
        vol_box = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        vol_box.add_widget(Label(text='Voice Volume', font_size=12))
        vol_slider = Slider(min=0, max=1, value=0.8)
        vol_box.add_widget(vol_slider)
        settings_box.add_widget(vol_box)
        
        # Game Profile selector
        profile_box = BoxLayout(orientation='vertical', size_hint_y=None, height=100)
        profile_box.add_widget(Label(text='Game Profile', font_size=12))
        
        from kivy.uix.spinner import Spinner
        profile_spinner = Spinner(
            text='PUBG Mobile',
            values=['PUBG Mobile', 'Free Fire', 'COD Mobile'],
            size_hint_y=None,
            height=40
        )
        profile_box.add_widget(profile_spinner)
        settings_box.add_widget(profile_box)
        
        scroll.add_widget(settings_box)
        content.add_widget(scroll)
        
        # Close button
        close_btn = Button(text='Close', size_hint_y=None, height=40)
        content.add_widget(close_btn)
        
        popup = Popup(
            title='Jarvis Settings',
            content=content,
            size_hint=(0.8, 0.8),
            auto_dismiss=False
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def _minimize(self, instance):
        """Minimize to small indicator"""
        # Animate to minimized state
        anim = Animation(size=(100, 40), duration=0.2)
        anim.start(self)
        
        # Show only status
        self.stats_grid.opacity = 0
        self.zone_label.opacity = 0
        
        # Change minimize button to restore
        instance.text = '+'
        instance.unbind(on_press=self._minimize)
        instance.bind(on_press=self._restore)
    
    def _restore(self, instance):
        """Restore from minimized state"""
        anim = Animation(size=(400, 200), duration=0.2)
        anim.start(self)
        
        self.stats_grid.opacity = 1
        self.zone_label.opacity = 1
        
        instance.text = '−'
        instance.unbind(on_press=self._restore)
        instance.bind(on_press=self._minimize)
    
    def _close_overlay(self, instance):
        """Close the overlay"""
        if self.voice:
            self.voice.speak("Jarvis shutting down. Good luck, boss!")
        
        # Stop services
        App.get_running_app().stop()
    
    def update_stats(self, stats):
        """Update displayed stats from analyzer"""
        self.current_stats = stats
        
        # HP display
        hp = stats.get('hp_percent')
        urgency = stats.get('hp_urgency', 'unknown')
        
        if hp is not None:
            hp_int = int(hp)
            
            if urgency == 'critical':
                self.hp_label.text = f'HP: {hp_int}% ⚠️ CRITICAL'
                self.hp_label.color = (1, 0, 0, 1)  # Red
            elif urgency == 'low':
                self.hp_label.text = f'HP: {hp_int}% ⚠️ LOW'
                self.hp_label.color = (1, 0.5, 0, 1)  # Orange
            elif urgency == 'medium':
                self.hp_label.text = f'HP: {hp_int}%'
                self.hp_label.color = (1, 1, 0, 1)  # Yellow
            else:
                self.hp_label.text = f'HP: {hp_int}% ✓'
                self.hp_label.color = (0, 1, 0, 1)  # Green
        else:
            self.hp_label.text = 'HP: --'
            self.hp_label.color = (0.5, 0.5, 0.5, 1)
        
        # Ammo display
        ammo = stats.get('ammo_count')
        if ammo is not None:
            if ammo <= 10:
                self.ammo_label.text = f'Ammo: {ammo} ⚠️'
                self.ammo_label.color = (1, 0.5, 0, 1)
            else:
                self.ammo_label.text = f'Ammo: {ammo}'
                self.ammo_label.color = (0, 1, 0, 1)
        else:
            self.ammo_label.text = 'Ammo: --'
            self.ammo_label.color = (0.5, 0.5, 0.5, 1)
        
        # Kills display
        kills = stats.get('kills')
        if kills is not None:
            self.kills_label.text = f'Kills: {kills}'
            self.kills_label.color = (1, 0.8, 0, 1)  # Gold
        else:
            self.kills_label.text = 'Kills: --'
            self.kills_label.color = (0.5, 0.5, 0.5, 1)
        
        # Enemy display
        enemies = stats.get('enemies', [])
        enemy_count = len(enemies)
        
        if enemy_count > 0:
            # Get direction of closest/most threatening
            if enemies:
                closest = min(enemies, key=lambda e: e.get('distance', 'far'))
                direction = closest.get('direction', 'unknown')
                self.enemy_label.text = f'Enemies: {enemy_count} @ {direction}'
            else:
                self.enemy_label.text = f'Enemies: {enemy_count}'
            
            if enemy_count >= 2:
                self.enemy_label.color = (1, 0, 0, 1)  # Red
            else:
                self.enemy_label.color = (1, 0.5, 0, 1)  # Orange
        else:
            self.enemy_label.text = 'Enemies: 0'
            self.enemy_label.color = (0, 1, 0, 1)  # Green
        
        # Zone display
        zone = stats.get('zone_info', {})
        if zone.get('active'):
            direction = zone.get('direction', 'unknown')
            self.zone_label.text = f'Zone: Closing from {direction}!'
            self.zone_label.color = (1, 0, 0, 1)  # Red alert
        else:
            self.zone_label.text = 'Zone: No data'
            self.zone_label.color = (0.5, 0.5, 0.5, 1)
    
    def _start_update_loop(self):
        """Start periodic UI update loop"""
        Clock.schedule_interval(self._update_loop, 1.0 / 15)  # 15 FPS
    
    def _update_loop(self, dt):
        """Periodic update from analyzer"""
        if not self.active or not self.analyzer:
            return
        
        # Get latest stats
        stats = self.analyzer.get_smoothed_stats()
        if stats:
            self.update_stats(stats['latest'])


class OverlayService:
    """
    Android Foreground Service wrapper for overlay
    """
    
    def __init__(self):
        self.overlay = None
        self.running = False
    
    def start(self, voice_engine, analyzer):
        """Start the overlay service"""
        try:
            if platform == 'android':
                from jnius import autoclass
                
                # Create notification for foreground service
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                NotificationBuilder = autoclass('android.app.Notification$Builder')
                NotificationManager = autoclass('android.app.NotificationManager')
                Context = autoclass('android.content.Context')
                
                activity = PythonActivity.mActivity
                notification_manager = activity.getSystemService(Context.NOTIFICATION_SERVICE)
                
                # Build notification
                builder = NotificationBuilder(activity)
                builder.setContentTitle("Jarvis Gaming Assistant")
                builder.setContentText("Active and monitoring")
                builder.setSmallIcon(activity.getApplicationInfo().icon)
                
                notification = builder.build()
                
                # Start foreground
                Service = autoclass('org.kivy.android.PythonService')
                Service.startForeground(1, notification)
            
            self.overlay = JarvisOverlay(voice_engine, analyzer)
            self.running = True
            
        except Exception as e:
            logger.error(f"Overlay service start failed: {e}")
    
    def stop(self):
        """Stop the overlay service"""
        self.running = False
        if self.overlay:
            self.overlay = None
