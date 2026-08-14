import os
import sys
import re
import time
import uuid
import queue
import builtins
import threading
import urllib.parse
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Ensure we are in the root directory and can import Cwelium
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- Monkeypatching builtins and sys to prevent serverless lockups/exits ---
# Prevents any input() call from hanging the serverless thread
builtins.input = lambda *args, **kwargs: ""

# Prevents sys.exit() from shutting down the FastAPI server process
original_exit = sys.exit
def mock_exit(code=0):
    raise RuntimeError(f"System exit called with code {code}")
sys.exit = mock_exit

# --- Thread Log Tracking Mechanism ---
thread_to_queue = {}
thread_to_queue_lock = threading.Lock()

# Intercept threading.Thread to propagate request log queues to spawned worker threads
original_init = threading.Thread.__init__
original_start = threading.Thread.start

def new_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    parent_id = threading.current_thread().ident
    with thread_to_queue_lock:
        if parent_id in thread_to_queue:
            self._parent_queue = thread_to_queue[parent_id]
        else:
            self._parent_queue = None

def new_start(self):
    pq = getattr(self, "_parent_queue", None)
    original_start(self)
    if pq:
        with thread_to_queue_lock:
            thread_to_queue[self.ident] = pq

threading.Thread.__init__ = new_init
threading.Thread.start = new_start

# --- Import Cwelium after applying base patches ---
import Cwelium

# --- Custom console.log replacement ---
def custom_log(text=None, color=None, token=None, log=None):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Formulate plain logs
    log_str = f"[{timestamp}] "
    if text:
        log_str += f"[{text}] "
    if token:
        hidden_token = token
        if len(token) > 12:
            hidden_token = f"{token[:8]}...{token[-4:]}"
        log_str += hidden_token
    if log:
        log_str += f" ({log})"

    log_data = {
        "timestamp": timestamp,
        "type": text,
        "token": token[:8] + "..." if token else None,
        "message": str(log) if log else None,
        "raw": log_str
    }

    # Retrieve the queue registered for the current thread
    current_id = threading.current_thread().ident
    q = None
    with thread_to_queue_lock:
        q = thread_to_queue.get(current_id)

    if q:
        q.put(log_data)
    else:
        # Fallback to local server stdout
        print(f"[STDOUT FALLBACK] {log_str}")

# --- Thread-Safe curl_cffi Session Proxy ---
class ThreadLocalSession:
    def __init__(self):
        self._local = threading.local()

    @property
    def current_session(self):
        if not hasattr(self._local, "session"):
            import curl_cffi
            self._local.session = curl_cffi.Session(impersonate="chrome136")
        return self._local.session

    def __getattr__(self, name):
        return getattr(self.current_session, name)

    def __setattr__(self, name, value):
        if name == "_local":
            super().__setattr__(name, value)
        else:
            setattr(self.current_session, name, value)

Cwelium.session = ThreadLocalSession()

# Bind custom logging to Cwelium console
Cwelium.console.log = custom_log

# --- Mock Cwelium Menu methods to run asynchronously without inputs ---
def mock_main_menu(self):
    pass

def mock_run(self, func, args):
    threads = []
    for idx, arg in enumerate(args):
        selected_proxy = None
        if Cwelium.proxy and Cwelium.proxies:
            selected_proxy = Cwelium.proxies[idx % len(Cwelium.proxies)]
            
        def thread_wrapper(p, f, *a):
            if p:
                Cwelium.session.proxies = {
                    "http": f"http://{p}",
                    "https": f"http://{p}"
                }
            else:
                Cwelium.session.proxies = {}
            f(*a)
            
        thread = threading.Thread(target=thread_wrapper, args=(selected_proxy, func) + arg, daemon=True)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

Cwelium.Menu.main_menu = mock_main_menu
Cwelium.Menu.run = mock_run

