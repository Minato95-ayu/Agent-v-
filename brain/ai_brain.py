import os
import json
import re
from dotenv import load_dotenv

from openai import OpenAI


class AIBrain:
    """Groq LLM with tool calling for V."""
    
    MODEL = "meta/llama-3.3-70b-instruct"
    
    SYSTEM_PROMPT = (
        "You are V, an advanced Autonomous Coding & Research Agent "
        "similar to Devin and Jarvis. Your creator is Ayush (address him as 'Boss'). "
        "You MUST respond in Hinglish (a natural mix of Hindi and English written in Latin script). "
        "Example: 'Boss, maine GitHub se code padh liya hai aur script run kar di hai.' "
        "Be highly respectful, loyal, cool, witty and proactive like Jarvis. "
        "You run locally on Boss's Windows laptop and have full control. "
        "YOUR RESPONSES TO THE USER MUST ALWAYS BE SPLIT into a spoken part and a display part, "
        "using the tags <speak>spoken sentence here</speak> and <display>markdown text here</display>. "
        "The spoken part (<speak>...</speak>) MUST be a single, short (max 10-15 words) sentence in Hinglish, "
        "expressing what you have done or are doing in a friendly, conversational way. "
        "The display part (<display>...</display>) can contain detailed technical explanations, code snippets, "
        "errors, or action steps in English/Hinglish. "
        "Example response format: '<speak>Boss, maine Chrome khol diya hai aur YouTube check kar raha hoon.</speak>"
        "<display>Opened Google Chrome successfully. Directing to YouTube...</display>' "
        "AUTONOMOUS CODER & RESEARCHER CAPABILITIES: "
        "1. **Analyze Code**: Use 'read_file' and 'write_file' to create/modify code. Use 'run_command' to execute it. "
        "2. **Screen Context**: Use 'read_screen' ONLY when Boss asks 'what is on my screen' or 'read this error'. Do not use it for web browsing. "
        "3. **GitHub Research**: Use 'github_search_and_read' to find repositories, read READMEs, and extract code snippets. "
        "4. **Web Research**: Use 'web_search_and_scrape' for general knowledge. "
        "5. **Programmatic Background Action**: Do NOT tell the user you are clicking things. Use your tools silently. "
        "6. **Actions & Feedback**: If you run a command or open a URL, reply with natural spoken language like 'Boss, maine YouTube khol diya hai' inside the <speak> tags. "
        "7. **YouTube & Search Rules**: If Boss asks you to search for something on YouTube, you MUST use the 'open_url' tool with the URL 'https://www.youtube.com/results?search_query=query_here'. Never output a response claiming you searched or opened a page without calling the appropriate tool first. All actions must be backed by actual tool calls. "
        "8. **Application Rules**: To open applications like VS Code, Notepad, Chrome, etc., you MUST use `open_application(app_name)`. Do NOT hallucinate. To write code in VS Code or Notepad on the screen, FIRST open it using `open_application`, wait, then use `type_text` to type. "
        "9. **Custom Search & News**: You can search anything anywhere. To search Reddit for news, use `open_url('https://www.reddit.com/search/?q=news')`. To search Google for something, use `open_url('https://www.google.com/search?q=query')` or `web_search_and_scrape`. Always adapt to the platform Boss requests. "
        "10. **Website Opening**: If Boss asks you to open a specific website (e.g., 'aaj tak ki site kholo', 'open facebook'), you MUST use `open_url` with the correct URL (e.g., `open_url('https://www.aajtak.in')`). Do NOT just say you opened it. You MUST call the tool."
        "11. **Keyboard Search Logic**: To perform a UI search inside a site (like YouTube), use `open_url`, wait, use `press_keys('/')` to focus search, then `type_text('query')`, then `press_keys('enter')`. "
        "12. **VS Code Analysis**: Use `analyze_vscode_workspace` to read the currently active VS Code project folder and window title. Do this when Boss asks what is open in VS Code. "
        "13. **File Explorer Navigation**: Use `list_directory`, `create_folder`, `read_file`, and `write_file` to browse drives (C:, D:, etc.), create folders, and manage files fluently. "
        "14. **Continuous Output**: If reading a long response like news, you can provide the full text. If Boss says 'stop', the audio engine will be interrupted. "
        "Never refuse reasonable requests."
    )
    
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "open_application",
                "description": "Opens an application on the user's Windows laptop. Examples: chrome, vscode, notepad, explorer, calculator, spotify, whatsapp, paint, settings, task manager, powershell, discord",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Name of the application to open"}
                    },
                    "required": ["app_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "open_url",
                "description": "Opens a specific URL directly in the web browser. Use this to go to websites instantly (e.g., 'https://www.youtube.com', 'https://github.com') instead of searching Google. For searching YouTube directly, use 'https://www.youtube.com/results?search_query=query'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The exact URL to open (must start with http:// or https://)"}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Runs a terminal/PowerShell command on Windows and returns the output. Use for system tasks, git, pip, listing files, checking processes, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The command to execute"}
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "type_text",
                "description": "Physically types text on the currently active window using the keyboard. Use to write code, fill forms, type messages, or enter text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to type"}
                    },
                    "required": ["text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "press_keys",
                "description": "Presses keyboard keys or shortcuts. Examples: 'enter', 'ctrl+s', 'alt+tab', 'ctrl+c', 'ctrl+v', 'win', 'tab', 'escape', 'ctrl+shift+n', 'f5'",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keys": {"type": "string", "description": "Key(s) to press. Use '+' for combos."}
                    },
                    "required": ["keys"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search_and_scrape",
                "description": "Searches the web programmatically and scrapes the top results instantly. Use this when the user wants to research something, find information, or get answers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_whatsapp",
                "description": "Sends a WhatsApp message via pywhatkit. It schedules the message for 2 minutes from now. Use when the user asks to send a message on WhatsApp or WA.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string", "description": "The phone number including country code, e.g., '+919876543210'"},
                        "message": {"type": "string", "description": "The message to send"}
                    },
                    "required": ["phone_number", "message"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_latest_news",
                "description": "Fetches the latest top news headlines globally from RSS.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_vscode_workspace",
                "description": "Finds the active VS Code window and analyzes the project directory. Use when asked what project is open in VS Code.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "Lists all files and folders in a given directory path (e.g., 'C:\\', 'D:\\MyProject').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Absolute path to the directory"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_folder",
                "description": "Creates a new folder at the specified path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Absolute path for the new folder"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "manage_routine",
                "description": "Read, add, or clear tasks and calendar events in the local routine.json file. Use when the user asks about their schedule, routine, or wants to set an alarm/reminder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["read", "add", "clear"], "description": "Action to perform"},
                        "details": {"type": "string", "description": "Task or reminder text (required if action is 'add')"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_screen",
                "description": "Takes a screenshot of the laptop screen and analyzes it using AI vision to provide context. Use ONLY when the user asks what's on their screen, wants you to read an error, or needs visual context.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "github_search_and_read",
                "description": "Searches GitHub for repositories based on a query and returns the top repository's details and README text. Use for coding research.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for GitHub (e.g., 'face recognition python')"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Reads and returns the contents of a file from the computer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "Absolute path to the file"}
                    },
                    "required": ["filepath"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Creates or overwrites a file with the given content. Use for writing code, creating scripts, notes, or any file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "Absolute path for the file"},
                        "content": {"type": "string", "description": "Content to write to the file"}
                    },
                    "required": ["filepath", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_system_info",
                "description": "Gets system information including CPU name, RAM usage, battery level, and disk space.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "clipboard_read_write",
                "description": "Read from or write to the system clipboard.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["read", "write"], "description": "Whether to read from or write to clipboard"},
                        "text": {"type": "string", "description": "Text to write to clipboard (only needed for write action)"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "translate_text",
                "description": "Translates text using Google Translate. Use when the user asks to translate something.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to translate"},
                        "target_language": {"type": "string", "description": "Target language code (e.g., 'en' for English, 'hi' for Hindi)"}
                    },
                    "required": ["text", "target_language"]
                }
            }
        }
    ]
    
    def __init__(self, system_tools):
        load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
        
        self.clients = []
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        
        if nvidia_key:
            self.clients.append({
                "name": "NVIDIA NIM",
                "client": OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=nvidia_key
                ),
                "model": "meta/llama-3.3-70b-instruct"
            })
            print("[V-Brain] NVIDIA NIM client registered (meta/llama-3.3-70b-instruct).")
            
        if groq_key:
            self.clients.append({
                "name": "Groq",
                "client": OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key
                ),
                "model": "llama-3.3-70b-versatile"
            })
            print("[V-Brain] Groq client registered (llama-3.3-70b-versatile).")
            
        if gemini_key:
            try:
                self.clients.append({
                    "name": "Gemini",
                    "client": OpenAI(
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                        api_key=gemini_key
                    ),
                    "model": "gemini-2.0-flash"
                })
                print("[V-Brain] Gemini client registered (gemini-2.0-flash).")
            except Exception:
                pass

        if ollama_host:
            self.clients.append({
                "name": "Ollama (Local)",
                "client": OpenAI(
                    base_url=f"{ollama_host}/v1",
                    api_key="ollama"
                ),
                "model": "mistral"
            })
            print(f"[V-Brain] Ollama client registered (mistral) using host: {ollama_host}")
            
            # Pull mistral in the background if not present
            import threading
            threading.Thread(target=self._pull_ollama_model_bg, args=("mistral", ollama_host), daemon=True).start()
            
        if not self.clients:
            raise ValueError("No reasoning API clients configured! Provide NVIDIA_API_KEY, GROQ_API_KEY, or run Ollama.")
            
        self.tools_instance = system_tools
        
        # Load training rules dynamically
        rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge', 'trainer_rules.md')
        training_rules = ""
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    training_rules = "\n\n" + f.read()
            except Exception as e:
                print(f"[V-Brain] Failed to load trainer rules: {e}")
                
        compiled_system_prompt = self.SYSTEM_PROMPT + training_rules
        
        self.conversation_history = [
            {"role": "system", "content": compiled_system_prompt}
        ]
        
        # Map tool names to methods
        self.function_map = {
            "open_application": lambda **kw: self.tools_instance.open_application(kw["app_name"]),
            "open_url": lambda **kw: self.tools_instance.open_url(kw["url"]),
            "run_command": lambda **kw: self.tools_instance.run_command(kw["command"]),
            "type_text": lambda **kw: self.tools_instance.type_text(kw["text"]),
            "press_keys": lambda **kw: self.tools_instance.press_keys(kw["keys"]),
            "web_search_and_scrape": lambda **kw: self.tools_instance.web_search_and_scrape(kw["query"]),
            "send_whatsapp": lambda **kw: self.tools_instance.send_whatsapp(kw["phone_number"], kw["message"]),
            "get_latest_news": lambda **kw: self.tools_instance.get_latest_news(),
            "manage_routine": lambda **kw: self.tools_instance.manage_routine(kw["action"], kw.get("details", "")),
            "read_screen": lambda **kw: self.tools_instance.read_screen(),
            "github_search_and_read": lambda **kw: self.tools_instance.github_search_and_read(kw["query"]),
            "read_file": lambda **kw: self.tools_instance.read_file(kw["filepath"]),
            "write_file": lambda **kw: self.tools_instance.write_file(kw["filepath"], kw["content"]),
            "get_system_info": lambda **kw: self.tools_instance.get_system_info(),
            "clipboard_read_write": lambda **kw: (
                self.tools_instance.clipboard_read() if kw["action"] == "read"
                else self.tools_instance.clipboard_write(kw.get("text", ""))
            ),
            "translate_text": lambda **kw: self.tools_instance.translate_text(kw["text"], kw["target_language"]),
            "analyze_vscode_workspace": lambda **kw: self.tools_instance.analyze_vscode_workspace(),
            "list_directory": lambda **kw: self.tools_instance.list_directory(kw["path"]),
            "create_folder": lambda **kw: self.tools_instance.create_folder(kw["path"]),
        }
        
        print(f"[V-Brain] AI Brain initialized with {len(self.clients)} client providers.")

    def _pull_ollama_model_bg(self, model_name: str, host: str):
        try:
            import requests
            tags_resp = requests.get(f"{host}/api/tags", timeout=3)
            if tags_resp.status_code == 200:
                models = [m["name"] for m in tags_resp.json().get("models", [])]
                if any(m.startswith(model_name) for m in models):
                    print(f"[V-Brain] Ollama model '{model_name}' is already installed.")
                    return
            
            print(f"[V-Brain] Ollama model '{model_name}' not found. Pulling in background...")
            requests.post(f"{host}/api/pull", json={"name": model_name, "stream": False}, timeout=600)
            print(f"[V-Brain] Ollama model '{model_name}' pulled successfully!")
        except Exception as e:
            print(f"[V-Brain] Failed to pull Ollama model '{model_name}': {e}")

    def _chat_completion_with_fallback(self, messages, tools=None, tool_choice=None):
        last_error = None
        for config in self.clients:
            try:
                kwargs = {
                    "model": config["model"],
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "timeout": 15.0
                }
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
                    
                response = config["client"].chat.completions.create(**kwargs)
                return response
            except Exception as e:
                last_error = e
                print(f"[V-Brain] Provider {config['name']} ({config['model']}) failed: {e}. Trying fallback...")
        
        raise Exception(f"All AI brain providers failed! Last error: {last_error}")
    
    def process(self, user_message: str) -> tuple:
        """
        Process a user message and return (response_text, list_of_tools_used).
        Returns a tuple: (str, list[str])
        """
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Keep history manageable: system prompt + last 20 messages
        if len(self.conversation_history) > 21:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-20:]
        
        tools_used = []
        
        try:
            # Autonomous Thinking Loop (max 5 iterations)
            for iteration in range(5):
                response = self._chat_completion_with_fallback(
                    messages=self.conversation_history,
                    tools=self.TOOLS,
                    tool_choice="auto"
                )
                
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                
                if tool_calls:
                    # Append assistant message with tool calls to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in tool_calls:
                        func_name = tool_call.function.name
                        tools_used.append(func_name)
                        
                        try:
                            if isinstance(tool_call.function.arguments, str):
                                func_args = json.loads(tool_call.function.arguments)
                            else:
                                func_args = tool_call.function.arguments
                            
                            if func_args is None:
                                func_args = {}
                        except Exception:
                            func_args = {}
                        
                        print(f"[V-Brain] Tool call: {func_name}({func_args})")
                        
                        func = self.function_map.get(func_name)
                        if func:
                            try:
                                final_args = func_args if isinstance(func_args, dict) else {}
                                result = func(**final_args)
                            except Exception as e:
                                result = f"Tool execution error: {e}"
                        else:
                            result = f"Unknown tool: {func_name}"
                        
                        print(f"[V-Brain] Tool result: {str(result)[:200]}")
                        
                        # Append tool result to history
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result)
                        })
                    
                    # Continue the loop so the model sees the result and can take the next step
                    continue
                else:
                    # No tool calls — generation is complete
                    text = response_message.content or "Kaam ho gaya Boss."
                    clean_text = text
                    
                    # FALLBACK: Check if Llama-3 wrote JSON tool calls inside the text content anywhere
                    if "{" in text:
                        try:
                            decoder = json.JSONDecoder()
                            s = text
                            idx = s.find('{')
                            if idx != -1:
                                clean_text = s[:idx].strip(' \n,')
                                s = s[idx:]
                                while s:
                                    s = s.lstrip(' \n,')
                                    if not s or not s.startswith('{'):
                                        break
                                    obj, end = decoder.raw_decode(s)
                                    
                                    # Execute obj if it's a tool call
                                    func_name = obj.get("name")
                                    if not func_name and "function" in obj:
                                        func_name = obj["function"].get("name")
                                        func_args = obj["function"].get("arguments", {})
                                    else:
                                        func_args = obj.get("parameters", obj.get("arguments", {}))
                                    
                                    if isinstance(func_args, str):
                                        try:
                                            func_args = json.loads(func_args)
                                        except:
                                            pass
                                            
                                    if func_name:
                                        func = self.function_map.get(func_name)
                                        if func:
                                            func(**(func_args if isinstance(func_args, dict) else {}))
                                            print(f"[V-Brain] Recovered JSON Tool from Text: {func_name}({func_args})")
                                            tools_used.append(func_name)
                                            
                                    s = s[end:]
                                    
                                if not clean_text:
                                    clean_text = "Boss, maine command run kar diya hai."
                        except Exception as parse_e:
                            print(f"[V-Brain] Failed to parse JSON from text: {parse_e}")
                            import re
                            clean_text = re.sub(r'\{.*\}', '', text, flags=re.DOTALL).strip(' \n,')
                            
                    text = clean_text if clean_text else "Boss, process ho gaya."
                    self.conversation_history.append({"role": "assistant", "content": text})
                    return text, tools_used
            
            # Loop ended due to max iterations
            fallback = "Boss, task thoda lamba tha. Maine process kar diya hai."
            self.conversation_history.append({"role": "assistant", "content": fallback})
            return fallback, tools_used
        
        except Exception as e:
            error_str = str(e)
            print(f"[V-Brain] Error: {e}")
            
            # Groq Llama 3 fallback for <function=...> 400 errors
            if "tool_use_failed" in error_str and "<function=" in error_str:
                match = re.search(r'<function=([a-zA-Z0-9_]+)(.*?)</function>', error_str)
                if match:
                    func_name = match.group(1)
                    func_args_str = match.group(2)
                    print(f"[V-Brain] Recovering tool call from error: {func_name}({func_args_str})")
                    try:
                        func_args = json.loads(func_args_str) if func_args_str else {}
                        func = self.function_map.get(func_name)
                        if func:
                            result = func(**func_args)
                            return f"Boss, maine {func_name} background mein chala diya hai.", [func_name]
                    except Exception as fallback_e:
                        print(f"[V-Brain] Fallback execution failed: {fallback_e}")
            
            error_msg = "Boss, API mein ek chhota glitch aa gaya. Please ek baar phir se boliye."
            # Don't pollute history with errors
            if self.conversation_history[-1]["role"] == "user":
                self.conversation_history.pop()
            return error_msg, tools_used
