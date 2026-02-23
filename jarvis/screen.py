"""
Jarvis Gaming Assistant - Screen Capture Module
Phase 2: Screen Capture using minicap + android_screen_buffer
"""
import os
import sys
import time
import threading
import subprocess
import numpy as np
from kivy.clock import Clock
import logging

logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Screen capture using minicap binary for high-performance frame capture
    at 15 FPS for game analysis
    """
    
    def __init__(self, fps=15, resolution=(1080, 2340)):
        self.fps = fps
        self.resolution = resolution
        self.frame_interval = 1.0 / fps
        self.running = False
        self.capture_thread = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_callbacks = []
        
        self.minicap_path = None
        self.minicap_process = None
        self.android_buffer = None
        
        self._find_minicap_binary()
    
    def _find_minicap_binary(self):
        """Find and extract minicap binary for the device's architecture"""
        try:
            # Get device architecture
            abi = self._get_device_abi()
            logger.info(f"Device ABI: {abi}")
            
            # Path to bundled minicap
            app_files_dir = self._get_app_files_dir()
            minicap_dir = os.path.join(app_files_dir, 'minicap')
            os.makedirs(minicap_dir, exist_ok=True)
            
            minicap_bin = os.path.join(minicap_dir, 'minicap')
            
            # Extract from assets if not exists
            if not os.path.exists(minicap_bin):
                self._extract_minicap(abi, minicap_bin)
            
            self.minicap_path = minicap_bin
            os.chmod(minicap_bin, 0o755)
            logger.info(f"Minicap ready at: {minicap_bin}")
            
        except Exception as e:
            logger.error(f"Minicap setup failed: {e}")
            self.minicap_path = None
    
    def _get_device_abi(self):
        """Get Android device ABI (arm64-v8a or armeabi-v7a)"""
        try:
            import android
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            return Build.CPU_ABI
        except:
            # Fallback detection
            try:
                result = subprocess.run(['getprop', 'ro.product.cpu.abi'], 
                                      capture_output=True, text=True)
                return result.stdout.strip() or 'arm64-v8a'
            except:
                return 'arm64-v8a'
    
    def _get_app_files_dir(self):
        """Get application's files directory"""
        try:
            import android
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            return activity.getFilesDir().getAbsolutePath()
        except:
            return '/data/data/com.yourname.jarvisgameassist/files'
    
    def _extract_minicap(self, abi, dest_path):
        """Extract minicap binary from app assets"""
        try:
            import android
            from jnius import autoclass
            
            asset_manager = autoclass('org.kivy.android.PythonActivity').mActivity.getAssets()
            asset_name = f'minicap/{abi}/minicap'
            
            input_stream = asset_manager.open(asset_name)
            
            with open(dest_path, 'wb') as f:
                buffer = bytearray(8192)
                while True:
                    length = input_stream.read(buffer)
                    if length <= 0:
                        break
                    f.write(buffer[:length])
            
            input_stream.close()
            logger.info(f"Extracted minicap to {dest_path}")
            
        except Exception as e:
            logger.error(f"Failed to extract minicap: {e}")
            raise
    
    def start(self):
        """Start screen capture at configured FPS"""
        if self.running:
            return
        
        self.running = True
        
        try:
            # Try minicap first
            if self.minicap_path:
                self._start_minicap()
            else:
                # Fallback to android_screen_buffer
                self._start_asb()
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info(f"Screen capture started at {self.fps} FPS")
            
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            self.running = False
    
    def stop(self):
        """Stop screen capture"""
        self.running = False
        
        if self.minicap_process:
            try:
                self.minicap_process.terminate()
                self.minicap_process.wait(timeout=2)
            except:
                self.minicap_process.kill()
            self.minicap_process = None
        
        if self.android_buffer:
            try:
                self.android_buffer.stop()
            except:
                pass
            self.android_buffer = None
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        
        logger.info("Screen capture stopped")
    
    def _start_minicap(self):
        """Start minicap server"""
        try:
            w, h = self.resolution
            # minicap format: -P <width>x<height>@<virtual_width>x<virtual_height>/<rotation>
            cmd = [
                self.minicap_path,
                '-P', f'{w}x{h}@{w}x{h}/0',
                '-S'  # Send frames via socket
            ]
            
            self.minicap_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(0.5)
            
            # Connect to minicap socket
            self._connect_minicap_socket()
            
        except Exception as e:
            logger.error(f"Minicap start failed: {e}")
            raise
    
    def _connect_minicap_socket(self):
        """Connect to minicap socket for frame data"""
        import socket
        
        try:
            # Forward minicap port via adb if needed
            subprocess.run(['adb', 'forward', 'tcp:1717', 'localabstract:minicap'], 
                         capture_output=True)
            
            self.minicap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.minicap_socket.connect(('localhost', 1717))
            self.minicap_socket.settimeout(1.0)
            
            # Read header (version, header size, PID, width, height, orientation, quirks)
            header = self.minicap_socket.recv(24)
            if len(header) >= 24:
                version, header_size, pid, read_width, read_height, orientation, quirks = \
                    struct.unpack_from('BBIIIIII', header)
                logger.info(f"Minicap: {read_width}x{read_height} @ {orientation}°")
            
        except Exception as e:
            logger.error(f"Minicap socket connection failed: {e}")
    
    def _start_asb(self):
        """Fallback to android_screen_buffer"""
        try:
            from android_screen_buffer import AndroidScreenBuffer
            self.android_buffer = AndroidScreenBuffer(port=12345)
            self.android_buffer.start()
            logger.info("AndroidScreenBuffer started")
        except ImportError:
            logger.warning("android_screen_buffer not available, using fallback")
            self.android_buffer = None
    
    def _capture_loop(self):
        """Main capture loop - runs in background thread"""
        last_capture = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                elapsed = current_time - last_capture
                
                if elapsed >= self.frame_interval:
                    frame = self._capture_frame()
                    
                    if frame is not None:
                        with self.frame_lock:
                            self.current_frame = frame
                        
                        # Notify callbacks on main thread
                        Clock.schedule_once(
                            lambda dt, f=frame: self._notify_callbacks(f), 0
                        )
                    
                    last_capture = current_time
                else:
                    # Small sleep to prevent busy-waiting
                    time.sleep(0.001)
                    
            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                time.sleep(0.1)
    
    def _capture_frame(self):
        """Capture single frame from minicap or fallback"""
        try:
            # Try minicap socket first
            if hasattr(self, 'minicap_socket') and self.minicap_socket:
                return self._read_minicap_frame()
            
            # Try android_screen_buffer
            elif self.android_buffer:
                return self.android_buffer.get_last_frame()
            
            # Final fallback: screencap
            else:
                return self._capture_screencap()
                
        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            return None
    
    def _read_minicap_frame(self):
        """Read frame from minicap socket"""
        try:
            # Read frame header (frame size)
            size_data = b''
            while len(size_data) < 4:
                chunk = self.minicap_socket.recv(4 - len(size_data))
                if not chunk:
                    return None
                size_data += chunk
            
            frame_size = int.from_bytes(size_data, 'big')
            
            # Read frame data
            frame_data = b''
            while len(frame_data) < frame_size:
                chunk = self.minicap_socket.recv(min(8192, frame_size - len(frame_data)))
                if not chunk:
                    return None
                frame_data += chunk
            
            # Decode JPEG to numpy array
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(frame_data))
            frame = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
            
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Minicap frame read error: {e}")
            return None
    
    def _capture_screencap(self):
        """Fallback using Android screencap command"""
        try:
            result = subprocess.run(
                ['screencap', '-p'],
                capture_output=True,
                timeout=0.5
            )
            
            if result.returncode == 0:
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(result.stdout))
                frame = np.array(image)
                
                # Convert to BGR
                import cv2
                if len(frame.shape) == 3 and frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                return frame
            
        except Exception as e:
            logger.error(f"Screencap failed: {e}")
        
        return None
    
    def get_last_frame(self):
        """Get the most recent captured frame"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def register_callback(self, callback):
        """Register a callback to receive new frames"""
        if callback not in self.frame_callbacks:
            self.frame_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """Unregister frame callback"""
        if callback in self.frame_callbacks:
            self.frame_callbacks.remove(callback)
    
    def _notify_callbacks(self, frame):
        """Notify all registered callbacks of new frame"""
        for callback in self.frame_callbacks:
            try:
                callback(frame)
            except Exception as e:
                logger.error(f"Frame callback error: {e}")


class MockScreenCapture:
    """Mock screen capture for testing without Android"""
    
    def __init__(self, fps=15, resolution=(1080, 2340)):
        self.fps = fps
        self.resolution = resolution
        self.running = False
        self.current_frame = None
        logger.info("MockScreenCapture initialized")
    
    def start(self):
        self.running = True
        logger.info("MockScreenCapture started")
    
    def stop(self):
        self.running = False
        logger.info("MockScreenCapture stopped")
    
    def get_last_frame(self):
        """Return a blank or test frame"""
        if self.current_frame is None:
            # Create a blank test frame
            self.current_frame = np.zeros(
                (self.resolution[1], self.resolution[0], 3), 
                dtype=np.uint8
            )
        return self.current_frame
    
    def load_test_image(self, path):
        """Load a test image as the current frame"""
        import cv2
        self.current_frame = cv2.imread(path)