# --- Custom Cwelium Helper Actions ---
def custom_spammer(raider, token, channel, message, guild, massping, pings, random_str, delay, count):
    try:
        if massping and guild:
            raider.get_random_members(guild, 1)
        url = f"https://discord.com/api/v9/channels/{channel}/messages"
        headers = raider.headers(token)
        
        for i in range(count):
            content = message
            if massping:
                content += f" {raider.get_random_members(guild, pings)}"
            if random_str:
                content += f" | {Cwelium.get_random_str(10)}"
            
            payload = {
                "content": content,
                "nonce": str(raider.nonce()),
                "tts": False
            }
            
            response = Cwelium.session.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                Cwelium.console.log("Sent", Cwelium.C["green"], token)
                if delay:
                    time.sleep(delay)
            elif response.status_code == 429:
                retry_after = response.json().get("retry_after", 1.0)
                Cwelium.console.log("Ratelimit", Cwelium.C["yellow"], token, f"Retry in {retry_after}s")
                time.sleep(float(retry_after))
            else:
                Cwelium.console.log("Failed", Cwelium.C["red"], token, response.json().get("message"))
                break
    except Exception as e:
        Cwelium.console.log("Failed", Cwelium.C["red"], token, str(e))

def custom_token_checker(raider, tokens_list):
    valid = []
    def check_token(token):
        try:
            while True:
                response = Cwelium.session.get(
                    "https://discordapp.com/api/v9/users/@me/library",
                    headers=raider.headers(token)
                )
                if response.status_code == 200:
                    Cwelium.console.log("Valid", Cwelium.C["green"], token)
                    valid.append(token)
                    break
                elif response.status_code == 403:
                    Cwelium.console.log("Locked", Cwelium.C["yellow"], token)
                    break
                elif response.status_code == 429:
                    retry_after = response.json().get("retry_after", 1.0)
                    Cwelium.console.log("Ratelimit", Cwelium.C["pink"], token, f"{retry_after}s")
                    time.sleep(retry_after)
                else:
                    Cwelium.console.log("Invalid", Cwelium.C["red"], token, response.json().get("message"))
                    break
        except Exception as e:
            Cwelium.console.log("Failed", Cwelium.C["red"], token, str(e))

    args = [(token,) for token in tokens_list]
    Cwelium.Menu().run(check_token, args)
    return valid

def custom_reactor(raider, channel_id, message_id, emoji_str):
    import urllib.parse
    encoded_emoji = urllib.parse.quote(emoji_str)
    
    def add_reaction(token):
        try:
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
            if ":" not in emoji_str:
                url += "?location=Message&type=0"
            
            response = Cwelium.session.put(url, headers=raider.headers(token))
            if response.status_code == 204:
                Cwelium.console.log("Reacted", Cwelium.C["green"], token, emoji_str)
            else:
                Cwelium.console.log("Failed", Cwelium.C["red"], token, response.json().get("message"))
        except Exception as e:
            Cwelium.console.log("Failed", Cwelium.C["red"], token, str(e))

    args = [(token,) for token in Cwelium.tokens]
    Cwelium.Menu().run(add_reaction, args)

