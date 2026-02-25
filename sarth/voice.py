"""
Sarth Gaming Assistant - Voice Pipeline
Phase 1: Wake Word + STT + TTS
"""
import threading
import queue
import numpy as np
import logging
import time

# Try to import Kivy, fallback to threading if not available
try:
    from kivy.clock import Clock
    HAS_KIVY = True
except ImportError:
    HAS_KIVY = False
    # Simple Clock fallback for testing
    class MockClock:
        @staticmethod
        def schedule_once(callback, timeout):
            timer = threading.Timer(timeout, callback, args=[0])
            timer.start()
            return timer
        
        @staticmethod
        def schedule_interval(callback, interval):
            def loop():
                while True:
                    callback(0)
                    time.sleep(interval)
            t = threading.Thread(target=loop, daemon=True)
            t.start()
            return t
        
        @staticmethod
        def get_time():
            return time.time()
    
    Clock = MockClock()

logger = logging.getLogger(__name__)


class VoiceEngine:
    """
    Voice Pipeline:
    1. Wake Word Detection (Porcupine)
    2. Speech-to-Text (Android SpeechRecognizer)
    3. Text-to-Speech (Android TTS)
    """
    
    def __init__(self, on_command_callback=None):
        self.on_command_callback = on_command_callback
        self.is_listening = False
        self.wake_word_detector = None
        self.stt = None
        self.tts = None
        self.audio_queue = queue.Queue()
        self.wake_thread = None
        self.command_queue = queue.Queue()
        self.speaking = False
        
        # Configuration
        self.wake_sensitivity = 0.5
        self.stt_timeout = 3.0
        self.audio_buffer_size = 512
        self.sample_rate = 16000
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize TTS, STT, and Wake Word engines"""
        try:
            self._init_tts()
            self._init_stt()
            self._init_wake_word()
            logger.info("Voice engines initialized successfully")
        except Exception as e:
            logger.error(f"Voice engine initialization failed: {e}")
    
    def _init_tts(self):
        """Initialize Text-to-Speech - Android first, then Desktop fallback"""
        try:
            from pykivdroid import TTS
            self.tts = TTS(voice='en-us-x-tpd-local')
            logger.info("Android TTS initialized")
        except ImportError:
            logger.info("pykivdroid not available, trying DesktopTTS")
            try:
                self.tts = DesktopTTS()
                logger.info("Desktop TTS initialized (pyttsx3)")
            except Exception as e:
                logger.warning(f"Desktop TTS failed: {e}, using MockTTS")
                self.tts = MockTTS()
    
    def _init_stt(self):
        """Initialize Speech-to-Text (offline preferred)"""
        try:
            from pykivdroid import STT
            self.stt = STT(prefer_offline=True, language='en-US')
            self.stt.on_partial_result = self._on_partial_result
            self.stt.on_result = self._on_speech_result
            self.stt.on_error = self._on_speech_error
            logger.info("STT initialized")
        except ImportError:
            logger.warning("pykivdroid not available, using mock STT")
            self.stt = MockSTT(self._on_speech_result)
    
    def _init_wake_word(self):
        """Initialize Porcupine wake word detector"""
        try:
            import pvporcupine
            # Access key should be set in environment or config
            self.wake_word_detector = pvporcupine.create(
                keyword_paths=['assets/jarvis_linux.ppn'],
                sensitivities=[self.wake_sensitivity]
            )
            logger.info("Wake word detector initialized")
        except Exception as e:
            logger.warning(f"Porcupine not available: {e}, using mock wake word")
            self.wake_word_detector = MockWakeWord(self._on_wake_detected)
    
    def start(self):
        """Start the voice pipeline"""
        self.is_listening = True
        self._start_wake_word_thread()
        logger.info("Voice pipeline started")
    
    def stop(self):
        """Stop all voice processing"""
        self.is_listening = False
        if self.wake_thread and self.wake_thread.is_alive():
            self.wake_thread.join(timeout=1.0)
        if self.stt:
            self.stt.stop_listening()
        logger.info("Voice pipeline stopped")
    
    def _start_wake_word_thread(self):
        """Start wake word detection in background thread"""
        self.wake_thread = threading.Thread(target=self._wake_word_loop, daemon=True)
        self.wake_thread.start()
    
    def _wake_word_loop(self):
        """Background loop for wake word detection"""
        try:
            import sounddevice as sd
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                self.audio_queue.put(indata.copy())
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.audio_buffer_size,
                dtype=np.float32,
                channels=1,
                callback=audio_callback
            ):
                logger.info("Audio stream started for wake word detection")
                
                while self.is_listening:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        if self.wake_word_detector and not isinstance(self.wake_word_detector, MockWakeWord):
                            pcm = (data * 32767).astype(np.int16).flatten()
                            keyword_index = self.wake_word_detector.process(pcm)
                            
                            if keyword_index >= 0:
                                Clock.schedule_once(lambda dt: self._on_wake_detected(), 0)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Wake word processing error: {e}")
                        
        except ImportError:
            logger.warning("sounddevice not available, using mock audio")
            # Mock wake word detection for testing
            import time
            while self.is_listening:
                time.sleep(5)  # Simulate periodic wake word detection
        
        except Exception as e:
            logger.error(f"Wake word loop error: {e}")
    
    def _on_wake_detected(self):
        """Called when wake word 'Sarth' is detected"""
        logger.info("Wake word detected!")
        self.speak("Yes boss?", priority='high')
        self._start_stt_listening()
    
    def _start_stt_listening(self):
        """Start listening for command after wake word"""
        if self.stt:
            try:
                self.stt.start_listening()
                # Schedule timeout
                Clock.schedule_once(self._stt_timeout, self.stt_timeout)
            except Exception as e:
                logger.error(f"STT start error: {e}")
    
    def _stt_timeout(self, dt):
        """Timeout handler for STT"""
        if self.stt and hasattr(self.stt, 'is_listening') and self.stt.is_listening:
            logger.info("STT timeout - stopping listening")
            self.stt.stop_listening()
    
    def _on_partial_result(self, text):
        """Handle partial STT results"""
        logger.debug(f"Partial STT: {text}")
    
    def _on_speech_result(self, text, confidence=None):
        """Handle final STT result"""
        logger.info(f"STT Result: {text} (confidence: {confidence})")
        
        if text and self.on_command_callback:
            # Process command on main thread
            Clock.schedule_once(lambda dt: self.on_command_callback(text.lower()), 0)
    
    def _on_speech_error(self, error):
        """Handle STT errors"""
        logger.error(f"STT Error: {error}")
    
    def speak(self, text, priority='normal'):
        """
        Text-to-Speech with priority queue
        Priority levels: 'emergency' > 'high' > 'normal' > 'low'
        """
        if not self.tts:
            logger.warning(f"TTS not available, would say: {text}")
            return
        
        priority_values = {'emergency': 0, 'high': 1, 'normal': 2, 'low': 3}
        prio_val = priority_values.get(priority, 2)
        
        # Emergency interrupts current speech
        if priority == 'emergency' and self.speaking:
            self._interrupt_speech()
        
        self.command_queue.put((prio_val, text))
        
        # Process speech queue
        if not self.speaking:
            Clock.schedule_once(self._process_speech_queue, 0)
    
    def _process_speech_queue(self, dt):
        """Process queued speech commands"""
        try:
            if not self.command_queue.empty():
                prio, text = self.command_queue.get()
                self.speaking = True
                self._speak_text(text)
        except Exception as e:
            logger.error(f"Speech queue error: {e}")
            self.speaking = False
    
    def _speak_text(self, text):
        """Execute TTS"""
        try:
            if self.tts:
                self.tts.speak(text)
                # Estimate speech duration (rough approximation)
                import time
                duration = len(text.split()) * 0.3  # ~300ms per word
                time.sleep(duration)
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self.speaking = False
            # Continue processing queue
            if not self.command_queue.empty():
                Clock.schedule_once(self._process_speech_queue, 0.1)
    
    def _interrupt_speech(self):
        """Interrupt current speech for emergency alerts"""
        try:
            if self.tts and hasattr(self.tts, 'stop'):
                self.tts.stop()
        except Exception as e:
            logger.error(f"TTS interrupt error: {e}")
        self.speaking = False


# Mock classes for development/testing without Android
class MockTTS:
    """Mock TTS for testing on non-Android platforms"""
    def speak(self, text):
        logger.info(f"[MOCK TTS]: {text}")


class DesktopTTS:
    """Desktop TTS using pyttsx3 - works on Windows, macOS, Linux"""
    
    def __init__(self):
        self.engine = None
        self._init_engine()
    
    def _init_engine(self):
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            # Configure voice properties
            self.engine.setProperty('rate', 150)  # Speech rate
            self.engine.setProperty('volume', 0.9)  # Volume 0-1
            
            # Try to set a male voice (Jarvis/Sarth style)
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            logger.info("Desktop TTS initialized (pyttsx3)")
        except ImportError:
            logger.error("pyttsx3 not installed. Run: pip install pyttsx3")
            self.engine = None
        except Exception as e:
            logger.error(f"Desktop TTS init failed: {e}")
            self.engine = None
    
    def speak(self, text):
        """Speak text using desktop TTS"""
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                logger.info(f"[Desktop TTS]: {text}")
            except Exception as e:
                logger.error(f"Desktop TTS speak error: {e}")
        else:
            logger.warning(f"[MOCK TTS]: {text}")
    
    def stop(self):
        """Stop current speech"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass


class MockSTT:
    """Mock STT for testing"""
    def __init__(self, callback):
        self.callback = callback
        self.is_listening = False
    
    def start_listening(self):
        self.is_listening = True
        logger.info("[MOCK STT] Started listening")
    
    def stop_listening(self):
        self.is_listening = False
        logger.info("[MOCK STT] Stopped listening")
    
    def simulate_command(self, text):
        """Simulate voice command for testing"""
        if self.callback:
            self.callback(text)


class MockWakeWord:
    """Mock wake word detector for testing"""
    def __init__(self, callback):
        self.callback = callback
