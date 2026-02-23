"""
Jarvis Gaming Assistant - Test Suite
Comprehensive testing for voice, screen, and analysis modules
"""
import os
import sys
import time
import threading
import unittest
import numpy as np
from unittest.mock import MagicMock, patch
import logging

# Setup detailed logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jarvis_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis.voice import VoiceEngine, MockTTS, MockSTT
from jarvis.brain import GameAnalyzer, CommandProcessor
from jarvis.screen import MockScreenCapture


class TestVoicePipeline(unittest.TestCase):
    """Test Phase 1: Voice Pipeline (Wake Word + STT + TTS)"""
    
    def setUp(self):
        """Set up test fixtures"""
        logger.info("\n" + "="*60)
        logger.info("SETTING UP VOICE PIPELINE TESTS")
        logger.info("="*60)
        self.commands_received = []
        
    def test_voice_engine_initialization(self):
        """Test VoiceEngine initializes correctly"""
        logger.info("[TEST] VoiceEngine initialization")
        
        def on_command(cmd):
            self.commands_received.append(cmd)
            logger.info(f"[CALLBACK] Command received: {cmd}")
        
        voice = VoiceEngine(on_command_callback=on_command)
        
        # Check components initialized
        self.assertIsNotNone(voice)
        self.assertIsNotNone(voice.tts)
        self.assertIsNotNone(voice.stt)
        logger.info("✓ VoiceEngine initialized successfully")
        
    def test_tts_speak(self):
        """Test TTS can speak text"""
        logger.info("[TEST] TTS speech synthesis")
        
        voice = VoiceEngine()
        
        # Test different priority levels
        test_messages = [
            ("Emergency test", 'emergency'),
            ("High priority test", 'high'),
            ("Normal message test", 'normal'),
            ("Low priority info", 'low')
        ]
        
        for message, priority in test_messages:
            logger.info(f"  Speaking ({priority}): {message}")
            voice.speak(message, priority=priority)
            time.sleep(0.1)  # Small delay between messages
            
        logger.info("✓ TTS speak test completed")
        
    def test_stt_simulation(self):
        """Test STT command recognition simulation"""
        logger.info("[TEST] STT command simulation")
        
        self.received_command = None
        
        def on_command(cmd):
            self.received_command = cmd
            logger.info(f"[CALLBACK] STT received: {cmd}")
        
        voice = VoiceEngine(on_command_callback=on_command)
        
        # Simulate commands
        test_commands = [
            "jarvis health",
            "jarvis enemies",
            "jarvis ammo",
            "jarvis zone",
            "jarvis status"
        ]
        
        for cmd in test_commands:
            logger.info(f"  Simulating: {cmd}")
            voice._on_speech_result(cmd)
            time.sleep(0.1)
            self.assertEqual(self.received_command, cmd)
            
        logger.info("✓ STT simulation test passed")
        
    def test_command_callback(self):
        """Test full command flow from wake word to callback"""
        logger.info("[TEST] Full voice command flow")
        
        commands = []
        
        def on_command(cmd):
            commands.append(cmd)
            logger.info(f"[FLOW] Command processed: {cmd}")
        
        voice = VoiceEngine(on_command_callback=on_command)
        
        # Simulate wake word detection
        logger.info("  Simulating wake word detection...")
        voice._on_wake_detected()
        
        # Simulate speech result
        test_cmd = "jarvis health"
        voice._on_speech_result(test_cmd)
        
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], test_cmd)
        
        logger.info("✓ Command flow test passed")


class TestScreenCapture(unittest.TestCase):
    """Test Phase 2: Screen Capture"""
    
    def setUp(self):
        logger.info("\n" + "="*60)
        logger.info("SETTING UP SCREEN CAPTURE TESTS")
        logger.info("="*60)
        
    def test_mock_screen_capture(self):
        """Test mock screen capture"""
        logger.info("[TEST] Mock Screen Capture")
        
        capture = MockScreenCapture(fps=15, resolution=(1080, 2340))
        
        # Test start/stop
        capture.start()
        self.assertTrue(capture.running)
        logger.info("✓ Screen capture started")
        
        # Get frame
        frame = capture.get_last_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (2340, 1080, 3))
        logger.info(f"✓ Frame captured: {frame.shape}")
        
        capture.stop()
        self.assertFalse(capture.running)
        logger.info("✓ Screen capture stopped")
        
    def test_frame_callback(self):
        """Test frame callback system"""
        logger.info("[TEST] Frame callbacks")
        
        frames_received = []
        
        def on_frame(frame):
            frames_received.append(frame)
            logger.info(f"[CALLBACK] Frame received: {frame.shape if frame is not None else 'None'}")
        
        capture = MockScreenCapture(fps=15)
        capture.register_callback(on_frame)
        
        capture.start()
        time.sleep(0.5)  # Wait for a few frames
        capture.stop()
        
        logger.info(f"✓ Received {len(frames_received)} frames via callback")
        self.assertGreater(len(frames_received), 0)


class TestGameAnalysis(unittest.TestCase):
    """Test Phase 3: Game Analysis (CV + OCR)"""
    
    def setUp(self):
        logger.info("\n" + "="*60)
        logger.info("SETTING UP GAME ANALYSIS TESTS")
        logger.info("="*60)
        
        # Create test analyzer
        self.analyzer = GameAnalyzer(templates_dir='../assets/game_templates')
        
    def test_analyzer_initialization(self):
        """Test GameAnalyzer initializes correctly"""
        logger.info("[TEST] GameAnalyzer initialization")
        
        self.assertIsNotNone(self.analyzer)
        self.assertIsNotNone(self.analyzer.regions)
        logger.info(f"✓ Analyzer regions: {list(self.analyzer.regions.keys())}")
        
    def test_hp_detection(self):
        """Test HP bar detection with synthetic images"""
        logger.info("[TEST] HP Detection")
        
        # Create synthetic frames with different HP levels
        def create_hp_frame(hp_level):
            """Create synthetic frame with HP bar"""
            frame = np.zeros((2340, 1080, 3), dtype=np.uint8)
            
            # Draw HP bar region (bottom-left)
            x1, y1, x2, y2 = 50, 1950, 400, 2100
            
            if hp_level == 'critical':
                color = (0, 0, 255)  # Red in BGR
                width = int((x2-x1) * 0.2)
            elif hp_level == 'low':
                color = (0, 255, 255)  # Yellow
                width = int((x2-x1) * 0.5)
            elif hp_level == 'high':
                color = (0, 255, 0)  # Green
                width = int((x2-x1) * 0.9)
            else:
                return frame
                
            # Draw HP bar
            cv2.rectangle(frame, (x1, y1), (x1 + width, y2), color, -1)
            
            return frame
        
        try:
            import cv2
            
            # Test critical HP
            frame = create_hp_frame('critical')
            result = self.analyzer._analyze_hp(frame)
            logger.info(f"  Critical HP result: {result}")
            self.assertEqual(result['hp_urgency'], 'critical')
            
            # Test low HP
            frame = create_hp_frame('low')
            result = self.analyzer._analyze_hp(frame)
            logger.info(f"  Low HP result: {result}")
            self.assertEqual(result['hp_urgency'], 'low')
            
            # Test high HP
            frame = create_hp_frame('high')
            result = self.analyzer._analyze_hp(frame)
            logger.info(f"  High HP result: {result}")
            self.assertEqual(result['hp_urgency'], 'high')
            
            logger.info("✓ HP detection tests passed")
            
        except ImportError:
            logger.warning("OpenCV not available, skipping HP detection test")
            
    def test_full_analysis(self):
        """Test full frame analysis"""
        logger.info("[TEST] Full frame analysis")
        
        # Create a test frame
        frame = np.zeros((2340, 1080, 3), dtype=np.uint8)
        
        # Add some test data
        # HP bar (red, low)
        cv2.rectangle(frame, (50, 1950), (150, 2100), (0, 0, 255), -1)
        
        # Ammo text area
        cv2.rectangle(frame, (800, 2100), (1050, 2250), (200, 200, 200), -1)
        
        # Analyze
        state = self.analyzer.analyze_frame(frame)
        
        logger.info(f"  Analysis result keys: {list(state.keys())}")
        self.assertIsNotNone(state)
        self.assertIn('hp_percent', state)
        self.assertIn('enemies', state)
        self.assertIn('timestamp', state)
        
        logger.info("✓ Full analysis test completed")
        
    def test_smoothed_stats(self):
        """Test time-averaged statistics"""
        logger.info("[TEST] Smoothed stats calculation")
        
        # Add multiple frames to history
        for i in range(5):
            frame = np.zeros((2340, 1080, 3), dtype=np.uint8)
            state = self.analyzer.analyze_frame(frame)
            time.sleep(0.01)
            
        stats = self.analyzer.get_smoothed_stats()
        
        if stats:
            logger.info(f"  Smoothed stats: {stats}")
            self.assertIn('latest', stats)
            logger.info("✓ Smoothed stats test passed")
        else:
            logger.warning("No stats history available")