def custom_button_click(raider, channel_id, message_id, guild_id, button_index=0):
    try:
        access_token = None
        for token in Cwelium.tokens:
            response = Cwelium.session.get(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=raider.headers(token),
                params={"around": message_id, "limit": 50}
            )
            if response.status_code == 200:
                access_token = token
                break
                
        if not access_token:
            Cwelium.console.log("Failed", Cwelium.C["red"], None, "Missing Permissions to read message")
            return

        message = next((m for m in response.json() if m["id"] == message_id), None)
        if not message:
            Cwelium.console.log("Failed", Cwelium.C["red"], None, "Message not found")
            return

        buttons = []
        for row in message.get("components", []):
            for comp in row.get("components", []):
                if comp.get("type") == 2:
                    buttons.append({
                        "label": comp.get("label", "No Label"),
                        "custom_id": comp["custom_id"]
                    })

        if not buttons:
            Cwelium.console.log("Failed", Cwelium.C["red"], None, "No buttons found in message")
            return

        idx = max(0, min(button_index, len(buttons) - 1))
        btn = buttons[idx]
        custom_id = btn["custom_id"]

        def click_button(token):
            try:
                payload = {
                    "application_id": message["author"]["id"],
                    "channel_id": channel_id,
                    "data": {
                        "component_type": 2,
                        "custom_id": custom_id,
                    },
                    "guild_id": guild_id,
                    "message_flags": 0,
                    "message_id": message_id,
                    "nonce": str(raider.nonce()),
                    "session_id": uuid.uuid4().hex,
                    "type": 3,
                }
                resp = Cwelium.session.post(
                    "https://discord.com/api/v9/interactions",
                    headers=raider.headers(token),
                    json=payload
                )
                if resp.status_code == 204:
                    Cwelium.console.log("Clicked", Cwelium.C["green"], token, btn["label"])
                else:
                    Cwelium.console.log("Failed", Cwelium.C["red"], token, resp.json().get("message"))
            except Exception as e:
                Cwelium.console.log("Failed", Cwelium.C["red"], token, str(e))

        args = [(token,) for token in Cwelium.tokens]
        Cwelium.Menu().run(click_button, args)
    except Exception as e:
        Cwelium.console.log("Failed", Cwelium.C["red"], None, f"Failed to click button: {str(e)}")

# --- FastAPI Setup ---
app = FastAPI(title="Cwelium API", description="Serverless API for Cwelium Discord Raider")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionRequest(BaseModel):
    action: str
    tokens: List[str]
    proxies: Optional[List[str]] = []
    invite: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    channel_link: Optional[str] = None
    message: Optional[str] = None
    message_link: Optional[str] = None
    bio: Optional[str] = None
    nickname: Optional[str] = None
    thread_name: Optional[str] = None
    emoji: Optional[str] = None
    user_id: Optional[str] = None
    massping: Optional[bool] = False
    pings_amount: Optional[int] = 5
    random_string: Optional[bool] = False
    delay: Optional[float] = 0.0
    spammer_count: Optional[int] = 5

@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

def cleanup_request_queue(q):
    with thread_to_queue_lock:
        keys_to_remove = [k for k, v in thread_to_queue.items() if v is q]
        for k in keys_to_remove:
            thread_to_queue.pop(k, None)

