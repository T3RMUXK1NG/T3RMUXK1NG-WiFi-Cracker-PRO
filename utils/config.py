#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3RMUXK1NG WiFi Cracker PRO - Configuration Utility"""

import os
import json
from pathlib import Path

class Config:
    DEFAULTS = {
        'interface': 'wlan0',
        'scan_duration': 30,
        'capture_duration': 120,
        'deauth_count': 10,
        'wordlist': '/usr/share/wordlists/rockyou.txt',
        'output_dir': '/tmp/t3rmuxk1ng_wifi_output',
        'log_level': 'INFO',
        'auto_save': True,
        'colors': True,
        'timeout': 300,
    }
    
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 't3rmuxk1ng-wifi-pro'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.DEFAULTS.copy()
        self.load()
    
    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config.update(json.load(f))
            except:
                pass
    
    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save()
