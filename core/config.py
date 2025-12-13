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
    "history": []
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save_config(self):
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

    def log_history(self, original, translated, image_path=None):
        if "history" not in self.config:
            self.config["history"] = []
            
        entry = {
            "original": original,
            "translated": translated,
            "image_path": image_path,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.config["history"].append(entry)
        
        # Automated Image Cleanup: Keep images only for the 3 most recent logs
        history = self.config["history"]
        if len(history) > 3:
            # Entries to clean (all except last 3)
            # We don't delete the entry, just the image file
            for i in range(len(history) - 3):
                entry_to_clean = history[i]
                img_path = entry_to_clean.get("image_path")
                if img_path and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except Exception as e:
                        print(f"Error deleting image {img_path}: {e}")
                # Remove path from entry to indicate it's gone
                entry_to_clean["image_path"] = None

        self.save_config()

    def clear_history(self):
        if "history" in self.config:
            for entry in self.config["history"]:
                img_path = entry.get("image_path")
                if img_path and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except Exception as e:
                        print(f"Error deleting image {img_path}: {e}")
            self.config["history"] = []
            self.save_config()

    def get_history(self):
        return self.config.get("history", [])
