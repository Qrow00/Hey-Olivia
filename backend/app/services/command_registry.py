import re
import json
from typing import Optional, Callable, Any
from dataclasses import dataclass, field


@dataclass
class CommandPattern:
    patterns: list[str]
    handler: str
    description: str
    category: str = "general"
    examples: list[str] = field(default_factory=list)


class CommandRegistry:
    def __init__(self):
        self.commands: dict[str, CommandPattern] = {}
        self.handlers: dict[str, Callable] = {}
        self._register_default_commands()

    def _register_default_commands(self):
        self.register(CommandPattern(
            patterns=[r"what time", r"what's the time", r"tell me the time", r"current time"],
            handler="get_time",
            description="Get the current time",
            category="system",
            examples=["What time is it?", "Tell me the time"],
        ))

        self.register(CommandPattern(
            patterns=[r"what date", r"what's the date", r"today's date", r"what day"],
            handler="get_date",
            description="Get the current date",
            category="system",
            examples=["What's today's date?", "What day is it?"],
        ))

        self.register(CommandPattern(
            patterns=[r"turn on (?:the )?(.+)", r"switch on (?:the )?(.+)", r"enable (?:the )?(.+)"],
            handler="turn_on_device",
            description="Turn on a smart device",
            category="smart_home",
            examples=["Turn on the lights", "Switch on the AC"],
        ))

        self.register(CommandPattern(
            patterns=[r"turn off (?:the )?(.+)", r"switch off (?:the )?(.+)", r"disable (?:the )?(.+)"],
            handler="turn_off_device",
            description="Turn off a smart device",
            category="smart_home",
            examples=["Turn off the lights", "Switch off the fan"],
        ))

        self.register(CommandPattern(
            patterns=[r"set (?:the )?(?:brightness|light) to (\d+)", r"brightness (\d+)"],
            handler="set_brightness",
            description="Set light brightness",
            category="smart_home",
            examples=["Set brightness to 50", "Light 75"],
        ))

        self.register(CommandPattern(
            patterns=[r"set (?:the )?temperature to (\d+)", r"temperature (\d+)"],
            handler="set_temperature",
            description="Set thermostat temperature",
            category="smart_home",
            examples=["Set temperature to 22", "Temperature 24"],
        ))

        self.register(CommandPattern(
            patterns=[r"show (?:me )?(?:the )?cameras?", r"open cameras?", r"view cameras?"],
            handler="show_cameras",
            description="Show camera feeds",
            category="camera",
            examples=["Show me the cameras", "Open camera view"],
        ))

        self.register(CommandPattern(
            patterns=[r"show (?:camera|feed) (.+)"],
            handler="show_camera",
            description="Show specific camera",
            category="camera",
            examples=["Show camera front door", "Show kitchen feed"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:what's|what is|show) my (?:heart rate|pulse)", r"heart rate"],
            handler="get_heart_rate",
            description="Get current heart rate",
            category="health",
            examples=["What's my heart rate?", "Show my heart rate"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:what's|what is|show) my (?:blood oxygen|oxygen|spo2)", r"blood oxygen"],
            handler="get_spo2",
            description="Get blood oxygen level",
            category="health",
            examples=["What's my blood oxygen?", "Show my SpO2"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:how many|what are) my steps", r"step count", r"steps today"],
            handler="get_steps",
            description="Get today's step count",
            category="health",
            examples=["How many steps today?", "What's my step count?"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:how did|what was) (?:i|my) (?:sleep|last night)", r"sleep data"],
            handler="get_sleep",
            description="Get sleep data",
            category="health",
            examples=["How did I sleep last night?", "Show my sleep data"],
        ))

        self.register(CommandPattern(
            patterns=[r"share (?:my )?screen", r"start screen share", r"show (?:my )?screen"],
            handler="start_screen_share",
            description="Start screen sharing",
            category="screen",
            examples=["Share my screen", "Start screen share"],
        ))

        self.register(CommandPattern(
            patterns=[r"stop screen share", r"end screen share", r"close screen"],
            handler="stop_screen_share",
            description="Stop screen sharing",
            category="screen",
            examples=["Stop screen share", "End screen sharing"],
        ))

        self.register(CommandPattern(
            patterns=[r"play (?:the )?(.+)", r"play music (.+)"],
            handler="play_music",
            description="Play music",
            category="media",
            examples=["Play some music", "Play jazz"],
        ))

        self.register(CommandPattern(
            patterns=[r"stop (?:music|playing|the music)"],
            handler="stop_music",
            description="Stop music playback",
            category="media",
            examples=["Stop music", "Stop playing"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:what's|what is) the (?:weather|temperature) (?:in|at|for) (.+)", r"weather in (.+)"],
            handler="get_weather",
            description="Get weather for a location",
            category="info",
            examples=["What's the weather in Manila?", "Weather in Tokyo"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:search|look up|find) (.+)"],
            handler="search",
            description="Search for information",
            category="info",
            examples=["Search for Flutter tutorials", "Look up recipes"],
        ))

        self.register(CommandPattern(
            patterns=[r"remind me to (.+) (?:at|in|on) (.+)"],
            handler="set_reminder",
            description="Set a reminder",
            category="system",
            examples=["Remind me to call mom at 5pm", "Remind me to take medicine in 2 hours"],
        ))

        self.register(CommandPattern(
            patterns=[r"take (?:a )?(?:photo|picture|snapshot)", r"capture"],
            handler="take_photo",
            description="Take a photo",
            category="camera",
            examples=["Take a photo", "Capture a picture"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:read|what's) (?:the )?(?:notification|alerts?)"],
            handler="read_notifications",
            description="Read notifications",
            category="system",
            examples=["Read my notifications", "What are my alerts?"],
        ))

        self.register(CommandPattern(
            patterns=[r"lock (?:the )?(?:door|doors|all)"],
            handler="lock_doors",
            description="Lock smart locks",
            category="smart_home",
            examples=["Lock the door", "Lock all doors"],
        ))

        self.register(CommandPattern(
            patterns=[r"unlock (?:the )?(?:door|doors)"],
            handler="unlock_doors",
            description="Unlock smart locks",
            category="smart_home",
            examples=["Unlock the front door"],
        ))

        self.register(CommandPattern(
            patterns=[r"what do you see", r"what can you see", r"describe (?:the )?(?:scene|camera|feed|view)"],
            handler="what_do_you_see",
            description="Describe what the AI sees on cameras",
            category="vision",
            examples=["What do you see?", "Describe the scene", "What can you see?"],
        ))

        self.register(CommandPattern(
            patterns=[r"look at (?:camera|the) (.+)", r"check (?:camera|the) (.+)", r"what's on (.+) camera"],
            handler="look_at_camera",
            description="Look at a specific camera",
            category="vision",
            examples=["Look at front door camera", "Check the living room", "What's on the kitchen camera?"],
        ))

        self.register(CommandPattern(
            patterns=[r"scan (?:all )?cameras?", r"scan (?:the )?(?:house|home|premises)"],
            handler="scan_cameras",
            description="Scan all cameras for activity",
            category="vision",
            examples=["Scan cameras", "Scan the house", "Scan all cameras"],
        ))

        self.register(CommandPattern(
            patterns=[r"watch (?:camera|the) (.+)", r"monitor (?:camera|the) (.+)", r"keep (?:an? )?eye on (.+)"],
            handler="watch_camera",
            description="Start monitoring a camera",
            category="vision",
            examples=["Watch the front door", "Monitor camera 1", "Keep an eye on the garage"],
        ))

        self.register(CommandPattern(
            patterns=[r"stop watching", r"stop monitoring", r"stop watching (.+)"],
            handler="stop_watching",
            description="Stop camera monitoring",
            category="vision",
            examples=["Stop watching", "Stop monitoring"],
        ))

        self.register(CommandPattern(
            patterns=[r"who (?:is|are) (?:that|there|at) (.+)", r"who (?:is|are) (?:in|inside) (.+)"],
            handler="who_is_there",
            description="Identify people at a location",
            category="vision",
            examples=["Who is at the front door?", "Who's in the living room?"],
        ))

        self.register(CommandPattern(
            patterns=[r"is (?:anyone|somebody|anybody) (?:there|home|inside|outside|around)"],
            handler="is_anyone_there",
            description="Check if anyone is around",
            category="vision",
            examples=["Is anyone there?", "Is someone outside?"],
        ))

        self.register(CommandPattern(
            patterns=[r"what(?:'s| is) (?:the|my) (.+) doing", r"what is happening (?:at|in|on) (.+)"],
            handler="what_is_happening",
            description="Describe activity at a location",
            category="vision",
            examples=["What's the cat doing?", "What is happening in the backyard?"],
        ))

        self.register(CommandPattern(
            patterns=[r"good\s*bye", r"bye", r"see you", r"see ya", r"exit", r"quit", r"close"],
            handler="goodbye",
            description="Say goodbye and close the app",
            category="system",
            examples=["Good bye", r"Bye", "See you later", "Exit"],
        ))

        self.register(CommandPattern(
            patterns=[r"search (?:for )?(.+)", r"google (.+)", r"look up (.+)"],
            handler="browser_search",
            description="Search Google for a query",
            category="browser",
            examples=["Search for Flutter docs", "Google weather today", "Look up restaurants near me"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:open|go to|visit|navigate to) (?:https?://)?(.+)"],
            handler="browser_navigate",
            description="Navigate to a website",
            category="browser",
            examples=["Open github.com", "Go to youtube.com", "Visit example.com"],
        ))

        self.register(CommandPattern(
            patterns=[r"click (.+)", r"press (.+)"],
            handler="browser_click",
            description="Click an element on the page",
            category="browser",
            examples=["Click the search button", "Press submit"],
        ))

        self.register(CommandPattern(
            patterns=[r"type (.+) in (.+)", r"enter (.+) in (.+)", r"input (.+) into (.+)"],
            handler="browser_type",
            description="Type text into a form field",
            category="browser",
            examples=["Type hello in the search box", "Enter my email in the field"],
        ))

        self.register(CommandPattern(
            patterns=[r"take (?:a )?screenshot", r"capture (?:the )?page", r"snapshot"],
            handler="browser_screenshot",
            description="Take a screenshot of the current page",
            category="browser",
            examples=["Take a screenshot", "Capture the page"],
        ))

        self.register(CommandPattern(
            patterns=[r"scroll (?:the )?(?:page )?(?:up|down)", r"(?:go )?(?:up|down) (?:the )?page"],
            handler="browser_scroll",
            description="Scroll the page up or down",
            category="browser",
            examples=["Scroll down", "Go up the page", "Scroll the page down"],
        ))

        self.register(CommandPattern(
            patterns=[r"what(?:'s| is) (?:on )?(?:the )?page", r"read (?:the )?page", r"what do you see (?:on )?(?:the )?page"],
            handler="browser_snapshot",
            description="Get the accessibility tree of the current page",
            category="browser",
            examples=["What's on the page?", "Read the page", "What do you see?"],
        ))

        self.register(CommandPattern(
            patterns=[r"go back", r"(?:navigate )?back"],
            handler="browser_back",
            description="Go back to the previous page",
            category="browser",
            examples=["Go back", "Navigate back"],
        ))

        self.register(CommandPattern(
            patterns=[r"go forward", r"(?:navigate )?forward"],
            handler="browser_forward",
            description="Go forward to the next page",
            category="browser",
            examples=["Go forward", "Navigate forward"],
        ))

        self.register(CommandPattern(
            patterns=[r"start (?:a )?browser", r"open browser", r"launch browser"],
            handler="browser_start",
            description="Start a browser session",
            category="browser",
            examples=["Start a browser", "Open browser"],
        ))

        self.register(CommandPattern(
            patterns=[r"stop (?:the )?browser", r"close browser", r"quit browser"],
            handler="browser_stop",
            description="Stop the browser session",
            category="browser",
            examples=["Stop the browser", "Close browser"],
        ))

        self.register(CommandPattern(
            patterns=[r"open (.+) browser", r"launch (.+) browser", r"open browser (.+)"],
            handler="open_app",
            description="Open a browser by name",
            category="desktop",
            examples=["Open Brave browser", "Launch Chrome browser"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:open|show|go to) (?:the )?(?:my )?(desktop|documents|downloads|pictures|music|videos|onedrive)(?: folder)?", r"(?:open|show) folder (desktop|documents|downloads|pictures|music|videos|onedrive)"],
            handler="open_file_explorer",
            description="Open a common folder",
            category="desktop",
            examples=["Open my documents", "Open downloads folder", "Show my onedrive"],
        ))

        self.register(CommandPattern(
            patterns=[r"open (.+)", r"launch (.+)", r"start (.+)"],
            handler="open_app",
            description="Open any application",
            category="desktop",
            examples=["Open Chrome", "Launch Spotify", "Start Notepad"],
        ))

        self.register(CommandPattern(
            patterns=[r"open browser", r"open (?:google )?chrome", r"open (?:mozilla )?firefox", r"open edge", r"open firefox"],
            handler="open_browser",
            description="Open web browser",
            category="desktop",
            examples=["Open browser", "Open Chrome", "Open Firefox"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:go to|open|search) (?:youtube\.com|youtube) (.+)", r"youtube (.+)", r"watch (.+) on youtube"],
            handler="open_youtube",
            description="Search YouTube",
            category="desktop",
            examples=["YouTube lofi hip hop", "Watch cooking tutorials on YouTube"],
        ))

        self.register(CommandPattern(
            patterns=[r"play (.+) on (?:youtube|yt)", r"play on youtube", r"play youtube (.+)"],
            handler="play_youtube",
            description="Play music on YouTube",
            category="desktop",
            examples=["Play jazz on YouTube", "Play YouTube music"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:open|show) (?:file )?(?:explorer|manager|files)", r"(?:open|go to) (?:my )?(desktop|documents|downloads|pictures|music|videos|home)", r"(?:open|show) folder (.+)"],
            handler="open_file_explorer",
            description="Open file explorer",
            category="desktop",
            examples=["Open file explorer", "Open my documents", "Open downloads folder"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:open|show) (?:a )?(?:terminal|cmd|command prompt|powershell)", r"(?:open|show) terminal at (.+)"],
            handler="open_terminal",
            description="Open terminal",
            category="desktop",
            examples=["Open terminal", "Open a command prompt"],
        ))

        self.register(CommandPattern(
            patterns=[r"opencode (.+)", r"use opencode to (.+)", r"run opencode (.+)", r"ask opencode to (.+)"],
            handler="open_opencode",
            description="Run an opencode command",
            category="desktop",
            examples=["Opencode fix the bug in main.py", "Use opencode to add tests"],
        ))

        self.register(CommandPattern(
            patterns=[r"close (.+)", r"kill (.+)"],
            handler="close_app",
            description="Close an application",
            category="desktop",
            examples=["Close Chrome", "Kill Notepad"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:take|capture) (?:a )?(?:screenshot|screen(?:shot)?|screen capture)"],
            handler="screenshot",
            description="Take a screenshot",
            category="desktop",
            examples=["Take a screenshot", "Capture screen"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:show|list|what(?:'s| is) running)(?: ?process(?:es)?)?", r"(?:show|list) task(?:s| ?manager)"],
            handler="list_processes",
            description="List running processes",
            category="desktop",
            examples=["Show processes", "What's running?", "List tasks"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:show|what(?:'s| is))(?: my)? (?:system|pc|computer) (?:info|specs|specifications)"],
            handler="get_system_info",
            description="Get system information",
            category="desktop",
            examples=["Show system info", "What are my PC specs?"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:show|what(?:'s| is))(?: my)? disk (?:usage|space|storage)"],
            handler="get_disk_usage",
            description="Check disk usage",
            category="desktop",
            examples=["Show disk usage", "What's my disk space?"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:set |change )?(?:volume|sound) to (\d+)", r"volume (\d+)", r"(?:set |change )?volume to (\d+)%"],
            handler="set_volume",
            description="Set system volume",
            category="media",
            examples=["Set volume to 50", "Volume 75", "Change volume to 30%"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:toggle |)mute(?:d)?", r"unmute", r"volume (?:up|down)"],
            handler="mute",
            description="Toggle mute",
            category="media",
            examples=["Mute", "Unmute", "Toggle mute"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:next|skip)(?: ?track| ?song)?", r"next song", r"skip this"],
            handler="next_track",
            description="Next track",
            category="media",
            examples=["Next track", "Skip song", "Next"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:previous|last|back)(?: ?track| ?song)?", r"previous song", r"go back"],
            handler="previous_track",
            description="Previous track",
            category="media",
            examples=["Previous track", "Last song", "Go back"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:play|pause|toggle play)(?:\/pause)?", r"(?:resume|unpause)"],
            handler="play_pause",
            description="Toggle play/pause",
            category="media",
            examples=["Play", "Pause", "Toggle play"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:shut down|shutdown|turn off)(?: the pc| the computer)?(?: in (\d+) (?:seconds?|minutes?))?"],
            handler="shutdown",
            description="Shut down the PC",
            category="desktop",
            examples=["Shut down", "Shutdown in 60 seconds", "Turn off the computer"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:restart|reboot)(?: the (?:pc|computer))?"],
            handler="restart",
            description="Restart the PC",
            category="desktop",
            examples=["Restart", "Reboot the PC"],
        ))

        self.register(CommandPattern(
            patterns=[r"lock(?: the (?:pc|computer|screen))?"],
            handler="lock_pc",
            description="Lock the PC",
            category="desktop",
            examples=["Lock", "Lock the screen"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:sleep|suspend)(?: the (?:pc|computer))?"],
            handler="sleep_pc",
            description="Put PC to sleep",
            category="desktop",
            examples=["Sleep", "Put PC to sleep"],
        ))

        self.register(CommandPattern(
            patterns=[r"run (?:the )?command (.+)", r"execute (.+)", r"shell (.+)"],
            handler="run_command",
            description="Run a shell command",
            category="desktop",
            examples=["Run command dir", "Execute ipconfig", "Shell whoami"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:search|find)(?: for)? (?:files? )?(?:named?|called?|matching) (.+)"],
            handler="search_files",
            description="Search for files",
            category="desktop",
            examples=["Search files named report", "Find documents matching budget"],
        ))

        self.register(CommandPattern(
            patterns=[r"open (?:the )?(?:url|website|page) (.+)"],
            handler="open_browser",
            description="Open a URL in browser",
            category="desktop",
            examples=["Open the url github.com", "Open website stackoverflow.com"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:list|show|what(?:'s| is) (?:in|here))(?: the )?(?:current )?(?:folder|directory|dir)?", r"where am i", r"(?:what(?:'s| is))?(?: my )?current (?:folder|directory|location|path)"],
            handler="list_dir",
            description="List current directory",
            category="navigation",
            examples=["List folder", "What's in this directory?", "Where am I?"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:go|navigate|open) to (.+)", r"(?:go|navigate) into (.+)", r"(?:open|show) folder (.+)", r"(?:list|show) (.+) folder"],
            handler="navigate_to",
            description="Navigate into a folder",
            category="navigation",
            examples=["Go to Documents", "Navigate into Projects", "Open folder Downloads"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:go back|back|up|parent|previous folder)"],
            handler="go_back",
            description="Go to parent directory",
            category="navigation",
            examples=["Go back", "Back", "Up one level"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:go )?home", r"my files", r"(?:go to )?home folder"],
            handler="go_home",
            description="Go to home directory",
            category="navigation",
            examples=["Home", "Go home", "My files"],
        ))

        self.register(CommandPattern(
            patterns=[r"read (?:the )?file (.+)", r"open file (.+)", r"show (?:the )?(?:content of )?(.+)"],
            handler="read_file",
            description="Read a text file",
            category="navigation",
            examples=["Read file notes.txt", "Open file main.py", "Show report.csv"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:where|what(?:'s| is)) (?:am i|current location|current directory)"],
            handler="get_current_location",
            description="Show current directory path",
            category="navigation",
            examples=["Where am I?", "What's my current location?"],
        ))

        self.register(CommandPattern(
            patterns=[r"(?:what|show)(?: ?)(?:folders?|directories?|files?)(?: ?)(?:are|is|do)(?: ?)(?:here|i have|on my pc|available)", r"(?:show|what)(?:'s| is)(?: ?)(?:in )?(?:my )?(?:pc|computer|system)", r"folder (?:map|list|structure)", r"(?:show|what) folders?"],
            handler="get_folder_map",
            description="Show all folders on the PC",
            category="navigation",
            examples=["What folders do I have?", "Show my folders", "Folder map"],
        ))

        self.register(CommandPattern(
            patterns=[r"scan (.+)", r"deep scan (.+)", r"what(?:'s| is) (?:in|inside) (.+)(?: ?)(?:folder|directory)?", r"show (?:me )?(?:what(?:'s| is) )?in (.+)"],
            handler="deep_scan",
            description="Deep scan a specific folder to see all files and subfolders",
            category="navigation",
            examples=["Scan my projects folder", "What's in Documents?", "Show me what's in Downloads"],
        ))

        self.register(CommandPattern(
            patterns=[r"remember (.+)", r"don't forget (.+)", r"keep in mind (.+)", r"make a note (.+)"],
            handler="remember",
            description="Remember something for future conversations",
            category="memory",
            examples=["Remember my WiFi password is 1234", "Don't forget I have a meeting at 3pm"],
        ))

        self.register(CommandPattern(
            patterns=[r"what do you remember", r"what have you remembered", r"recall (.+)", r"what do you know about (.+)", r"do you remember (.+)"],
            handler="recall",
            description="Recall something from memory",
            category="memory",
            examples=["What do you remember?", "Do you remember my WiFi password?"],
        ))

        self.register(CommandPattern(
            patterns=[r"forget (.+)", r"clear memory", r"reset memory"],
            handler="forget",
            description="Forget something from memory",
            category="memory",
            examples=["Forget my WiFi password", "Clear memory"],
        ))

        self.register(CommandPattern(
            patterns=[r"what do you know(?: about)? (.+)", r"tell me about (.+)", r"what have you learned about (.+)"],
            handler="knowledge_search",
            description="Search what the AI knows about a topic",
            category="memory",
            examples=["What do you know about me?", "Tell me about my projects"],
        ))

        self.register(CommandPattern(
            patterns=[r"what do you know", r"what have you learned", r"knowledge summary", r"show your knowledge"],
            handler="knowledge_summary",
            description="Show a summary of everything the AI has learned",
            category="memory",
            examples=["What do you know?", "Show your knowledge"],
        ))

    def register(self, command: CommandPattern):
        for pattern in command.patterns:
            self.commands[pattern] = command

    def register_handler(self, handler_name: str, handler: Callable):
        self.handlers[handler_name] = handler

    def match_command(self, text: str) -> Optional[tuple[CommandPattern, dict]]:
        text = text.lower().strip()

        for pattern, command in self.commands.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (command, {"groups": match.groups(), "text": text})

        return None

    def parse_command(self, text: str) -> dict:
        text = text.strip()
        cleaned = re.sub(
            r"^(?:can you|could you|would you|please|hey|ok |alright |yeah |yep |yo |jarvis[,.]?\s*|computer[,.]?\s*|assistant[,.]?\s*)\s*",
            "", text, flags=re.IGNORECASE
        ).strip()
        cleaned = re.sub(r"\s*(?:please|sir|madam|boss|thanks|thank you)\s*$", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^(?:i (?:want to|would like to|need to|wanna|gonna))\s*", "", cleaned, flags=re.IGNORECASE).strip()

        for pattern, command in self.commands.items():
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                return {
                    "matched": True,
                    "handler": command.handler,
                    "category": command.category,
                    "description": command.description,
                    "params": match.groups(),
                    "text": cleaned,
                }

        for pattern, command in self.commands.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "matched": True,
                    "handler": command.handler,
                    "category": command.category,
                    "description": command.description,
                    "params": match.groups(),
                    "text": text,
                }

        return {"matched": False, "text": text}

    async def execute_command(self, text: str, context: dict = None) -> dict:
        parsed = self.parse_command(text)

        if not parsed["matched"]:
            return {
                "status": "not_recognized",
                "text": text,
                "message": "I didn't understand that command. Try asking me something else.",
            }

        handler_name = parsed["handler"]
        handler = self.handlers.get(handler_name)

        if not handler:
            return {
                "status": "handler_not_found",
                "command": parsed,
                "message": f"Handler not registered for: {handler_name}",
            }

        try:
            if context:
                result = await handler(*parsed["params"], **context)
            else:
                result = await handler(*parsed["params"])

            return {
                "status": "success",
                "command": parsed,
                "result": result,
            }
        except Exception as e:
            return {
                "status": "error",
                "command": parsed,
                "message": str(e),
            }

    def get_commands_by_category(self, category: str) -> list[dict]:
        seen_handlers = set()
        commands = []
        for pattern, cmd in self.commands.items():
            if cmd.category == category and cmd.handler not in seen_handlers:
                seen_handlers.add(cmd.handler)
                commands.append({
                    "handler": cmd.handler,
                    "description": cmd.description,
                    "category": cmd.category,
                    "examples": cmd.examples,
                })
        return commands

    def get_all_commands(self) -> list[dict]:
        seen_handlers = set()
        commands = []
        for pattern, cmd in self.commands.items():
            if cmd.handler not in seen_handlers:
                seen_handlers.add(cmd.handler)
                commands.append({
                    "handler": cmd.handler,
                    "description": cmd.description,
                    "category": cmd.category,
                    "examples": cmd.examples,
                })
        return commands

    def get_categories(self) -> list[str]:
        return list(set(cmd.category for cmd in self.commands.values()))

    async def llm_parse_command(self, text: str) -> Optional[dict]:
        import ollama
        from app.services.system_command_service import system_command_service

        handlers = {}
        seen = set()
        for cmd in self.commands.values():
            if cmd.handler not in seen:
                seen.add(cmd.handler)
                handlers[cmd.handler] = {
                    "description": cmd.description,
                    "category": cmd.category,
                    "examples": cmd.examples,
                }

        try:
            folder_info = await system_command_service.get_folder_map()
            current_dir = folder_info.get("current_dir", "")
            home = folder_info.get("home", "")
            top_level = folder_info.get("top_level", [])
            folder_context = f"User's home: {home}\nCurrent directory: {current_dir}\nTop-level folders: {', '.join(top_level)}"
        except:
            folder_context = ""

        prompt = f"""You are a command parser. Given user input, determine which command to execute.

Available commands:
{json.dumps(handlers, indent=2)}

User's PC folders:
{folder_context}

User said: "{text}"

Return ONLY a JSON object:
- "handler": handler name (must match one from the list exactly)
- "params": extracted parameters as a list of strings

RULES:
- For "open_app": params should be just the app name, no filler words. E.g. "open brave browser" -> ["brave"], "launch spotify app" -> ["spotify"]
- For "open_file_explorer": params should be the folder name that matches what the user has. E.g. "open my onedrive" -> ["onedrive"]
- For "navigate_to": params should be an actual folder the user has from the folder list above
- For "play_youtube"/"open_youtube": params should be the search query
- For "browser_search": params should be the search query
- For "browser_navigate": params should be the URL or website name
- For "browser_click": params should be the element description
- For "browser_type": params should be [text, field_description]
- For "browser_scroll": params should be ["up"] or ["down"]
- Remove filler words like "please", "the", "my", "a", "app", "browser", "folder" from app names
- If the user mentions a folder that exists on their PC, use navigate_to or open_file_explorer accordingly
- If no command matches, return: {{"handler": null, "params": []}}

Examples:
- "open brave browser" -> {{"handler": "open_app", "params": ["brave"]}}
- "launch spotify" -> {{"handler": "open_app", "params": ["spotify"]}}
- "open my onedrive" -> {{"handler": "open_file_explorer", "params": ["onedrive"]}}
- "go to my downloads folder" -> {{"handler": "navigate_to", "params": ["downloads"]}}
- "show me what's in the documents folder" -> {{"handler": "navigate_to", "params": ["documents"]}}
- "what's in this folder" -> {{"handler": "list_dir", "params": []}}
- "play some jazz on youtube" -> {{"handler": "play_youtube", "params": ["jazz"]}}
- "go back" -> {{"handler": "go_back", "params": []}}
- "read the config file" -> {{"handler": "read_file", "params": ["config"]}}
- "open the file explorer to my pictures" -> {{"handler": "open_file_explorer", "params": ["pictures"]}}
- "where am i" -> {{"handler": "get_current_location", "params": []}}
- "mute the pc" -> {{"handler": "mute", "params": []}}
- "take a screenshot" -> {{"handler": "screenshot", "params": []}}
- "shut down the computer" -> {{"handler": "shutdown", "params": []}}
- "restart my pc" -> {{"handler": "restart", "params": []}}
- "lock my screen" -> {{"handler": "lock_pc", "params": []}}
- "what folders do i have" -> {{"handler": "get_folder_map", "params": []}}
- "scan my projects folder" -> {{"handler": "deep_scan", "params": ["projects"]}}
- "what's in documents" -> {{"handler": "deep_scan", "params": ["documents"]}}
- "show me what's in downloads" -> {{"handler": "deep_scan", "params": ["downloads"]}}
- "remember my wifi password is 1234" -> {{"handler": "remember", "params": ["my wifi password is 1234"]}}
- "don't forget i have a meeting at 3pm" -> {{"handler": "remember", "params": ["i have a meeting at 3pm"]}}
- "what do you remember" -> {{"handler": "recall", "params": [""]}}
- "do you remember my wifi password" -> {{"handler": "recall", "params": ["wifi password"]}}
- "recall what i told you about projects" -> {{"handler": "recall", "params": ["projects"]}}
- "forget my wifi password" -> {{"handler": "forget", "params": ["wifi password"]}}
- "clear memory" -> {{"handler": "forget", "params": ["clear memory"]}}
- "what do you know about me" -> {{"handler": "knowledge_search", "params": ["me"]}}
- "what have you learned" -> {{"handler": "knowledge_summary", "params": []}}
- "tell me about my preferences" -> {{"handler": "knowledge_search", "params": ["preferences"]}}
- "search for flutter docs" -> {{"handler": "browser_search", "params": ["flutter docs"]}}
- "google weather today" -> {{"handler": "browser_search", "params": ["weather today"]}}
- "open github.com" -> {{"handler": "browser_navigate", "params": ["github.com"]}}
- "go to youtube.com" -> {{"handler": "browser_navigate", "params": ["youtube.com"]}}
- "click the search button" -> {{"handler": "browser_click", "params": ["search button"]}}
- "type hello in the search box" -> {{"handler": "browser_type", "params": ["hello", "search box"]}}
- "take a screenshot" -> {{"handler": "browser_screenshot", "params": []}}
- "scroll down" -> {{"handler": "browser_scroll", "params": ["down"]}}
- "what's on the page" -> {{"handler": "browser_snapshot", "params": []}}
- "start a browser" -> {{"handler": "browser_start", "params": []}}
- "stop the browser" -> {{"handler": "browser_stop", "params": []}}

Return ONLY valid JSON, no explanation."""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": 150},
            )
            content = response["message"]["content"].strip()
            content = re.sub(r'```json\n?|\n?```', '', content).strip()
            result = json.loads(content)
            if result.get("handler"):
                return result
        except Exception as e:
            print(f"[LLM PARSE ERROR] {e}")
        return None


command_registry = CommandRegistry()
