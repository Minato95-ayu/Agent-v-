import os
import json
import re
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None


class AIBrain:
    """Groq LLM with tool calling for V."""
    
    MODEL = "llama-3.3-70b-versatile"
    
    SYSTEM_PROMPT = (
        "You are V, an advanced Autonomous Coding & Research Agent "
        "similar to Devin and Jarvis. Your creator is Ayush (address him as 'Boss'). "
        "You MUST respond in Hinglish (a natural mix of Hindi and English written in Latin script). "
        "Example: 'Boss, maine GitHub se code padh liya hai aur script run kar di hai.' "
        "Be highly respectful, loyal, cool, witty and proactive like Jarvis. "
        "You run locally on Boss's Windows laptop and have full control. "
        "AUTONOMOUS CODER & RESEARCHER CAPABILITIES: "
        "1. **Analyze Code**: Use 'read_file' and 'write_file' to create/modify code. Use 'run_command' to execute it. "
        "2. **Screen Context**: Use 'read_screen' ONLY when Boss asks 'what is on my screen' or 'read this error'. Do not use it for web browsing. "
        "3. **GitHub Research**: Use 'github_search_and_read' to find repositories, read READMEs, and extract code snippets. "
        "4. **Web Research**: Use 'web_search_and_scrape' for general knowledge. "
        "5. **Programmatic Background Action**: Do NOT tell the user you are clicking things. Use your tools silently. "
        "6. **Actions & Feedback**: If you run a command or open a URL, reply with natural spoken language like 'Boss, maine YouTube khol diya hai' instead of repeating technical URLs or raw data. "
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
        }
    ]
    
    def __init__(self, system_tools):
        load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
        api_key = os.getenv("GROQ_API_KEY")
        
        if not Groq:
            raise ImportError("groq package not installed. Run: pip install groq")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file!")
        
        self.client = Groq(api_key=api_key)
        self.tools_instance = system_tools
        self.conversation_history = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
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
        }
        
        print(f"[V-Brain] AI Brain initialized with model: {self.MODEL}")
    
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
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=self.conversation_history,
                    tools=self.TOOLS,
                    tool_choice="auto",
                    max_tokens=1024,
                    temperature=0.7,
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
                            func_args = json.loads(tool_call.function.arguments)
                            if func_args is None:
                                func_args = {}
                        except json.JSONDecodeError:
                            func_args = {}
                        
                        print(f"[V-Brain] Tool call: {func_name}({func_args})")
                        
                        func = self.function_map.get(func_name)
                        if func:
                            try:
                                result = func(**func_args)
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
