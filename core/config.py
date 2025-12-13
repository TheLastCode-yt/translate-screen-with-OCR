import json
import os
import datetime

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "api_keys": {
        "deepl": "",
        "google": ""
    },
    "source_language": "en",
    "target_language": "pt",
    "default_capture_mode": "global",  # or "crop"
    "default_provider": "mymemory",  # "deepl", "google", "mymemory"
    "bubble_style": {
        "background_color": "#2d2d2d",
        "text_color": "#ffffff",
        "font_size": 12
    }
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
        self.history = [] # In-memory history

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        # Don't save history to file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_api_key(self, provider):
        return self.config["api_keys"].get(provider, "")

    def set_api_key(self, provider, key):
        self.config["api_keys"][provider] = key
        self.save_config()

    def log_history(self, original, translated, image_data=None):
        # image_data is expected to be a PIL Image object or similar
        entry = {
            "original": original,
            "translated": translated,
            "image_data": image_data,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.append(entry)
        
        # Automated Image Cleanup: Keep images only for the 3 most recent logs
        # The list is appended to, so the last elements are the most recent.
        # If we have more than 3 entries, we need to clear image_data from the older ones.
        if len(self.history) > 3:
            # The index of the entry that just fell out of the "top 3" window
            # is len(self.history) - 4.
            # Actually, we can just iterate through all except the last 3 and ensure image_data is None.
            for i in range(len(self.history) - 3):
                self.history[i]["image_data"] = None

    def clear_history(self):
        self.history = []

    def get_history(self):
        return self.history
