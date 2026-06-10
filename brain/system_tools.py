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
    
    APP_MAP = {
        'chrome': 'start chrome',
        'google chrome': 'start chrome',
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
        """Takes screenshot and describes it using Gemini Vision for context."""
        if not pyautogui:
            return "Error: pyautogui not installed"
        try:
            filepath = os.path.join(os.path.dirname(__file__), '..', 'v_screenshot.png')
            filepath = os.path.abspath(filepath)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            try:
                import google.generativeai as genai
                from PIL import Image
                from dotenv import load_dotenv
                load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    img = Image.open(filepath)
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    response = model.generate_content([
                        "Describe everything visible on this screen in detail. "
                        "Mention open applications, text content, errors, code snippets, and context. "
                        "Do not provide bounding boxes, just describe the visual context.",
                        img
                    ])
                    return f"Screen Context: {response.text}"
                else:
                    return "Screenshot saved but Gemini API key not found for analysis."
            except Exception as e:
                return f"Vision analysis failed: {e}"
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
