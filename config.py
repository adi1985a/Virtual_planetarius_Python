import json
import os

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        self.DEFAULT_CONFIG = {
            'colors': {
                'background': (0, 0, 30),
                'text': (255, 223, 0),  # Gold
                'highlight': (100, 149, 237),  # Cornflower Blue
                'star': (255, 255, 255)
            },
            'window': {
                'width': 800,
                'height': 600,
                'title': 'Virtual Planetarium - by Adrian Lesniak'
            },
            'font': {
                'size': 16,
                'name': 'Arial'
            }
        }
        
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = self.DEFAULT_CONFIG
            self.save_config()
    
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