class TestCommandProcessor(unittest.TestCase):
    """Test Phase 4: Command Processing"""
    
    def setUp(self):
        logger.info("\n" + "="*60)
        logger.info("SETTING UP COMMAND PROCESSOR TESTS")
        logger.info("="*60)
        
        # Create mock components
        self.mock_analyzer = MagicMock()
        self.mock_analyzer.get_smoothed_stats.return_value = {
            'avg_hp': 45.5,
            'max_enemies': 2,
            'latest': {
                'hp_percent': 45.5,
                'hp_urgency': 'low',
                'ammo_count': 12,
                'kills': 3,
                'enemies': [
                    {'direction': '3 o\'clock', 'distance': 'close'},
                    {'direction': '9 o\'clock', 'distance': 'medium'}
                ],
                'zone_info': {'active': True, 'direction': 'north'}
            }
        }
        
        self.mock_voice = MagicMock()
        self.processor = CommandProcessor(self.mock_analyzer, self.mock_voice)
        
    def test_command_health(self):
        """Test 'health' command processing"""
        logger.info("[TEST] Health command")
        
        self.processor.cmd_health("jarvis health")
        
        # Check voice.speak was called
        self.mock_voice.speak.assert_called()
        call_args = self.mock_voice.speak.call_args
        logger.info(f"  Voice response: {call_args}")
        
        logger.info("✓ Health command test passed")
        
    def test_command_enemies(self):
        """Test 'enemies' command processing"""
        logger.info("[TEST] Enemies command")
        
        self.processor.cmd_enemies("jarvis enemies")
        
        self.mock_voice.speak.assert_called()
        call_args = self.mock_voice.speak.call_args
        logger.info(f"  Voice response: {call_args}")
        
        logger.info("✓ Enemies command test passed")
        
    def test_command_ammo(self):
        """Test 'ammo' command processing"""
        logger.info("[TEST] Ammo command")
        
        self.processor.cmd_ammo("jarvis ammo")
        
        self.mock_voice.speak.assert_called()
        call_args = self.mock_voice.speak.call_args
        logger.info(f"  Voice response: {call_args}")
        
        logger.info("✓ Ammo command test passed")
        
    def test_command_zone(self):
        """Test 'zone' command processing"""
        logger.info("[TEST] Zone command")
        
        self.processor.cmd_zone("jarvis zone")
        
        self.mock_voice.speak.assert_called()
        call_args = self.mock_voice.speak.call_args
        logger.info(f"  Voice response: {call_args}")
        
        logger.info("✓ Zone command test passed")
        
    def test_command_status(self):
        """Test 'status' command processing"""
        logger.info("[TEST] Status command")
        
        self.processor.cmd_status("jarvis status")
        
        self.mock_voice.speak.assert_called()
        call_args = self.mock_voice.speak.call_args
        logger.info(f"  Voice response: {call_args}")
        
        logger.info("✓ Status command test passed")


