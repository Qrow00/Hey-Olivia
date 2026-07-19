import asyncio
import subprocess
import os
import re
import json
import webbrowser
from pathlib import Path
from datetime import datetime, timezone


class SystemCommandService:
    def __init__(self):
        self.opencode_path = "opencode"
        self.current_dir = os.path.expanduser("~")
        self._folder_cache = None
        self._folder_cache_time = 0
        self._cache_ttl = 300
        self._skip_dirs = set()
        self._scan_dirs = []
        self._load_config()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "scan_config.json")
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
            self._skip_dirs = set(cfg.get("skip_dirs", []))
            self._scan_dirs = cfg.get("scan_dirs", [])
            self._cache_ttl = cfg.get("cache_ttl_seconds", 300)
        except:
            self._skip_dirs = {".git", ".cache", ".local", ".vscode", "AppData", "node_modules", "__pycache__"}
            self._scan_dirs = []

    def _should_skip(self, name: str) -> bool:
        return name.startswith(".") or name in self._skip_dirs

    def _scan_folder(self, path: str, depth: int = 0, max_depth: int = 2) -> dict:
        result = {"path": path, "name": os.path.basename(path), "subfolders": [], "files": []}
        if depth >= max_depth:
            return result
        try:
            for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
                if self._should_skip(entry.name):
                    continue
                if entry.is_dir():
                    sub = self._scan_folder(entry.path, depth + 1, max_depth)
                    sub["name"] = entry.name
                    result["subfolders"].append(sub)
                else:
                    result["files"].append(entry.name)
        except PermissionError:
            pass
        return result

    async def _run(self, cmd: str, timeout: int = 30) -> dict:
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "status": "success" if proc.returncode == 0 else "error",
                "stdout": stdout.decode(errors="replace").strip(),
                "stderr": stderr.decode(errors="replace").strip(),
                "exit_code": proc.returncode,
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"status": "error", "message": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_time(self) -> dict:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        return {"status": "success", "time": time_str, "message": f"The current time is {time_str}."}

    async def get_date(self) -> dict:
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return {"status": "success", "date": date_str, "message": f"Today is {date_str}."}

    async def _run_sync(self, cmd: str, timeout: int = 30) -> dict:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def open_app(self, app_name: str) -> dict:
        app_name = app_name.strip().lower()
        app_aliases = {
            "brave": "brave",
            "brave browser": "brave",
            "google chrome": "chrome",
            "chrome": "chrome",
            "chrome browser": "chrome",
            "firefox": "firefox",
            "mozilla": "firefox",
            "mozilla firefox": "firefox",
            "edge": "msedge",
            "microsoft edge": "msedge",
            "edge browser": "msedge",
            "notepad": "notepad",
            "notepad++": "notepad++",
            "visual studio code": "code",
            "vs code": "code",
            "vscode": "code",
            "code": "code",
            "spotify": "spotify",
            "discord": "discord",
            "slack": "slack",
            "telegram": "telegram",
            "whatsapp": "whatsapp",
            "file explorer": "explorer",
            "explorer": "explorer",
            "files": "explorer",
            "calculator": "calc",
            "calc": "calc",
            "paint": "mspaint",
            "word": "winword",
            "microsoft word": "winword",
            "excel": "excel",
            "microsoft excel": "excel",
            "powerpoint": "powerpnt",
            "microsoft powerpoint": "powerpnt",
            "terminal": "cmd",
            "cmd": "cmd",
            "command prompt": "cmd",
            "powershell": "pwsh",
            "photoshop": "photoshop",
            "premiere": "premiere",
            "obs": "obs64",
            "obs studio": "obs64",
            "steam": "steam",
            "epic": "epicgameslauncher",
            "epic games": "epicgameslauncher",
            "blender": "blender",
            "sublime": "sublime_text",
            "sublime text": "sublime_text",
            "intellij": "idea64",
            "pycharm": "pycharm64",
            "android studio": "studio64",
            "vlc": "vlc",
            "media player": "wmplayer",
            "onedrive": "onedrive",
            "onedrive - personal": "onedrive",
        }
        resolved = app_aliases.get(app_name, app_name)

        try:
            check = await asyncio.create_subprocess_shell(
                f'where {resolved}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(check.communicate(), timeout=3)
            if check.returncode != 0:
                return {"status": "error", "message": f"I couldn't find an app called '{app_name}' on your PC. It may not be installed."}
        except:
            pass

        try:
            proc = await asyncio.create_subprocess_shell(
                f'start "" "{resolved}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=5)
            return {"message": f"Opening {app_name}", "status": "success"}
        except asyncio.TimeoutError:
            return {"message": f"Opening {app_name}", "status": "success"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open {app_name}: {e}"}

    async def open_browser(self, url: str = "") -> dict:
        url = url.strip()
        if not url:
            url = "https://www.google.com"
        elif not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return {"status": "success", "message": f"Opened {url}"}

    async def open_youtube(self, query: str = "") -> dict:
        query = query.strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = "https://www.youtube.com"
        webbrowser.open(url)
        return {"status": "success", "message": f"Opened YouTube{' for ' + query if query else ''}"}

    async def play_youtube(self, query: str = "") -> dict:
        query = query.strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = "https://music.youtube.com"
        webbrowser.open(url)
        return {"status": "success", "message": f"Playing {query} on YouTube Music" if query else "Opened YouTube Music"}

    async def open_file_explorer(self, path: str = "") -> dict:
        path = path.strip().lower()
        home = os.path.expanduser("~")
        path_map = {
            "": home,
            "home": home,
            "desktop": os.path.join(home, "Desktop"),
            "documents": os.path.join(home, "Documents"),
            "downloads": os.path.join(home, "Downloads"),
            "pictures": os.path.join(home, "Pictures"),
            "music": os.path.join(home, "Music"),
            "videos": os.path.join(home, "Videos"),
            "onedrive": os.path.join(home, "OneDrive"),
            "onedrive - personal": os.path.join(home, "OneDrive"),
            "onedrive - school": os.path.join(home, "OneDrive - School"),
            "onedrive - work": os.path.join(home, "OneDrive - Work"),
        }
        resolved = path_map.get(path, path)
        if resolved == path and not os.path.isdir(resolved):
            for key, val in path_map.items():
                if path in key or key in path:
                    resolved = val
                    break
        if not os.path.isdir(resolved):
            home_entries = os.listdir(home)
            for entry in home_entries:
                if path.lower() in entry.lower():
                    candidate = os.path.join(home, entry)
                    if os.path.isdir(candidate):
                        resolved = candidate
                        break
        if not os.path.isdir(resolved):
            return {"status": "error", "message": f"I couldn't find a folder called '{path}' on your PC. It may not exist or may be named differently."}
        try:
            proc = await asyncio.create_subprocess_shell(
                f'start "" "{resolved}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=5)
        except:
            pass
        return {"message": f"Opened {os.path.basename(resolved)}", "status": "success", "path": resolved}

    async def open_terminal(self, path: str = "") -> dict:
        path = path.strip()
        if path:
            result = await self._run(f'start cmd /k "cd /d {path}"')
        else:
            result = await self._run("start cmd")
        return {"message": "Opened terminal", **result}

    async def open_opencode(self, task: str = "") -> dict:
        task = task.strip()
        if task:
            result = await self._run(f'{self.opencode_path} "{task}"', timeout=60)
        else:
            result = await self._run(f"start cmd /k \"{self.opencode_path}\"")
            return {"message": "Opened opencode", **result}
        return {"message": f"Ran opencode: {task}", **result}

    async def close_app(self, app_name: str) -> dict:
        app_name = app_name.strip()
        result = await self._run(f'taskkill /IM "{app_name}.exe" /F')
        return {"message": f"Closed {app_name}", **result}

    async def screenshot(self) -> dict:
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        result = await self._run(
            f'snippingtool /clip /save "{path}"', timeout=10
        )
        if result["status"] == "error":
            result = await self._run(
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; '
                f'$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, '
                f'[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); '
                f'$gfx = [System.Drawing.Graphics]::FromImage($bmp); '
                f'$gfx.CopyFromScreen(0, 0, 0, 0, $bmp.Size); '
                f'$bmp.Save(\'{path}\')"'
            )
        return {"message": f"Screenshot saved to {path}", **result}

    async def list_processes(self) -> dict:
        result = await self._run("tasklist /FO CSV")
        lines = result.get("stdout", "").split("\n")
        procs = []
        for line in lines[1:20]:
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 5:
                procs.append({"name": parts[0], "pid": parts[1], "memory": parts[4]})
        return {"status": "success", "processes": procs, "message": f"Top {len(procs)} processes"}

    async def get_system_info(self) -> dict:
        result = await self._run(
            'systeminfo | findstr /C:"OS Name" /C:"Total Physical Memory" /C:"Processor"'
        )
        return {"status": "success", "info": result.get("stdout", ""), "message": "System info retrieved"}

    async def get_disk_usage(self) -> dict:
        result = await self._run("wmic logicaldisk get size,freespace,caption")
        return {"status": "success", "disks": result.get("stdout", ""), "message": "Disk usage retrieved"}

    async def set_volume(self, level: str) -> dict:
        level = level.strip().rstrip("%")
        try:
            vol = int(level)
            vol = max(0, min(100, vol))
        except ValueError:
            return {"status": "error", "message": "Invalid volume level"}
        result = await self._run(
            f'powershell -Command "$wsh = New-Object -ComObject WScript.Shell; '
            f'1..50 | ForEach-Object {{$wsh.SendKeys([char]174)}}; '
            f'1..{vol // 2} | ForEach-Object {{$wsh.SendKeys([char]175)}}"'
        )
        return {"message": f"Volume set to {vol}%", **result}

    async def mute(self) -> dict:
        result = await self._run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"'
        )
        return {"message": "Toggled mute", **result}

    async def next_track(self) -> dict:
        result = await self._run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"'
        )
        return {"message": "Next track", **result}

    async def previous_track(self) -> dict:
        result = await self._run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]177)"'
        )
        return {"message": "Previous track", **result}

    async def play_pause(self) -> dict:
        result = await self._run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"'
        )
        return {"message": "Play/Pause toggled", **result}

    async def shutdown(self, delay: str = "0") -> dict:
        result = await self._run(f"shutdown /s /t {delay}")
        return {"message": f"Shutting down in {delay} seconds", **result}

    async def restart(self) -> dict:
        result = await self._run("shutdown /r /t 0")
        return {"message": "Restarting", **result}

    async def lock_pc(self) -> dict:
        result = await self._run("rundll32.exe user32.dll,LockWorkStation")
        return {"message": "PC locked", **result}

    async def sleep_pc(self) -> dict:
        result = await self._run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return {"message": "PC going to sleep", **result}

    async def run_command(self, command: str) -> dict:
        result = await self._run(command, timeout=60)
        output = result.get("stdout", result.get("message", ""))
        if len(output) > 500:
            output = output[:500] + "..."
        return {"message": f"Command executed", "output": output, **result}

    async def search_files(self, query: str) -> dict:
        home = os.path.expanduser("~")
        result = await self._run(
            f'dir /s /b "{home}\\{query}*" 2>nul', timeout=15
        )
        files = result.get("stdout", "").split("\n")[:10]
        files = [f for f in files if f.strip()]
        return {"status": "success", "files": files, "message": f"Found {len(files)} files matching '{query}'"}

    async def list_dir(self, path: str = "") -> dict:
        path = path.strip() if path else self.current_dir
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            return {"status": "error", "message": f"Not a directory: {path}"}
        self.current_dir = os.path.abspath(path)
        entries = []
        try:
            for entry in sorted(os.scandir(self.current_dir), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name.startswith("."):
                    continue
                entry_type = "folder" if entry.is_dir() else "file"
                size = ""
                if entry_type == "file":
                    try:
                        s = entry.stat().st_size
                        if s >= 1024 * 1024:
                            size = f"{s / (1024 * 1024):.1f} MB"
                        elif s >= 1024:
                            size = f"{s / 1024:.1f} KB"
                        else:
                            size = f"{s} B"
                    except:
                        pass
                entries.append({"name": entry.name, "type": entry_type, "size": size})
        except PermissionError:
            return {"status": "error", "message": f"Permission denied: {self.current_dir}"}
        folders = [e for e in entries if e["type"] == "folder"]
        files = [e for e in entries if e["type"] == "file"]
        summary = f"In {self.current_dir}: {len(folders)} folders, {len(files)} files"
        if folders:
            summary += f"\nFolders: {', '.join(e['name'] for e in folders[:15])}"
        if files:
            file_list = files[:10]
            summary += f"\nFiles: {', '.join(e['name'] + (' (' + e['size'] + ')' if e['size'] else '') for e in file_list)}"
            if len(files) > 10:
                summary += f" and {len(files) - 10} more"
        return {"status": "success", "current_dir": self.current_dir, "folders": [e["name"] for e in folders], "files": [e["name"] for e in files], "message": summary}

    async def navigate_to(self, folder_name: str) -> dict:
        folder_name = folder_name.strip()
        target = os.path.join(self.current_dir, folder_name)
        if not os.path.isdir(target):
            matches = []
            for entry in os.scandir(self.current_dir):
                if entry.is_dir() and folder_name.lower() in entry.name.lower():
                    matches.append(entry.name)
            if len(matches) == 1:
                target = os.path.join(self.current_dir, matches[0])
            elif len(matches) > 1:
                return {"status": "error", "message": f"Multiple matches: {', '.join(matches)}. Be more specific."}
            else:
                return {"status": "error", "message": f"Folder '{folder_name}' not found in {self.current_dir}"}
        self.current_dir = os.path.abspath(target)
        return await self.list_dir()

    async def go_back(self) -> dict:
        parent = os.path.dirname(self.current_dir)
        if parent == self.current_dir:
            return {"status": "error", "message": "Already at root"}
        self.current_dir = parent
        return await self.list_dir()

    async def go_home(self) -> dict:
        self.current_dir = os.path.expanduser("~")
        return await self.list_dir()

    async def open_file(self, filename: str) -> dict:
        filename = filename.strip()
        target = os.path.join(self.current_dir, filename)
        if not os.path.exists(target):
            for entry in os.scandir(self.current_dir):
                if entry.is_file() and filename.lower() in entry.name.lower():
                    target = entry.path
                    break
        if not os.path.exists(target):
            return {"status": "error", "message": f"File '{filename}' not found in {self.current_dir}"}
        result = await self._run(f'start "" "{target}"')
        return {"message": f"Opened {os.path.basename(target)}", **result}

    async def read_file(self, filename: str) -> dict:
        filename = filename.strip()
        target = os.path.join(self.current_dir, filename)
        if not os.path.exists(target):
            for entry in os.scandir(self.current_dir):
                if entry.is_file() and filename.lower() in entry.name.lower():
                    target = entry.path
                    break
        if not os.path.exists(target):
            return {"status": "error", "message": f"File '{filename}' not found"}
        try:
            size = os.path.getsize(target)
            if size > 1_000_000:
                return {"status": "error", "message": f"File too large: {size / (1024*1024):.1f} MB"}
            text_extensions = {'.txt', '.py', '.js', '.ts', '.dart', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.md', '.csv', '.log', '.ini', '.cfg', '.toml', '.sh', '.bat', '.ps1', '.sql', '.r', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt'}
            ext = os.path.splitext(target)[1].lower()
            if ext not in text_extensions:
                return {"status": "success", "message": f"Cannot read {ext} file. Opened instead.", "file": target}
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(5000)
            lines = content.count("\n") + 1
            return {"status": "success", "content": content, "lines": lines, "file": target, "message": f"Read {lines} lines from {os.path.basename(target)}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_current_location(self) -> dict:
        return {"status": "success", "current_dir": self.current_dir, "message": f"Currently in {self.current_dir}"}

    async def get_folder_map(self) -> dict:
        now = datetime.now().timestamp()
        if self._folder_cache and (now - self._folder_cache_time) < self._cache_ttl:
            return self._folder_cache

        home = os.path.expanduser("~")
        folder_map = {"home": home, "current": self.current_dir}
        top_level = []
        scan_targets = []

        if self._scan_dirs:
            for d in self._scan_dirs:
                expanded = os.path.expanduser(d)
                if os.path.isdir(expanded):
                    scan_targets.append(expanded)
        else:
            scan_targets = [home]

        for target in scan_targets:
            tree = self._scan_folder(target, max_depth=2)
            if target == home:
                for sub in tree["subfolders"]:
                    name = sub["name"]
                    top_level.append(name)
                    if sub["subfolders"]:
                        folder_map[name.lower()] = {
                            "path": sub["path"],
                            "subfolders": [s["name"] for s in sub["subfolders"][:20]],
                        }
                    else:
                        folder_map[name.lower()] = sub["path"]
            else:
                rel = os.path.relpath(target, home)
                folder_map[rel.lower()] = {
                    "path": target,
                    "subfolders": [s["name"] for s in tree["subfolders"][:20]],
                }

        summary = f"Home: {home}\nCurrent: {self.current_dir}\nFolders: {', '.join(top_level)}"
        result = {
            "status": "success",
            "folder_map": folder_map,
            "top_level": top_level,
            "current_dir": self.current_dir,
            "home": home,
            "message": summary,
        }
        self._folder_cache = result
        self._folder_cache_time = now
        return result

    async def deep_scan(self, folder_name: str) -> dict:
        home = os.path.expanduser("~")
        target = None
        if os.path.isdir(folder_name):
            target = folder_name
        else:
            candidate = os.path.join(self.current_dir, folder_name)
            if os.path.isdir(candidate):
                target = candidate
            else:
                candidate = os.path.join(home, folder_name)
                if os.path.isdir(candidate):
                    target = candidate
        if not target:
            for entry in os.scandir(home):
                if entry.is_dir() and folder_name.lower() in entry.name.lower():
                    target = entry.path
                    break
        if not target:
            return {"status": "error", "message": f"Folder '{folder_name}' not found"}

        tree = self._scan_folder(target, max_depth=3)
        flat = []
        def _flatten(node, prefix=""):
            for sub in node["subfolders"]:
                path = os.path.join(prefix, sub["name"]) if prefix else sub["name"]
                flat.append({"name": path, "type": "folder", "path": sub["path"]})
                _flatten(sub, path)
            for f in node["files"]:
                flat.append({"name": os.path.join(prefix, f) if prefix else f, "type": "file"})
        _flatten(tree)

        summary = f"Deep scan of {target}:\n{len([f for f in flat if f['type'] == 'folder'])} folders, {len([f for f in flat if f['type'] == 'file'])} files"
        folder_list = [f["name"] for f in flat if f["type"] == "folder"][:30]
        if folder_list:
            summary += f"\nFolders: {', '.join(folder_list)}"
        return {"status": "success", "path": target, "entries": flat[:50], "message": summary}

    async def remember(self, text: str) -> dict:
        text = text.strip()
        kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "knowledge_base.json")
        kb = {"entries": [], "facts": [], "preferences": [], "people": [], "rules": []}
        try:
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
        except:
            pass

        import ollama
        categorize_prompt = (
            f'Categorize this statement into JSON with fields: category (fact/preference/rule/person/place/other), '
            f'subject (main topic), predicate (what about it), summary (one-line rewrite).\n\n'
            f'Statement: "{text}"\n\nReturn ONLY valid JSON, no explanation.'
        )
        try:
            resp = ollama.chat(
                model="llama3.2",
                messages=[{"role": "user", "content": categorize_prompt}],
                options={"temperature": 0.0, "num_predict": 100},
            )
            raw = resp["message"]["content"].strip()
            raw = re.sub(r'```json\n?|\n?```', '', raw).strip()
            parsed = json.loads(raw)
        except:
            parsed = {"category": "other", "subject": text[:30], "predicate": "is", "summary": text}

        entry = {
            "content": text,
            "category": parsed.get("category", "other"),
            "subject": parsed.get("subject", ""),
            "predicate": parsed.get("predicate", ""),
            "summary": parsed.get("summary", text),
            "timestamp": datetime.now().isoformat(),
        }

        kb["entries"].append(entry)
        cat = entry["category"]
        if cat in kb and isinstance(kb[cat], list):
            kb[cat].append(entry)

        kb["entries"] = kb["entries"][-200:]
        for key in ["facts", "preferences", "rules", "people", "places"]:
            if key in kb and isinstance(kb[key], list):
                kb[key] = kb[key][-50:]

        os.makedirs(os.path.dirname(kb_path), exist_ok=True)
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb, f, indent=2, ensure_ascii=False)

        cat_labels = {"fact": "a fact", "preference": "a preference", "rule": "a rule", "person": "about a person", "place": "about a place"}
        label = cat_labels.get(cat, "something")
        return {"status": "success", "message": f"I have learned {label}: {entry['summary']}"}

    async def recall(self, query: str = "") -> dict:
        kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "knowledge_base.json")
        kb = {"entries": []}
        try:
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
        except:
            pass

        entries = kb.get("entries", [])
        if not entries:
            return {"status": "success", "message": "I haven't learned anything yet. Teach me something!", "memories": []}

        query_lower = query.strip().lower()
        if query_lower:
            matched = [e for e in entries if query_lower in e.get("content", "").lower() or query_lower in e.get("subject", "").lower() or query_lower in e.get("summary", "").lower()]
            if not matched:
                return {"status": "success", "message": f"I don't know anything about '{query}' yet. You can teach me by saying 'remember that {query} is...'", "memories": []}
            items = "\n".join(f"- [{e.get('category', 'other')}] {e.get('summary', e.get('content', ''))}" for e in matched[-10:])
            return {"status": "success", "message": f"Here is what I know about '{query}':\n{items}", "memories": matched}

        recent = entries[-15:]
        items = "\n".join(f"- [{e.get('category', 'other')}] {e.get('summary', e.get('content', ''))}" for e in recent)
        return {"status": "success", "message": f"Here is everything I have learned so far:\n{items}", "memories": recent}

    async def forget(self, text: str) -> dict:
        kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "knowledge_base.json")
        kb = {"entries": [], "facts": [], "preferences": [], "rules": [], "people": []}
        try:
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
        except:
            pass

        text_lower = text.strip().lower()
        if text_lower in ("clear memory", "reset memory", "forget everything"):
            kb = {"entries": [], "facts": [], "preferences": [], "rules": [], "people": [], "places": [], "other": []}
            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(kb, f, indent=2, ensure_ascii=False)
            return {"status": "success", "message": "I have forgotten everything. My mind is blank."}

        before = len(kb.get("entries", []))
        kb["entries"] = [e for e in kb.get("entries", []) if text_lower not in e.get("content", "").lower() and text_lower not in e.get("subject", "").lower()]
        for key in ["facts", "preferences", "rules", "people", "places", "other"]:
            if key in kb and isinstance(kb[key], list):
                kb[key] = [e for e in kb[key] if text_lower not in e.get("content", "").lower() and text_lower not in e.get("subject", "").lower()]
        removed = before - len(kb.get("entries", []))

        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb, f, indent=2, ensure_ascii=False)

        if removed == 0:
            return {"status": "success", "message": f"I couldn't find anything about '{text}' in my knowledge."}
        return {"status": "success", "message": f"I have forgotten {removed} thing(s) about '{text}'."}

    async def get_knowledge_summary(self) -> dict:
        kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "knowledge_base.json")
        kb = {"entries": [], "facts": [], "preferences": [], "rules": [], "people": []}
        try:
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
        except:
            pass

        entries = kb.get("entries", [])
        cats = {}
        for e in entries:
            c = e.get("category", "other")
            cats[c] = cats.get(c, 0) + 1
        summary = ", ".join(f"{v} {k}s" for k, v in sorted(cats.items(), key=lambda x: -x[1]))
        return {"status": "success", "total": len(entries), "by_category": cats, "message": f"I know {len(entries)} things: {summary}" if entries else "I haven't learned anything yet."}


system_command_service = SystemCommandService()
