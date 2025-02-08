import gradio as gr
from typing import List, Dict, Set
import re

class CommandMatcher:
    def __init__(self):
        # Previous filter words remain the same
        self.filter_words = {
            'hey', 'hi', 'hello', 'please', 'could', 'can', 'would', 'will',
            'you', 'friend', 'kindly', 'there', 'now', 'just', 'want', 'to',
            'need', 'like', 'try', 'let', 'us', 'do', 'the', 'um', 'uh'
        }
        
        # Previous commands dictionary with updated WAYPOINT patterns
        self.commands = {
            'ARM': {
                'keywords': {'start', 'arm', 'begin', 'activate', 'power', 'initialize', 'ready', 'motor', 'motors', 'drone'},
                'key_phrases': {'start motor', 'start motors', 'arm drone', 'begin flight'},
                'command': 'arm throttle'
            },
            'MODE_AUTO': {
                'keywords': {'mission', 'auto', 'autonomous', 'execute', 'run', 'start', 'perform', 'begin'},
                'key_phrases': {'start mission', 'begin mission', 'run mission', 'auto mode', 'perform mission', 'your mission'},
                'command': 'mode auto'
            },
            'MODE_GUIDED': {
                'keywords': {'guided', 'manual', 'control', 'take'},
                'key_phrases': {'guided mode', 'manual control', 'take control'},
                'command': 'mode guided'
            },
            'MODE_RTL': {
                'keywords': {'return', 'home', 'back', 'rtl', 'base'},
                'key_phrases': {'return home', 'come back', 'go home', 'rtl', 'bring back', 'bring it back', 'bring it home'},
                'command': 'mode rtl'
            },
            'MODE_LOITER': {
                'keywords': {'hover', 'stay', 'hold', 'maintain', 'position', 'loiter', 'wait'},
                'key_phrases': {'hover here', 'stay here', 'hold position', 'maintain position'},
                'command': 'mode loiter'
            },
            'TAKEOFF': {
                'keywords': {'takeoff', 'take', 'off', 'lift', 'launch', 'fly', 'meters', 'meter', 'm'},
                'key_phrases': {'take off', 'lift off', 'launch'},
                'command': lambda height='10': f"mode guided; takeoff {height}"
            },
            'LAND': {
                'keywords': {'land', 'down', 'ground', 'descend'},
                'key_phrases': {'land here', 'touch down', 'land now', 'bring down', 'land'},
                'command': 'mode land'
            },
            'DISARM': {
                'keywords': {'stop', 'off', 'kill', 'disarm', 'shutdown', 'end', 'finish'},
                'key_phrases': {'stop motors', 'turn off', 'kill motors', 'disarm drone'},
                'command': 'disarm'
            },
            'WAYPOINT': {
                'keywords': {'go', 'move', 'fly', 'navigate', 'waypoint', 'wp', 'point', 'location', 'position', 'to'},
                'key_phrases': {'go to', 'move to', 'fly to', 'navigate to', 'waypoint', 'set waypoint', 'wp'},
                'command': lambda wp=None, lat=None, lon=None, alt=None: (
                    f"wp seq {wp}" if wp else 
                    f"mode guided; wp {lat} {lon} {alt if alt else '10'}"
                )
            }
        }

    def extract_waypoint_number(self, text: str) -> str:
        """Extract waypoint number from text"""
        patterns = [
            r'waypoint\s*(\d+)',  # matches "waypoint 1"
            r'wp\s*(\d+)',        # matches "wp 1"
            r'point\s*(\d+)',     # matches "point 1"
            r'#(\d+)',            # matches "#1"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        return None

    def extract_coordinates(self, text: str) -> tuple:
        """Extract latitude, longitude, and optional altitude from text"""
        # Pattern for numbers (including negative integers)
        num = r'-?\d+\.?\d*'
        
        patterns = [
            # Basic number pair (e.g., "18, 99" or "18,99")
            rf'(?:to\s+)?({num})\s*,\s*({num})',
            
            # More complex formats
            rf'({num})\s*,\s*({num})(?:\s*,\s*({num}))?',
            rf'(?:lat(?:itude)?)\s*({num}).*?(?:lon(?:gitude)?)\s*({num})(?:.*?(?:alt(?:itude)?|height)\s*({num}))?',
            rf'({num})\s+({num})(?:\s+({num}))?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                # If we have a 2-group match, add None for altitude
                if len(groups) == 2:
                    return groups[0], groups[1], None
                return groups[0], groups[1], groups[2]
        
        return None, None, None

    def clean_text(self, text: str) -> str:
        """Clean and normalize input text"""
        text = text.lower()
        
        # Replace special sequence indicators
        text = re.sub(r'once (?:you are|you\'re|it is|it\'s) done', 'then', text)
        text = re.sub(r'when (?:you are|you\'re|it is|it\'s) done', 'then', text)
        text = re.sub(r'after (?:you are|you\'re|it is|it\'s) done', 'then', text)
        
        words = text.split()
        while words and words[0] in self.filter_words:
            words.pop(0)
        
        text = ' '.join(words)
        # Keep commas, periods, and negative signs for coordinates
        text = re.sub(r'[^\w\s,.-]', '', text)
        return text

    def split_into_commands(self, text: str) -> List[str]:
        """Split text into individual command segments"""
        # Split on common separators while preserving coordinate pairs
        text = re.sub(r'(?<=\d)\s+and\s+(?=\d)', ',', text)  # Convert "and" between numbers to comma
        separators = r'\sand\s|\sthen\s|\safter\s|\snext\s|\sfinally\s|\slastly\s|\s*,\s*(?!(?:\d|$))'
        segments = re.split(separators, text)
        return [seg.strip() for seg in segments if seg.strip()]

    def find_best_command_match(self, text: str) -> str:
        """Find the best matching command based on keywords and phrases"""
        text = text.lower()
        words = set(text.split())
        best_match = None
        max_score = 0

        for cmd_name, cmd_info in self.commands.items():
            keyword_matches = len(words & cmd_info['keywords'])
            phrase_matches = sum(1 for phrase in cmd_info['key_phrases'] if phrase in text)
            
            # Special case for coordinates - check if there's a number pair
            if cmd_name == 'WAYPOINT' and re.search(r'\d+\s*,\s*\d+', text):
                keyword_matches += 2
            
            score = keyword_matches + (phrase_matches * 3)
            
            if score > max_score:
                max_score = score
                best_match = cmd_name
                
        return best_match if max_score > 0 else None

    def process_command(self, text: str) -> str:
        """Process input text and return corresponding commands"""
        if not text:
            return "Please enter a command"
            
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return "Please enter a valid command"
            
        command_segments = self.split_into_commands(cleaned_text)
        
        results = []
        for segment in command_segments:
            cmd_type = self.find_best_command_match(segment)
            if cmd_type:
                cmd_info = self.commands[cmd_type]
                if cmd_type == 'WAYPOINT':
                    wp_num = self.extract_waypoint_number(segment)
                    if wp_num:
                        results.append(cmd_info['command'](wp=wp_num))
                    else:
                        lat, lon, alt = self.extract_coordinates(segment)
                        if lat and lon:
                            results.append(cmd_info['command'](wp=None, lat=lat, lon=lon, alt=alt))
                elif callable(cmd_info['command']):
                    if cmd_type == 'TAKEOFF':
                        height = self.extract_number(segment)
                        results.append(cmd_info['command'](height))
                else:
                    results.append(cmd_info['command'])
        
        return "; ".join(results) if results else "No commands recognized. Please try again."

    def extract_number(self, text: str) -> str:
        """Extract the first number from text"""
        numbers = re.findall(r'\d+', text)
        return numbers[0] if numbers else '10'

# Initialize the command matcher
matcher = CommandMatcher()

# Updated examples list with simple coordinate examples
examples=[
        # Starting Motors Examples
        ["start motors"],
        ["arm motors"],
        ["power up motors"],
        ["activate motors"],
        ["turn on motors"],
        ["initialize drone"],
        ["motors on"],
        ["arm system"],
        ["enable motors"],
        ["start engines"],
        
        # Mission Examples
        ["start mission"],
        ["begin mission"],
        ["run mission"],
        ["perform mission"],
        ["execute mission"],
        ["start auto"],
        ["mission start"],
        ["auto mode"],
        ["do mission"],
        ["fly mission"],
        
        # Return Home Examples
        ["return home"],
        ["come back"],
        ["rtl"],
        ["go home"],
        ["head home"],
        ["return base"],
        ["come home"],
        ["fly home"],
        ["back home"],
        ["bring it home"],
        
        # Landing Examples
        ["land"],
        ["land here"],
        ["touch down"],
        ["bring down"],
        ["descend"],
        ["set down"],
        ["ground"],
        ["make landing"],
        ["start landing"],
        ["come down"],
        
        # Hovering Examples
        ["hover"],
        ["hold position"],
        ["stay here"],
        ["maintain position"],
        ["loiter"],
        ["stay put"],
        ["keep position"],
        ["hold here"],
        ["hover in place"],
        ["keep steady"],
        
        # Taking Off Examples
        ["take off"],
        ["takeoff"],
        ["lift off"],
        ["launch"],
        ["take off 10m"],
        ["launch 20 meters"],
        ["ascend"],
        ["rise up"],
        ["climb"],
        ["start ascent"],
        
        # Stopping Motors Examples
        ["stop motors"],
        ["disarm"],
        ["motors off"],
        ["kill motors"],
        ["power down"],
        ["end flight"],
        ["shut down"],
        ["turn off"],
        ["stop engines"],
        ["disable motors"],
        
        # Simple Combinations
        ["start motors then takeoff"],
        ["take off and start mission"],
        ["mission then home"],
        ["land and stop motors"],
        ["start motors takeoff land"],
        ["motors on then mission"],
        ["return then land"],
        ["hover then home"],
        ["mission home land"],
        ["start up and fly"]
    ]

demo = gr.Interface(
    fn=matcher.process_command,
    inputs=gr.Textbox(
        label="Enter command",
        placeholder="e.g., start motors, go to 18 99 5, then land",
        lines=5,
        max_lines=10
    ),
    outputs=gr.Textbox(
        label="Mission Planner Commands",
        lines=3
    ),
    title="Mission Planner Command Generator",
    description="Enter commands naturally. Use simple coordinates (e.g., 'go to 18 99 5') or waypoint numbers. Separate multiple commands with 'and', 'then', or commas.",
    examples=examples
)

if __name__ == "__main__":
    print("Starting Mission Planner Command Generator...")
    print("Once running, open your browser to: http://localhost:7860")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )