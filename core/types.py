#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Data Types"""
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime


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


class AttackType(Enum):
    """Attack types"""
    HANDSHAKE = auto()
    PMKID = auto()
    WPS_PIXIE = auto()
    WPS_BRUTE = auto()
    DEAUTH = auto()
    EVIL_TWIN = auto()
    KARMA = auto()
    MITM = auto()


class AttackStatus(Enum):
    """Attack status"""
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    TIMEOUT = auto()


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
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    password: str = ""
    
    def to_dict(self) -> dict:
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
            'last_seen': self.last_seen,
            'password': self.password
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WiFiNetwork':
        return cls(
            bssid=data.get('bssid', ''),
            essid=data.get('essid', ''),
            channel=data.get('channel', 0),
            power=data.get('power', -100),
            security=SecurityType[data.get('security', 'UNKNOWN')],
            cipher=data.get('cipher', ''),
            auth=data.get('auth', ''),
            clients=data.get('clients', 0),
            wps=data.get('wps', False),
            wps_locked=data.get('wps_locked', False),
            pmkid=data.get('pmkid', False),
            handshake_captured=data.get('handshake_captured', False),
            first_seen=data.get('first_seen', datetime.now().isoformat()),
            last_seen=data.get('last_seen', datetime.now().isoformat()),
            password=data.get('password', '')
        )


@dataclass
class WiFiClient:
    """WiFi client data"""
    mac: str
    bssid: str
    power: int
    packets: int
    channel: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
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
    
    def to_dict(self) -> dict:
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


@dataclass
class HandshakeCapture:
    """Handshake capture data"""
    bssid: str
    essid: str
    capture_file: str
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cracked: bool = False
    password: str = ""
    
    def to_dict(self) -> dict:
        return {
            'bssid': self.bssid,
            'essid': self.essid,
            'capture_file': self.capture_file,
            'captured_at': self.captured_at,
            'cracked': self.cracked,
            'password': self.password
        }


@dataclass
class AttackResult:
    """Attack result data"""
    attack_type: AttackType
    target: str
    status: AttackStatus
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""
    result: str = ""
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'attack_type': self.attack_type.name,
            'target': self.target,
            'status': self.status.name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'result': self.result,
            'details': self.details
        }
