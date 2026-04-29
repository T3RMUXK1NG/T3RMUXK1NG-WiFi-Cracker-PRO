#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Logger"""
import os
import sys
import logging
from datetime import datetime


class Logger:
    """Advanced logging system"""
    
    # ANSI Color codes
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'RESET': '\033[0m',
    }
    
    def __init__(self, name: str = "RS-WiFi-Pro", log_dir: str = "/var/log/rs-wifi-pro"):
        self.name = name
        self.log_dir = log_dir
        self.use_colors = sys.stdout.isatty()
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Log file
        self.log_file = os.path.join(log_dir, f"rs_wifi_pro_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Setup Python logging
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('%(message)s'))
        
        if not self.logger.handlers:
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text"""
        if self.use_colors and color in self.COLORS:
            return f"{self.COLORS[color]}{text}{self.COLORS['RESET']}"
        return text
    
    def _timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime('%H:%M:%S')
    
    def info(self, msg: str):
        """Log info message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[INFO]', 'GREEN')} ✓ {msg}")
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Log warning message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[WARN]', 'YELLOW')} ⚠ {msg}")
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """Log error message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[ERROR]', 'RED')} ✗ {msg}")
        self.logger.error(msg)
    
    def debug(self, msg: str):
        """Log debug message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[DEBUG]', 'DIM')} {msg}")
        self.logger.debug(msg)
    
    def success(self, msg: str):
        """Log success message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[SUCCESS]', 'GREEN')} ★ {msg}")
        self.logger.info(f"SUCCESS: {msg}")
    
    def progress(self, msg: str):
        """Log progress message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[PROGRESS]', 'CYAN')} ◆ {msg}")
        self.logger.info(f"PROGRESS: {msg}")
    
    def critical(self, msg: str):
        """Log critical message"""
        ts = self._timestamp()
        print(f"{ts} {self._colorize('[CRITICAL]', 'RED')} !!! {msg}")
        self.logger.critical(msg)
    
    def hex_dump(self, data: bytes, prefix: str = ""):
        """Print hex dump"""
        for i in range(0, len(data), 16):
            hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
            print(f"{prefix}{i:04x}: {hex_part:<48} {ascii_part}")
    
    def table(self, headers: list, rows: list):
        """Print formatted table"""
        # Calculate column widths
        widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        
        # Print header
        header_str = ' | '.join(str(h).ljust(w) for h, w in zip(headers, widths))
        print(self._colorize(header_str, 'CYAN'))
        print('-' * len(header_str))
        
        # Print rows
        for row in rows:
            print(' | '.join(str(c).ljust(w) for c, w in zip(row, widths)))
