"""
Sarth Gaming Assistant - Main Application
Kivy App entry point integrating all modules
"""
import os
import sys
import logging
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.properties import StringProperty, BooleanProperty

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure sarth modules are in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sarth.voice import VoiceEngine, MockSTT
from sarth.screen import SarthScreenCapture, MockScreenCapture
from sarth.brain import GameAnalyzer, CommandProcessor
from sarth.overlay import SarthOverlay


class SarthApp(App):
    """
    Main Sarth Gaming Assistant Application
    Integrates Voice, Screen Capture, Game Analysis, and Overlay UI
    """
    
    status_text = StringProperty("Initializing...")
    service_running = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voice = None
        self.screen_capture = None
        self.analyzer = None
        self.processor = None
        self.overlay = None
        self.alert_check_event = None
        
    def build(self):
        """Build main application UI (launcher screen)"""
        # Window settings
        Window.clearcolor = (0.05, 0.05, 0.08, 1)
        Window.size = (400, 600)
        
        # Main layout
        root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Title
        title = Label(
            text='[b]JARVIS GAMING ASSISTANT[/b]',
            markup=True,
            font_size=24,
            color=(0.2, 0.8, 1, 1),
            size_hint_y=0.1
        )
        root.add_widget(title)
        
        # Status display
        self.status_label = Label(
            text=self.status_text,
            font_size=14,
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=0.08
        )
        root.add_widget(self.status_label)
        
        # Info panel
        info = Label(
            text='Voice: "Sarth" wake word\nCommands: health, enemies, ammo, zone, status',
            font_size=12,
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=0.15,
            halign='center'
        )
        root.add_widget(info)
        
        # Main controls
        controls = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.4)
        
        self.start_btn = Button(
            text='▶ START SARTH',
            font_size=16,
            background_color=(0, 0.7, 0, 1),
            size_hint_y=0.25
        )
        self.start_btn.bind(on_press=self.start_service)
        
        self.stop_btn = Button(
            text='⏹ STOP SARTH',
            font_size=16,
            background_color=(0.7, 0, 0, 1),
            disabled=True,
            size_hint_y=0.25
        )
        self.stop_btn.bind(on_press=self.stop_service)
        
        test_voice_btn = Button(
            text='🔊 Test Voice',
            font_size=14,
            size_hint_y=0.2
        )
        test_voice_btn.bind(on_press=self.test_voice)
        
        permissions_btn = Button(
            text='🔐 Check Permissions',
            font_size=14,
            size_hint_y=0.2
        )
        permissions_btn.bind(on_press=self.check_permissions)
        
        controls.add_widget(self.start_btn)
        controls.add_widget(self.stop_btn)
        controls.add_widget(test_voice_btn)
        controls.add_widget(permissions_btn)
        
        root.add_widget(controls)
        
        # Test commands section
        test_section = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.25)
        test_section.add_widget(Label(text='Quick Test Commands:', font_size=12, color=(0.7, 0.7, 0.7, 1)))
        
        test_grid = BoxLayout(spacing=5)
        
        cmds = ['health', 'enemies', 'ammo', 'zone', 'status']
        for cmd in cmds:
            btn = Button(text=cmd, font_size=11)
            btn.bind(on_press=lambda inst, c=cmd: self.simulate_command(c))
            test_grid.add_widget(btn)
        
        test_section.add_widget(test_grid)
        root.add_widget(test_section)
        
        # Footer
        footer = Label(
            text='v1.0 | PUBG/FreeFire/COD Mobile',
            font_size=10,
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.05
        )
        root.add_widget(footer)
        
        # Bind status property
        self.bind(status_text=self.status_label.setter('text'))
        self.bind(service_running=self._update_ui_state)
        
        # Initialize modules
        Clock.schedule_once(self._initialize_modules, 0.5)
        
        return root
    
    def _update_ui_state(self, instance, value):
        """Update UI based on service state"""
        self.start_btn.disabled = value
        self.stop_btn.disabled = not value
        
        if value:
            self.start_btn.background_color = (0.3, 0.3, 0.3, 1)
            self.stop_btn.background_color = (0.7, 0, 0, 1)
        else:
            self.start_btn.background_color = (0, 0.7, 0, 1)
            self.stop_btn.background_color = (0.3, 0.3, 0.3, 1)
    
    def _initialize_modules(self, dt):
        """Initialize all Sarth modules"""
        try:
            self.status_text = "Initializing voice engine..."
            
            # Initialize voice (Phase 1)
            self.voice = VoiceEngine(on_command_callback=self._on_voice_command)
            
            self.status_text = "Initializing screen capture..."
            
            # Initialize screen capture (auto-detects platform)
            try:
                self.screen_capture = SarthScreenCapture(fps=15, monitor=1, resolution=(1920, 1080))
                self.screen_capture.register_callback(self._on_new_frame)
                logger.info("Screen capture initialized (auto-detected platform)")
            except Exception as e:
                logger.warning(f"Screen capture init failed: {e}, using mock")
                self.screen_capture = MockScreenCapture(fps=15, resolution=(1920, 1080))
            
            self.status_text = "Initializing game analyzer..."
            
            # Initialize game analyzer (Phase 3)
            templates_dir = os.path.join(os.path.dirname(__file__), 'assets', 'game_templates')
            self.analyzer = GameAnalyzer(templates_dir=templates_dir)
            
            # Initialize command processor (Phase 4)
            self.processor = CommandProcessor(self.analyzer, self.voice)
            
            self.status_text = "Ready to start. Press START SARTH."
            
        except Exception as e:
            logger.error(f"Module initialization failed: {e}")
            self.status_text = f"Init failed: {str(e)[:50]}"
    
    def start_service(self, instance):
        """Start Sarth services"""
        if not self.voice or not self.analyzer:
            self._initialize_modules(0)
            return
        
        try:
            self.status_text = "Starting voice pipeline..."
            
            # Start voice
            self.voice.start()
            
            self.status_text = "Starting screen capture..."
            
            # Start screen capture
            if self.screen_capture:
                self.screen_capture.start()
            
            self.status_text = "Launching overlay..."
            
            # Create overlay (Phase 5)
            self.overlay = SarthOverlay(
                voice_engine=self.voice,
                analyzer=self.analyzer
            )
            
            # Start auto-alert checking
            self.alert_check_event = Clock.schedule_interval(self._check_alerts, 2.0)
            
            self.service_running = True
            self.status_text = "SARTH IS ACTIVE - Say 'Sarth health' to test"
            
            # Welcome message
            Clock.schedule_once(lambda dt: self.voice.speak("Sarth online. Ready to assist, boss!"), 1.0)
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            self.status_text = f"Start failed: {str(e)[:50]}"
    
    def stop_service(self, instance):
        """Stop all Sarth services"""
        try:
            self.status_text = "Stopping services..."
            
            if self.voice:
                self.voice.stop()
            
            if self.screen_capture:
                self.screen_capture.stop()
            
            if self.overlay:
                self.overlay = None
            
            if self.alert_check_event:
                Clock.unschedule(self.alert_check_event)
                self.alert_check_event = None
            
            self.service_running = False
            self.status_text = "Sarth stopped. Ready to restart."
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            self.status_text = f"Stop error: {str(e)[:50]}"
    
    def test_voice(self, instance):
        """Test voice synthesis"""
        if self.voice:
            self.voice.speak("Voice test successful. Sarth is ready, boss!", priority='high')
            self.status_text = "Voice test playing..."
        else:
            self.status_text = "Voice not initialized!"
    
    def check_permissions(self, instance):
        """Check and request required permissions"""
        if platform != 'android':
            self.status_text = "Permissions only needed on Android"
            return
        
        try:
            from android.permissions import Permission, request_permissions, check_permission
            
            permissions = [
                Permission.RECORD_AUDIO,
                Permission.SYSTEM_ALERT_WINDOW,
                Permission.FOREGROUND_SERVICE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ]
            
            # Check current permissions
            missing = [p for p in permissions if not check_permission(p)]
            
            if missing:
                request_permissions(missing, self._on_permissions_result)
                self.status_text = f"Requesting {len(missing)} permissions..."
            else:
                self.status_text = "All permissions granted!"
                
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            self.status_text = f"Permission error: {str(e)[:40]}"
    
    def _on_permissions_result(self, permissions, grants):
        """Callback for permission requests"""
        granted = sum(grants)
        total = len(grants)
        self.status_text = f"Permissions: {granted}/{total} granted"
        
        if granted < total:
            self._show_permission_popup()
    
    def _show_permission_popup(self):
        """Show permission instructions popup"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        msg = Label(
            text='Sarth needs these permissions:\n\n'
                 '• Microphone - Voice commands\n'
                 '• Overlay - Floating UI\n'
                 '• Storage - Screen capture\n\n'
                 'Please enable in Settings > Apps > Sarth',
            halign='left',
            font_size=14
        )
        content.add_widget(msg)
        
        close_btn = Button(text='OK', size_hint_y=0.2)
        content.add_widget(close_btn)
        
        popup = Popup(
            title='Permissions Required',
            content=content,
            size_hint=(0.8, 0.6)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def simulate_command(self, command):
        """Simulate a voice command for testing"""
        if not self.processor:
            self.status_text = "Start Sarth first!"
            return
        
        self._on_voice_command(f"sarth {command}")
        self.status_text = f"Simulated: '{command}'"
    
    def _on_voice_command(self, text):
        """Handle voice command callback"""
        logger.info(f"Voice command received: {text}")
        
        if self.processor:
            self.processor.process_command(text)
        
        Clock.schedule_once(lambda dt: setattr(
            self, 'status_text', f"Command: {text[:40]}"
        ), 0)
    
    def _on_new_frame(self, frame):
        """Handle new screen frame callback"""
        if self.analyzer:
            self.analyzer.analyze_frame(frame)
    
    def _check_alerts(self, dt):
        """Periodic check for automatic alerts"""
        if self.processor:
            self.processor.check_auto_alerts()
    
    def on_stop(self):
        """App is closing"""
        self.stop_service(None)
        return True


def main():
    """Application entry point"""
    # Android-specific setup
    if platform == 'android':
        try:
            import android
            from jnius import autoclass
            
            # Keep screen on
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            WindowManager = autoclass('android.view.WindowManager')
            LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
            
            activity.getWindow().addFlags(LayoutParams.FLAG_KEEP_SCREEN_ON)
            
        except Exception as e:
            logger.warning(f"Android setup error: {e}")
    
    # Run app
    SarthApp().run()


if __name__ == '__main__':
    main()
