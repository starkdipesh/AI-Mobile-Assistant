"""
Quick validation script for Jarvis Gaming Assistant
Tests core functionality without full unittest framework
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_voice_pipeline():
    """Test voice engine initialization and TTS"""
    print("\n" + "="*60)
    print("TEST 1: Voice Pipeline")
    print("="*60)
    
    try:
        from jarvis.voice import VoiceEngine
        
        commands = []
        def on_cmd(cmd):
            commands.append(cmd)
            print(f"  [CALLBACK] Received: {cmd}")
        
        print("  Initializing VoiceEngine...")
        voice = VoiceEngine(on_command_callback=on_cmd)
        print("  ✓ VoiceEngine initialized")
        
        print("  Testing TTS...")
        voice.speak("Voice test successful", priority='normal')
        print("  ✓ TTS test completed")
        
        print("  Testing command callback...")
        voice._on_speech_result("jarvis health")
        time.sleep(0.1)
        
        if len(commands) == 1 and commands[0] == "jarvis health":
            print("  ✓ Command callback working")
            return True
        else:
            print("  ✗ Command callback failed")
            return False
            
    except Exception as e:
        print(f"  ✗ Voice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_screen_capture():
    """Test screen capture module"""
    print("\n" + "="*60)
    print("TEST 2: Screen Capture")
    print("="*60)
    
    try:
        from jarvis.screen import MockScreenCapture
        
        print("  Initializing MockScreenCapture...")
        capture = MockScreenCapture(fps=15, resolution=(1080, 2340))
        
        print("  Starting capture...")
        capture.start()
        
        print("  Getting frame...")
        frame = capture.get_last_frame()
        
        if frame is not None:
            print(f"  ✓ Frame captured: shape={frame.shape}, dtype={frame.dtype}")
            
            # Verify dimensions
            expected_shape = (2340, 1080, 3)
            if frame.shape == expected_shape:
                print(f"  ✓ Frame dimensions correct: {frame.shape}")
            else:
                print(f"  ⚠ Frame dimensions: got {frame.shape}, expected {expected_shape}")
        else:
            print("  ✗ Frame is None")
            
        print("  Stopping capture...")
        capture.stop()
        print("  ✓ Screen capture test completed")
        return True
        
    except Exception as e:
        print(f"  ✗ Screen capture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_analyzer():
    """Test game analysis module"""
    print("\n" + "="*60)
    print("TEST 3: Game Analysis")
    print("="*60)
    
    try:
        from jarvis.brain import GameAnalyzer
        
        print("  Initializing GameAnalyzer...")
        analyzer = GameAnalyzer()
        print("  ✓ GameAnalyzer initialized")
        
        print("  Testing with blank frame...")
        import numpy as np
        
        # Create test frame
        frame = np.zeros((2340, 1080, 3), dtype=np.uint8)
        
        # Analyze
        state = analyzer.analyze_frame(frame)
        
        if state:
            print(f"  ✓ Analysis returned state with keys: {list(state.keys())}")
            print(f"    HP: {state.get('hp_percent')}")
            print(f"    Enemies: {len(state.get('enemies', []))}")
            print(f"    Urgency: {state.get('hp_urgency')}")
        else:
            print("  ✗ Analysis returned None")
            return False
        
        # Test smoothed stats
        print("  Testing smoothed stats...")
        for i in range(3):
            analyzer.analyze_frame(frame)
            time.sleep(0.01)
        
        stats = analyzer.get_smoothed_stats()
        if stats:
            print(f"  ✓ Smoothed stats: {stats}")
        
        print("  ✓ Game analyzer test completed")
        return True
        
    except Exception as e:
        print(f"  ✗ Game analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_command_processor():
    """Test command processing"""
    print("\n" + "="*60)
    print("TEST 4: Command Processor")
    print("="*60)
    
    try:
        from jarvis.brain import CommandProcessor, GameAnalyzer
        from jarvis.voice import VoiceEngine
        
        print("  Initializing components...")
        voice = VoiceEngine()
        analyzer = GameAnalyzer()
        processor = CommandProcessor(analyzer, voice)
        
        print("  ✓ CommandProcessor initialized")
        
        # Test command processing
        test_commands = [
            "jarvis health",
            "jarvis enemies", 
            "jarvis ammo",
            "jarvis zone",
            "jarvis status"
        ]
        
        print("  Testing commands...")
        for cmd in test_commands:
            print(f"    Processing: {cmd}")
            processor.process_command(cmd)
            time.sleep(0.1)
        
        print("  ✓ Command processor test completed")
        return True
        
    except Exception as e:
        print(f"  ✗ Command processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration"""
    print("\n" + "="*60)
    print("TEST 5: Full Integration")
    print("="*60)
    
    try:
        from jarvis.voice import VoiceEngine
        from jarvis.brain import GameAnalyzer, CommandProcessor
        from jarvis.screen import MockScreenCapture
        
        print("  Initializing all modules...")
        
        # Setup
        voice = VoiceEngine()
        analyzer = GameAnalyzer()
        processor = CommandProcessor(analyzer, voice)
        capture = MockScreenCapture(fps=15)
        
        # Link voice to processor
        voice.on_command_callback = processor.process_command
        
        print("  ✓ All modules initialized and linked")
        
        # Start capture
        print("  Starting screen capture...")
        capture.start()
        
        # Simulate voice command
        print("  Simulating voice command: 'jarvis status'")
        voice._on_speech_result("jarvis status")
        
        time.sleep(0.5)
        
        # Get frame and analyze
        print("  Capturing and analyzing frame...")
        frame = capture.get_last_frame()
        if frame is not None:
            state = analyzer.analyze_frame(frame)
            print(f"  ✓ Frame analyzed: {state}")
        
        capture.stop()
        
        print("  ✓ Integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("JARVIS GAMING ASSISTANT - VALIDATION TESTS")
    print("="*70)
    
    results = {
        'Voice Pipeline': test_voice_pipeline(),
        'Screen Capture': test_screen_capture(),
        'Game Analysis': test_game_analyzer(),
        'Command Processor': test_command_processor(),
        'Integration': test_integration()
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("-"*70)
    print(f"  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("  ✓ ALL TESTS PASSED - System ready!")
        return 0
    else:
        print(f"  ✗ {total - passed} test(s) failed - Review errors above")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
