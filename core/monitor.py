#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3RMUXK1NG WiFi Cracker PRO - Real-time Monitor Module"""

import time
import threading
from typing import Callable, Dict, List

class RealtimeMonitor:
    def __init__(self, interface: str):
        self.interface = interface
        self.running = False
        self.callbacks: List[Callable] = []
        self.stats = {'packets': 0, 'networks': 0}
    
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def _monitor_loop(self):
        while self.running:
            time.sleep(1)
            for callback in self.callbacks:
                try:
                    callback(self.stats)
                except:
                    pass
    
    def stop(self):
        self.running = False
    
    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)
