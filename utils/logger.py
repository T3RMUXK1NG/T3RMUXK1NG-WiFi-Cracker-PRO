#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Logger Utility"""

import os
import logging
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, log_dir: str = "/tmp/rs_wifi_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._setup_logging()
    
    def _setup_logging(self):
        self.logger = logging.getLogger('RS-WiFi-PRO')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    
    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)
    def success(self, msg): self.logger.info(f"SUCCESS: {msg}")
    def debug(self, msg): self.logger.debug(msg)