def execute_action(raider, req: ActionRequest):
    if req.action == "joiner":
        invite = req.invite
        invite = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
        raider.joiner(invite)
        
    elif req.action == "leaver":
        args = [(token, req.guild_id) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.leaver, args)
        
    elif req.action == "spammer":
        channel_id = req.channel_id
        guild_id = req.guild_id
        if req.channel_link:
            parts = req.channel_link.rstrip("/").split("/")
            if len(parts) >= 6:
                guild_id = parts[-2]
                channel_id = parts[-1]
                
        def run_spammer(token):
            custom_spammer(
                raider, 
                token, 
                channel_id, 
                req.message, 
                guild_id, 
                req.massping, 
                req.pings_amount, 
                req.random_string, 
                req.delay, 
                req.spammer_count
            )
            
        args = [(token,) for token in Cwelium.tokens]
        Cwelium.Menu().run(run_spammer, args)
        
    elif req.action == "checker":
        custom_token_checker(raider, Cwelium.tokens)
        
    elif req.action == "reactor":
        channel_id = req.channel_id
        message_id = req.message_id
        if req.message_link:
            parts = req.message_link.rstrip("/").split("/")
            if len(parts) >= 7:
                channel_id = parts[-2]
                message_id = parts[-1]
        custom_reactor(raider, channel_id, message_id, req.emoji)
        
    elif req.action == "button":
        channel_id = req.channel_id
        message_id = req.message_id
        guild_id = req.guild_id
        if req.message_link:
            parts = req.message_link.rstrip("/").split("/")
            if len(parts) >= 7:
                guild_id = parts[-3]
                channel_id = parts[-2]
                message_id = parts[-1]
        custom_button_click(raider, channel_id, message_id, guild_id, 0)
        
    elif req.action == "accept":
        raider.accept_rules(req.guild_id)
        
    elif req.action == "guild":
        raider.guild_checker(req.guild_id)
        
    elif req.action == "bio":
        args = [(token, req.bio) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.bio_changer, args)
        
    elif req.action == "onboard":
        raider.onboard_bypass(req.guild_id)
        
    elif req.action == "voice_joiner":
        channel_id = req.channel_id
        guild_id = req.guild_id
        if req.channel_link:
            parts = req.channel_link.rstrip("/").split("/")
            if len(parts) >= 6:
                guild_id = parts[-2]
                channel_id = parts[-1]
        args = [(token, guild_id, channel_id) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.join_voice_channel, args)
        
    elif req.action == "friender":
        args = [(token, req.nickname) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.friender, args)
        
    elif req.action == "caller":
        args = [(token, req.user_id) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.call_spammer, args)
        
    elif req.action == "dm_spam":
        args = [(token, req.user_id, req.message) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.dm_spammer, args)
        
    elif req.action == "typer":
        channel_id = req.channel_id
        if req.channel_link:
            parts = req.channel_link.rstrip("/").split("/")
            if len(parts) >= 6:
                channel_id = parts[-1]
        args = [(token, channel_id) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.typier, args)
        
    elif req.action == "nick_changer":
        args = [(token, req.guild_id, req.nickname) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.mass_nick, args)
        
    elif req.action == "thread_spammer":
        channel_id = req.channel_id
        if req.channel_link:
            parts = req.channel_link.rstrip("/").split("/")
            if len(parts) >= 6:
                channel_id = parts[-1]
        args = [(token, channel_id, req.thread_name) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.thread_spammer, args)
        
    elif req.action == "onliner":
        import websocket
        args = [(token, websocket.WebSocket()) for token in Cwelium.tokens]
        Cwelium.Menu().run(raider.onliner, args)
        
    else:
        raise ValueError(f"Unknown action: {req.action}")

@app.post("/api/run")
def run(req: ActionRequest):
    q = queue.Queue()
    
    def worker():
        # Setup thread context mapping
        main_thread_id = threading.current_thread().ident
        with thread_to_queue_lock:
            thread_to_queue[main_thread_id] = q
            
        try:
            # Set memory tokens/proxies dynamically
            Cwelium.tokens = [t.strip() for t in req.tokens if t.strip()]
            Cwelium.proxies = [p.strip() for p in req.proxies if p.strip()]
            Cwelium.proxy = len(Cwelium.proxies) > 0
            
            raider = Cwelium.Raider()
            execute_action(raider, req)
        except Exception as e:
            q.put({
                "timestamp": datetime.now().strftime('%H:%M:%S'),
                "type": "Error",
                "token": None,
                "message": f"Execution failed: {str(e)}",
                "raw": f"[{datetime.now().strftime('%H:%M:%S')}] [Error] Execution failed ({str(e)})"
            })
        finally:
            # Signal completion
            q.put(None)
            
    t = threading.Thread(target=worker)
    t.start()
    
    def event_generator():
        while True:
            try:
                # Wait for logs from the queue
                log_item = q.get(timeout=20.0)
                if log_item is None:
                    break
                yield f"data: {json_dumps(log_item)}\n\n"
            except queue.Empty:
                yield "data: {\"ping\": true}\n\n"
        
        cleanup_request_queue(q)
        yield "data: {\"done\": true}\n\n"

    # Helper to serialize JSON quickly
    def json_dumps(obj):
        import json
        return json.dumps(obj)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve the frontend static files locally
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="public", html=True), name="public")
