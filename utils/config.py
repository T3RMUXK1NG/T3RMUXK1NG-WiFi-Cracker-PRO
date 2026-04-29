#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Configuration"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration"""
    
    # Application info
    app_name: str = "RS WiFi Cracker PRO"
    version: str = "4.0.1"
    author: str = "T3rmuxk1ng"
    release_type: str = "Private Release"
    
    # Installation paths
    install_dir: str = "/opt/rs-wifi-pro-v4"
    log_dir: str = "/var/log/rs-wifi-pro"
    capture_dir: str = "/tmp/rs-wifi-captures"
    wordlist_dir: str = "/usr/share/wordlists/rs-wordlists"
    report_dir: str = "/tmp/rs-wifi-reports"
    
    # Database
    db_path: str = "/var/lib/rs-wifi-pro/sessions.db"
    
    # Timeouts
    scan_timeout: int = 30
    handshake_timeout: int = 300
    crack_timeout: int = 3600
    wps_timeout: int = 300
    pmkid_timeout: int = 60
    
    # Display settings
    color_output: bool = True
    verbose: bool = False
    debug: bool = False
    
    # Network defaults
    default_channel: int = 1
    max_retries: int = 3
    deauth_packets: int = 10
    
    # Attack settings
    use_gpu: bool = True
    auto_crack: bool = False
    save_captures: bool = True
    
    def __post_init__(self):
        """Create directories after initialization"""
        for dir_path in [
            self.log_dir, self.capture_dir, self.wordlist_dir,
            self.report_dir, os.path.dirname(self.db_path)
        ]:
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
    
    @classmethod
    def from_file(cls, config_file: str) -> 'Config':
        """Load configuration from file"""
        config = cls()
        
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            except:
                pass
        
        return config
    
    def save(self, config_file: str):
        """Save configuration to file"""
        import json
        
        data = {
            'app_name': self.app_name,
            'version': self.version,
            'log_dir': self.log_dir,
            'capture_dir': self.capture_dir,
            'wordlist_dir': self.wordlist_dir,
            'scan_timeout': self.scan_timeout,
            'handshake_timeout': self.handshake_timeout,
            'crack_timeout': self.crack_timeout,
            'color_output': self.color_output,
            'verbose': self.verbose,
            'debug': self.debug,
            'use_gpu': self.use_gpu,
            'auto_crack': self.auto_crack,
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
