import asyncio
import os
import time
import threading

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None




class VoiceIO:
    """Voice Input/Output for V — STT (Google) + TTS (edge-tts)."""
    
    VOICE = "hi-IN-MadhurNeural"  # Male Hindi neural voice
    AUDIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'v_speech.mp3')
    
    def __init__(self, on_transcript=None):
        """
        Args:
            on_transcript: Callback(text: str) called when speech is recognized.
        """
        self.on_transcript = on_transcript
        self.is_speaking = False
        self.is_listening = False
        self.stop_listening_fn = None
        self._lock = threading.Lock()
        
        if not sr:
            print("[V-Voice] WARNING: speech_recognition not installed. Voice input disabled.")
            return
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibrate for ambient noise
        print("[V-Voice] Calibrating microphone for ambient noise...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("[V-Voice] Microphone calibrated.")
        except Exception as e:
            print(f"[V-Voice] Microphone calibration failed: {e}")
        
        # Tuning
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
    
    def start_listening(self):
        """Start continuous background listening."""
        if not sr:
            print("[V-Voice] Cannot start listening — speech_recognition not available.")
            return
        
        def callback(recognizer, audio):
            if self.is_speaking:
                return  # Skip while V is speaking (echo cancellation)
            try:
                text = recognizer.recognize_google(audio, language='hi-IN')
                if text.strip():
                    print(f"[V-Ears] Heard: {text}")
                    if self.on_transcript:
                        self.on_transcript(text)
            except sr.UnknownValueError:
                pass  # Could not understand
            except sr.RequestError as e:
                print(f"[V-Ears] Google STT Error: {e}")
            except Exception as e:
                print(f"[V-Ears] Unexpected error: {e}")
        
        try:
            self.stop_listening_fn = self.recognizer.listen_in_background(
                self.microphone, callback, phrase_time_limit=15
            )
            self.is_listening = True
            print("[V-Voice] Background listening started.")
        except Exception as e:
            print(f"[V-Voice] Failed to start listening: {e}")
    
    def stop(self):
        """Stop listening."""
        if self.stop_listening_fn:
            self.stop_listening_fn(wait_for_stop=False)
            self.is_listening = False
            print("[V-Voice] Listening stopped.")
    
    async def speak(self, text: str):
        """Convert text to speech and play it using Windows native PowerShell TTS."""
        with self._lock:
            self.is_speaking = True
        
        try:
            # Escape text for PowerShell string
            safe_text = text.replace("'", "''").replace('"', '')
            ps_command = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{safe_text}')"
            
            # Run PowerShell synchronously but in executor to not block asyncio
            loop = asyncio.get_event_loop()
            def run_ps():
                import subprocess
                subprocess.run(["powershell", "-Command", ps_command], creationflags=subprocess.CREATE_NO_WINDOW)
                
            await loop.run_in_executor(None, run_ps)
                
        except Exception as e:
            print(f"[V-Voice] TTS Error: {e}")
        finally:
            with self._lock:
                self.is_speaking = False
    
    def _play_audio(self, filepath: str):
        """Play an audio file synchronously."""
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[V-Voice] Playback Error: {e}")