class TestIntegration(unittest.TestCase):
    """Test full system integration"""
    
    def setUp(self):
        logger.info("\n" + "="*60)
        logger.info("SETTING UP INTEGRATION TESTS")
        logger.info("="*60)
        
    def test_voice_to_command_flow(self):
        """Test complete voice → analysis → response flow"""
        logger.info("[TEST] Voice to Command integration")
        
        commands_processed = []
        
        def on_command(cmd):
            commands_processed.append(cmd)
            logger.info(f"[INTEGRATION] Processing: {cmd}")
        
        # Initialize components
        voice = VoiceEngine(on_command_callback=on_command)
        analyzer = GameAnalyzer()
        processor = CommandProcessor(analyzer, voice)
        
        # Link processor to voice
        voice.on_command_callback = processor.process_command
        
        # Simulate voice commands
        test_cmds = [
            "jarvis health",
            "jarvis enemies",
            "jarvis ammo"
        ]
        
        for cmd in test_cmds:
            logger.info(f"  Simulating: {cmd}")
            voice._on_speech_result(cmd)
            time.sleep(0.2)
            
        logger.info(f"✓ Processed {len(commands_processed)} commands")
        self.assertEqual(len(commands_processed), len(test_cmds))
        
    def test_frame_to_analysis_flow(self):
        """Test screen → analysis → stats flow"""
        logger.info("[TEST] Screen to Analysis integration")
        
        analyzer = GameAnalyzer()
        capture = MockScreenCapture(fps=15)
        
        frames_analyzed = []
        
        def on_frame(frame):
            state = analyzer.analyze_frame(frame)
            frames_analyzed.append(state)
            logger.info(f"[INTEGRATION] Frame analyzed: HP={state.get('hp_percent')}, Enemies={len(state.get('enemies', []))}")
        
        capture.register_callback(on_frame)
        
        capture.start()
        time.sleep(1.0)  # Collect frames for 1 second
        capture.stop()
        
        logger.info(f"✓ Analyzed {len(frames_analyzed)} frames")
        self.assertGreater(len(frames_analyzed), 10)  # Should get ~15 frames


def run_tests():
    """Run all tests with detailed output"""
    logger.info("\n" + "="*70)
    logger.info("JARVIS GAMING ASSISTANT - COMPREHENSIVE TEST SUITE")
    logger.info("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVoicePipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestScreenCapture))
    suite.addTests(loader.loadTestsFromTestCase(TestGameAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        logger.info("✓ ALL TESTS PASSED")
    else:
        logger.error("✗ SOME TESTS FAILED")
        
    return result.wasSuccessful()


def run_interactive_test():
    """Run interactive test with keyboard simulation"""
    logger.info("\n" + "="*70)
    logger.info("INTERACTIVE TEST MODE")
    logger.info("="*70)
    logger.info("Testing voice commands. Type commands to simulate voice input.")
    logger.info("Commands: health, enemies, ammo, zone, status, quit")
    logger.info("-"*70)
    
    from jarvis.brain import CommandProcessor
    from jarvis.voice import VoiceEngine
    
    # Setup
    voice = VoiceEngine()
    analyzer = GameAnalyzer()
    processor = CommandProcessor(analyzer, voice)
    
    voice.on_command_callback = processor.process_command
    
    # Simulate commands
    while True:
        try:
            cmd = input("\nEnter command (or 'quit'): ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd in ['health', 'enemies', 'ammo', 'zone', 'status']:
                full_cmd = f"jarvis {cmd}"
                logger.info(f"Simulating: {full_cmd}")
                voice._on_speech_result(full_cmd)
            else:
                logger.info("Unknown command. Try: health, enemies, ammo, zone, status")
                
        except KeyboardInterrupt:
            break
        except EOFError:
            break
    
    logger.info("\nInteractive test completed.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Jarvis Test Suite')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run interactive test')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.interactive:
        run_interactive_test()
    else:
        success = run_tests()
        sys.exit(0 if success else 1)
