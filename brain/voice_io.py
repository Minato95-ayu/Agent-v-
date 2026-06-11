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
        self._stop_playback = False
        
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
        self.recognizer.pause_threshold = 2.5
        self.recognizer.dynamic_energy_threshold = True
    
    def start_listening(self):
        """Start continuous background listening."""
        if not sr:
            print("[V-Voice] Cannot start listening — speech_recognition not available.")
            return
        
        def callback(recognizer, audio):
            try:
                text = recognizer.recognize_google(audio, language='hi-IN')
                if text.strip():
                    lower_text = text.strip().lower()
                    
                    # If speaking, only interrupt on specific keywords to avoid self-echo cancellation
                    if self.is_speaking:
                        if "stop" in lower_text or "ruko" in lower_text or "badlo" in lower_text or "band karo" in lower_text:
                            print(f"[V-Ears] Interruption command heard: {text}")
                            self.stop_playback()
                            if self.on_transcript:
                                self.on_transcript(text)
                        return
                        
                    print(f"[V-Ears] Heard: {text}")
                    if self.on_transcript:
                        self.on_transcript(text)
            except sr.UnknownValueError:
                pass  # Could not understand
            except sr.RequestError as e:
                print(f"[V-Ears] Google STT Error: {e}. Falling back to Groq Whisper...")
                try:
                    wav_data = audio.get_wav_data()
                    temp_wav = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp_audio.wav')
                    with open(temp_wav, "wb") as f:
                        f.write(wav_data)
                    
                    from openai import OpenAI
                    from dotenv import load_dotenv
                    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
                    groq_key = os.getenv("GROQ_API_KEY")
                    
                    if groq_key:
                        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                        with open(temp_wav, "rb") as audio_file:
                            transcription = client.audio.transcriptions.create(
                                model="whisper-large-v3",
                                file=audio_file,
                                language="hi"
                            )
                        text = transcription.text
                        if text.strip():
                            print(f"[V-Ears] Heard (Groq): {text}")
                            if self.on_transcript:
                                self.on_transcript(text)
                    try:
                        os.remove(temp_wav)
                    except:
                        pass
                except Exception as groq_e:
                    print(f"[V-Ears] Groq Whisper failed: {groq_e}")
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
        """Convert text to speech and play it using edge-tts with native PowerShell fallback."""
        with self._lock:
            self.is_speaking = True
        
        try:
            # 1. Try high-quality Edge-TTS first
            import edge_tts
            communicate = edge_tts.Communicate(text, self.VOICE)
            await communicate.save(self.AUDIO_FILE)
            
            # Play using pygame in executor to avoid event loop starvation
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_audio, self.AUDIO_FILE)
            try:
                os.remove(self.AUDIO_FILE)
            except:
                pass
                
        except Exception as e:
            print(f"[V-Voice] Edge-TTS failed, falling back to Google TTS: {e}")
            try:
                # 2. Fallback to Google TTS
                from gtts import gTTS
                tts = gTTS(text=text, lang='hi')
                tts.save(self.AUDIO_FILE)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._play_audio, self.AUDIO_FILE)
                try:
                    os.remove(self.AUDIO_FILE)
                except:
                    pass
            except Exception as gtts_e:
                print(f"[V-Voice] Google TTS failed, falling back to native PowerShell: {gtts_e}")
                try:
                    # 3. Fallback to native Windows PowerShell speech synthesizer
                    safe_text = text.replace("'", "''").replace('"', '')
                    ps_command = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{safe_text}')"
                    
                    # Run PowerShell synchronously but in executor to not block asyncio
                    loop = asyncio.get_event_loop()
                    def run_ps():
                        import subprocess
                        subprocess.run(["powershell", "-Command", ps_command], creationflags=subprocess.CREATE_NO_WINDOW)
                        
                    await loop.run_in_executor(None, run_ps)
                except Exception as pe:
                    print(f"[V-Voice] PowerShell fallback TTS Error: {pe}")
        finally:
            with self._lock:
                self.is_speaking = False
    
    def stop_playback(self):
        """Interrupts current TTS playback."""
        self._stop_playback = True

    def _play_audio(self, filepath: str):
        """Play an audio file synchronously."""
        self._stop_playback = False
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if self._stop_playback:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[V-Voice] Playback Error: {e}")
