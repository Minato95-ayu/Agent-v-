import os
import subprocess
import time

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.3
except ImportError:
    pyautogui = None

try:
    import pyperclip
except ImportError:
    pyperclip = None


class SystemTools:
    """All system control tools for V - the autonomous AI assistant."""
    
    def __init__(self):
        # Trigger background Ollama vision model pull
        import threading
        from dotenv import load_dotenv
        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path)
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        threading.Thread(target=self._pull_ollama_model_bg, args=("moondream", ollama_host), daemon=True).start()

    def _pull_ollama_model_bg(self, model_name: str, host: str):
        try:
            import requests
            tags_resp = requests.get(f"{host}/api/tags", timeout=3)
            if tags_resp.status_code == 200:
                models = [m["name"] for m in tags_resp.json().get("models", [])]
                if any(m.startswith(model_name) for m in models):
                    print(f"[V-SystemTools] Ollama model '{model_name}' is already installed.")
                    return
            
            print(f"[V-SystemTools] Ollama model '{model_name}' not found. Pulling in background...")
            requests.post(f"{host}/api/pull", json={"name": model_name, "stream": False}, timeout=600)
            print(f"[V-SystemTools] Ollama model '{model_name}' pulled successfully!")
        except Exception as e:
            print(f"[V-SystemTools] Failed to pull Ollama model '{model_name}': {e}")

    APP_MAP = {
        'chrome': 'start chrome',
        'google chrome': 'start chrome',
        'google': 'start chrome "https://www.google.com"',
        'browser': 'start chrome',
        'youtube': 'start chrome "https://www.youtube.com"',
        'gmail': 'start chrome "https://mail.google.com"',
        'chatgpt': 'start chrome "https://chatgpt.com"',
        'vscode': 'code',
        'vs code': 'code',
        'visual studio code': 'code',
        'notepad': 'notepad',
        'explorer': 'explorer',
        'file explorer': 'explorer',
        'file manager': 'explorer',
        'cmd': 'start cmd',
        'terminal': 'start cmd',
        'powershell': 'start powershell',
        'calculator': 'calc',
        'paint': 'mspaint',
        'task manager': 'taskmgr',
        'settings': 'start ms-settings:',
        'spotify': 'start spotify:',
        'whatsapp': 'start whatsapp:',
        'discord': 'start discord:',
        'vscode': 'code',
        'visual studio code': 'code',
        'code': 'code',
        'notepad': 'notepad',
        'chrome': 'start chrome',
        'google chrome': 'start chrome',
        'browser': 'start chrome',
        'edge': 'start msedge',
    }
    
    def open_application(self, app_name: str) -> str:
        """Opens an application by name."""
        key = app_name.lower().strip()
        cmd = self.APP_MAP.get(key)
        if not cmd:
            cmd = f'start {app_name}'
        try:
            subprocess.Popen(cmd, shell=True)
            time.sleep(1)
            return f"Successfully opened {app_name}"
        except Exception as e:
            return f"Error opening {app_name}: {e}"

    def open_url(self, url: str) -> str:
        """Opens a direct URL in the default browser."""
        try:
            subprocess.Popen(f'start "" "{url}"', shell=True)
            time.sleep(1)
            return f"Successfully opened URL: {url}"
        except Exception as e:
            return f"Error opening URL {url}: {e}"
    
    def run_command(self, command: str) -> str:
        """Runs a terminal command and returns output."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=30, cwd=os.path.expanduser('~')
            )
            output = result.stdout.strip()
            if result.returncode != 0 and result.stderr.strip():
                output += f"\nError: {result.stderr.strip()}"
            return output[:2000] if output else "Command executed successfully (no output)."
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {e}"
    
    def type_text(self, text: str) -> str:
        """Types text on the active window."""
        if not pyautogui:
            return "Error: pyautogui not installed"
        try:
            # For ASCII text, use write()
            if text.isascii():
                pyautogui.write(text, interval=0.03)
            else:
                # For non-ASCII (Hindi etc), use clipboard paste
                if pyperclip:
                    pyperclip.copy(text)
                    pyautogui.hotkey('ctrl', 'v')
                else:
                    pyautogui.write(text, interval=0.03)
            return f"Typed text successfully."
        except Exception as e:
            return f"Error typing: {e}"
    
    def press_keys(self, keys: str) -> str:
        """Presses keyboard keys/shortcuts. E.g., 'enter', 'ctrl+s', 'alt+tab'"""
        if not pyautogui:
            return "Error: pyautogui not installed"
        try:
            if '+' in keys:
                parts = [k.strip().lower() for k in keys.split('+')]
                pyautogui.hotkey(*parts)
            else:
                pyautogui.press(keys.strip().lower())
            return f"Pressed: {keys}"
        except Exception as e:
            return f"Error pressing keys: {e}"
    
    def web_search_and_read(self, query: str) -> str:
        """Opens Chrome and searches Google."""
        try:
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            subprocess.Popen(f'start chrome "{url}"', shell=True)
            time.sleep(1)
            return f"Opened Google search for: {query}. The browser is now showing results."
        except Exception as e:
            return f"Error searching: {e}"
    
    def web_search_and_scrape(self, query: str) -> str:
        """Searches DuckDuckGo and scrapes top results without opening a browser."""
        try:
            from duckduckgo_search import DDGS
            import requests
            from bs4 import BeautifulSoup

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return "No results found."

            output = f"Top results for '{query}':\n"
            for res in results:
                title = res.get('title', '')
                href = res.get('href', '')
                snippet = res.get('body', '')
                output += f"\n- {title}\n  Link: {href}\n  Summary: {snippet}\n"
                # Scrape first link lightly
                if len(output) < 1500 and href.startswith('http'):
                    try:
                        resp = requests.get(href, timeout=5)
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        text = ' '.join([p.text for p in soup.find_all('p')])[:500]
                        if text: output += f"  Extracted Text: {text}...\n"
                    except: pass
            
            return output[:3000]
        except Exception as e:
            return f"Error searching/scraping: {e}"

    def send_whatsapp(self, phone_number: str, message: str) -> str:
        """Sends a WhatsApp message using pywhatkit."""
        try:
            import pywhatkit
            import datetime
            import time
            now = datetime.datetime.now()
            # To avoid errors, send exactly 2 minutes from current time
            minute = now.minute + 2
            hour = now.hour
            if minute >= 60:
                minute -= 60
                hour = (hour + 1) % 24
                
            pywhatkit.sendwhatmsg(phone_number, message, hour, minute, wait_time=15, tab_close=True, close_time=3)
            return f"WhatsApp message scheduled to be sent to {phone_number} at {hour}:{minute:02d}."
        except Exception as e:
            return f"Error sending WhatsApp: {e}"

    def get_latest_news(self) -> str:
        """Fetches latest world/tech news."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = "https://news.google.com/rss"
            resp = requests.get(url, timeout=5)
            soup = BeautifulSoup(resp.content, features="xml")
            items = soup.findAll('item')
            news = "Here are the latest top news headlines:\n"
            for item in items[:5]:
                news += f"- {item.title.text}\n"
            return news
        except Exception as e:
            return f"Error fetching news: {e}"

    def manage_routine(self, action: str, details: str = "") -> str:
        """Reads or writes to the local routine.json calendar file."""
        import json
        import os
        filepath = os.path.join(os.path.dirname(__file__), '..', 'routine.json')
        try:
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump({"tasks": []}, f)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if action == "read":
                tasks = data.get("tasks", [])
                if not tasks: return "No routines or calendar events scheduled."
                return "Current Schedule/Routine:\n" + "\n".join([f"- {t}" for t in tasks])
            
            elif action == "add":
                data.setdefault("tasks", []).append(details)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                return f"Successfully added to routine: {details}"
                
            elif action == "clear":
                with open(filepath, 'w') as f:
                    json.dump({"tasks": []}, f)
                return "Routine cleared successfully."
            
            else:
                return "Invalid action. Use 'read', 'add', or 'clear'."
        except Exception as e:
            return f"Error managing routine: {e}"
    
    def read_screen(self) -> str:
        """Takes screenshot and describes it using NVIDIA NIM Vision (or Gemini fallback) for context."""
        if not pyautogui:
            return "Error: pyautogui not installed"
        try:
            from PIL import Image
            from dotenv import load_dotenv
            import base64
            
            # Load environment variables
            dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
            load_dotenv(dotenv_path)
            
            # Capture screen
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'v_screenshot.png')
            filepath = os.path.abspath(filepath)
            screenshot = pyautogui.screenshot()
            
            # Resize image to max width 1280 to save bandwidth and API processing time
            max_size = 1280
            width, height = screenshot.size
            if width > max_size:
                ratio = max_size / width
                new_width = max_size
                new_height = int(height * ratio)
                screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save compressed JPEG to speed up API transfer
            jpeg_path = filepath.replace(".png", ".jpg")
            screenshot.convert("RGB").save(jpeg_path, "JPEG", quality=75)
            
            # 1. Primary path: NVIDIA NIM Vision
            nvidia_key = os.getenv("NVIDIA_API_KEY")
            if nvidia_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(
                        base_url="https://integrate.api.nvidia.com/v1",
                        api_key=nvidia_key
                    )
                    with open(jpeg_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                        
                    response = client.chat.completions.create(
                        model="meta/llama-3.2-11b-vision-instruct",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Describe everything visible on this screen in detail. "
                                                "Mention open applications, text content, errors, code snippets, and context. "
                                                "Do not provide bounding boxes, just describe the visual context."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{encoded_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=500
                    )
                    desc = response.choices[0].message.content
                    return f"Screen Context (NVIDIA): {desc}"
                except Exception as ne:
                    print(f"[V-SystemTools] NVIDIA Vision failed, falling back to Gemini: {ne}")
            
            # 2. Fallback 1: Gemini Vision
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    img = Image.open(jpeg_path)
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    response = model.generate_content([
                        "Describe everything visible on this screen in detail. "
                        "Mention open applications, text content, errors, code snippets, and context. "
                        "Do not provide bounding boxes, just describe the visual context.",
                        img
                    ])
                    return f"Screen Context (Gemini): {response.text}"
                except Exception as ge:
                    print(f"[V-SystemTools] Gemini Vision failed, falling back to Ollama: {ge}")
            
            # 3. Fallback 2: Ollama Vision (Local)
            ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
            if ollama_host:
                try:
                    import requests
                    tags_resp = requests.get(f"{ollama_host}/api/tags", timeout=3)
                    if tags_resp.status_code == 200:
                        models = [m["name"] for m in tags_resp.json().get("models", [])]
                        vision_model = None
                        for model_name in ["moondream", "llama3.2-vision", "llava"]:
                            for m in models:
                                if m.startswith(model_name):
                                    vision_model = m
                                    break
                            if vision_model:
                                break
                        
                        if vision_model:
                            with open(jpeg_path, "rb") as image_file:
                                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                            
                            payload = {
                                "model": vision_model,
                                "prompt": "Describe everything visible on this screen in detail. "
                                          "Mention open applications, text content, errors, code snippets, and context. "
                                          "Do not provide bounding boxes, just describe the visual context.",
                                "images": [encoded_image],
                                "stream": False
                            }
                            ollama_resp = requests.post(f"{ollama_host}/api/generate", json=payload, timeout=60)
                            if ollama_resp.status_code == 200:
                                desc = ollama_resp.json().get("response", "")
                                return f"Screen Context (Ollama - {vision_model}): {desc}"
                            else:
                                raise Exception(f"Ollama returned status {ollama_resp.status_code}: {ollama_resp.text}")
                        else:
                            raise Exception("No local vision models (moondream, llama3.2-vision, llava) found in Ollama.")
                except Exception as oe:
                    return f"Vision analysis failed (NVIDIA, Gemini, and Ollama all failed): {oe}"
            
            return "Error: No vision API key found, and Ollama is not configured."
            
        except Exception as e:
            return f"Error capturing screen: {e}"


    def github_search_and_read(self, query: str) -> str:
        """Searches GitHub and extracts the top repository README or code snippet."""
        try:
            import requests
            # Use GitHub REST API
            search_url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
            response = requests.get(search_url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=10)
            if response.status_code != 200:
                return f"GitHub API error: {response.status_code}"
            
            data = response.json()
            items = data.get("items", [])
            if not items:
                return "No repositories found on GitHub."
                
            top_repo = items[0]
            repo_full_name = top_repo["full_name"]
            description = top_repo.get("description", "No description")
            url = top_repo["html_url"]
            
            output = f"Top GitHub Result: {repo_full_name}\nURL: {url}\nDescription: {description}\n\n"
            
            # Fetch README
            readme_url = f"https://raw.githubusercontent.com/{repo_full_name}/master/README.md"
            readme_resp = requests.get(readme_url, timeout=5)
            if readme_resp.status_code == 404:
                readme_url = f"https://raw.githubusercontent.com/{repo_full_name}/main/README.md"
                readme_resp = requests.get(readme_url, timeout=5)
            
            if readme_resp.status_code == 200:
                readme_text = readme_resp.text
                output += f"--- README SNIPPET ---\n{readme_text[:2000]}...\n"
            else:
                output += "Could not fetch README."
                
            return output
        except Exception as e:
            return f"Error searching GitHub: {e}"
            
    def read_file(self, filepath: str) -> str:
        """Reads contents of a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content[:3000] if content else "File is empty."
        except UnicodeDecodeError:
            return "Error: File is binary, cannot read as text."
        except Exception as e:
            return f"Error reading file: {e}"
    
    def write_file(self, filepath: str, content: str) -> str:
        """Writes content to a file."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written successfully: {filepath}"
        except Exception as e:
            return f"Error writing file: {e}"
    
    def analyze_vscode_workspace(self) -> str:
        """Finds the active VS Code window and analyzes the project directory to find its absolute path."""
        try:
            import pygetwindow as gw
            import os
            import json
            import urllib.parse
            
            windows = gw.getAllTitles()
            vscode_window = None
            for w in windows:
                if "Visual Studio Code" in w:
                    vscode_window = w
                    break
            
            if not vscode_window:
                return "VS Code is not open or no active window found."
                
            parts = [p.strip() for p in vscode_window.split('-')]
            if len(parts) >= 2:
                folder_name = parts[-2]
                
                # Try to resolve absolute path from workspaceStorage
                storage_path = os.path.expanduser('~\\AppData\\Roaming\\Code\\User\\workspaceStorage')
                matched_path = None
                
                if os.path.exists(storage_path):
                    for folder in os.listdir(storage_path):
                        json_path = os.path.join(storage_path, folder, 'workspace.json')
                        if os.path.exists(json_path):
                            try:
                                with open(json_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    if 'folder' in data:
                                        folder_uri = data['folder']
                                        if folder_uri.startswith('file:///'):
                                            path = urllib.parse.unquote(folder_uri[8:])
                                            path = os.path.normpath(path)
                                            if os.path.basename(path).lower() == folder_name.lower():
                                                matched_path = path
                                                break
                            except Exception:
                                pass
                
                if matched_path:
                    return f"Active VS Code Project Folder: '{folder_name}'. Absolute Path: '{matched_path}'"
                else:
                    return f"Active VS Code Project Folder: '{folder_name}'. IMPORTANT: The absolute path is UNKNOWN. Do NOT guess the path or hallucinate files. Ask the user for the absolute path."
            else:
                return f"Found VS Code window: {vscode_window}, but couldn't determine project folder."
        except Exception as e:
            return f"Error analyzing VS Code workspace: {e}"

    def list_directory(self, path: str) -> str:
        """Lists files and folders in a directory."""
        try:
            import os
            if not os.path.exists(path):
                return f"Error: Path '{path}' does not exist."
            
            items = os.listdir(path)
            if not items:
                return f"Directory '{path}' is empty."
                
            output = f"Contents of {path}:\n"
            folders = [i for i in items if os.path.isdir(os.path.join(path, i))]
            files = [i for i in items if os.path.isfile(os.path.join(path, i))]
            
            output += "Folders:\n" + "\n".join([f"- {f}/" for f in folders]) + "\n\n"
            output += "Files:\n" + "\n".join([f"- {f}" for f in files])
            
            return output[:3000]
        except Exception as e:
            return f"Error listing directory: {e}"

    def create_folder(self, path: str) -> str:
        """Creates a new folder at the specified path."""
        try:
            import os
            os.makedirs(path, exist_ok=True)
            return f"Successfully created folder: {path}"
        except Exception as e:
            return f"Error creating folder: {e}"

    def get_system_info(self) -> str:
        """Gets system information."""
        info = []
        try:
            # CPU
            r = subprocess.run('wmic cpu get name /value', shell=True, capture_output=True, text=True, timeout=10)
            for line in r.stdout.strip().split('\n'):
                if 'Name=' in line:
                    info.append(f"CPU: {line.split('=')[1].strip()}")
        except: pass
        try:
            # RAM
            r = subprocess.run('wmic os get TotalVisibleMemorySize,FreePhysicalMemory /value', shell=True, capture_output=True, text=True, timeout=10)
            total = free = 0
            for line in r.stdout.strip().split('\n'):
                if 'TotalVisibleMemorySize=' in line:
                    total = int(line.split('=')[1].strip()) // 1024
                elif 'FreePhysicalMemory=' in line:
                    free = int(line.split('=')[1].strip()) // 1024
            if total:
                info.append(f"RAM: {total - free} MB used / {total} MB total ({free} MB free)")
        except: pass
        try:
            # Battery
            r = subprocess.run('wmic path win32_battery get EstimatedChargeRemaining /value', shell=True, capture_output=True, text=True, timeout=10)
            for line in r.stdout.strip().split('\n'):
                if 'EstimatedChargeRemaining=' in line:
                    info.append(f"Battery: {line.split('=')[1].strip()}%")
        except: pass
        try:
            # Disk
            r = subprocess.run('wmic logicaldisk where drivetype=3 get caption,freespace,size /value', shell=True, capture_output=True, text=True, timeout=10)
            info.append(f"Disk: {r.stdout.strip()[:300]}")
        except: pass
        return '\n'.join(info) if info else "Could not retrieve system info."
    
    def clipboard_read(self) -> str:
        """Reads clipboard contents."""
        if not pyperclip:
            return "Error: pyperclip not installed"
        try:
            content = pyperclip.paste()
            return content if content else "Clipboard is empty."
        except Exception as e:
            return f"Error reading clipboard: {e}"
    
    def clipboard_write(self, text: str) -> str:
        """Writes to clipboard."""
        if not pyperclip:
            return "Error: pyperclip not installed"
        try:
            pyperclip.copy(text)
            return "Text copied to clipboard."
        except Exception as e:
            return f"Error writing to clipboard: {e}"

    def translate_text(self, text: str, target_language: str) -> str:
        """Translates text using deep-translator."""
        try:
            from deep_translator import GoogleTranslator
            # deep_translator uses 'hi' for Hindi, 'en' for English
            translated = GoogleTranslator(source='auto', target=target_language).translate(text)
            return f"Translated text ({target_language}): {translated}"
        except Exception as e:
            return f"Error translating text: {e}"
