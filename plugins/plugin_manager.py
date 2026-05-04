#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3RMUXK1NG WiFi Cracker PRO - Plugin Manager"""

import os
import importlib
from pathlib import Path
from typing import Dict, List

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, dict] = {}
        self.plugin_dir = Path(__file__).parent.parent / 'plugins'
    
    def load_all(self):
        if not self.plugin_dir.exists():
            return
        
        for f in self.plugin_dir.glob('*.py'):
            if f.name.startswith('_'):
                continue
            try:
                spec = importlib.util.spec_from_file_location(f.stem, f)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'register'):
                    plugin = module.register()
                    self.plugins[plugin['name']] = plugin
            except:
                pass
    
    def list_plugins(self) -> List[dict]:
        return list(self.plugins.values())
    
    def get_plugin(self, name: str):
        return self.plugins.get(name)
    
    def execute(self, name: str, *args, **kwargs):
        plugin = self.plugins.get(name)
        if plugin and 'execute' in plugin:
            return plugin['execute'](*args, **kwargs)
        return None
