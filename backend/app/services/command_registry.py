import re
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
        result = self.match_command(text)
        if not result:
            return {"matched": False, "text": text}

        command, match_data = result
        return {
            "matched": True,
            "handler": command.handler,
            "category": command.category,
            "description": command.description,
            "params": match_data["groups"],
            "text": match_data["text"],
        }

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


command_registry = CommandRegistry()
