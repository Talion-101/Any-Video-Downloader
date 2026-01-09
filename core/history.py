import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, filepath="history.json"):
        self.filepath = filepath
        self.history = self._load_history()

    def _load_history(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_history(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, data):
        """
        Adds a new entry to history.
        data expected keys: title, url, format_label, status, date, output_path
        """
        entry = {
            'id': str(int(datetime.now().timestamp())), # Simple ID
            'title': data.get('title', 'Unknown'),
            'url': data.get('url', ''),
            'format_label': data.get('format_label', ''),
            'status': data.get('status', 'Finished'), # Finished, Cancelled, Paused, Error
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'output_path': data.get('output_path', ''),
            'thumbnail': data.get('thumbnail', '')
        }
        # Prepend to list (newest first)
        self.history.insert(0, entry)
        self.save_history()
        return entry

    def update_status(self, entry_id, new_status):
        for entry in self.history:
            if entry['id'] == entry_id:
                entry['status'] = new_status
                self.save_history()
                return True
        return False

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
        self.save_history()
