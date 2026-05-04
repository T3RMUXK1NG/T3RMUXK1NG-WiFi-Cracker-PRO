#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3RMUXK1NG WiFi Cracker PRO - Network Scanner Module
Advanced WiFi network discovery with multiple scanning methods
"""

import os
import re
import time
import json
import subprocess
import threading
import queue
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import socket
import struct
import fcntl

# Try to import optional dependencies
try:
    from scapy.all import Dot11, Dot11Beacon, Dot11Elt, RadioTap, sniff, wrpcap
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


@dataclass
class WiFiNetwork:
    """WiFi Network Data Structure"""
    bssid: str
    essid: str
    channel: int
    power: int
    encryption: str
    cipher: str = ""
    auth: str = ""
    clients: int = 0
    handshake: bool = False
    wps: bool = False
    wps_pin: str = ""
    wps_version: str = ""
    wps_locked: bool = False
    pmkid: bool = False
    band: str = "2.4GHz"
    frequency: int = 0
    beacon_interval: int = 100
    vendor: str = ""
    first_seen: str = ""
    last_seen: str = ""
    packets: int = 0
    data_rate: float = 0.0
    hidden: bool = False
    wpa3: bool = False
    owe: bool = False  # Opportunistic Wireless Encryption
    mesh: bool = False
    adhoc: bool = False
    
    def __post_init__(self):
        if not self.first_seen:
            self.first_seen = datetime.now().isoformat()
        self.last_seen = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @property
    def is_crackable(self) -> bool:
        """Check if network is potentially crackable"""
        if self.wps and not self.wps_locked:
            return True
        if 'WPA' in self.encryption or 'WEP' in self.encryption:
            return True
        return False
    
    @property
    def security_score(self) -> int:
        """Rate security 1-10 (higher = more secure)"""
        score = 1
        if 'WPA3' in self.encryption:
            score = 10
        elif 'WPA2' in self.encryption:
            score = 8
            if 'CCMP' in self.cipher or 'AES' in self.cipher:
                score = 9
        elif 'WPA' in self.encryption:
            score = 6
        elif 'WEP' in self.encryption:
            score = 2
        elif 'Open' in self.encryption or not self.encryption:
            score = 1
        
        # WPS vulnerability reduces score
        if self.wps and not self.wps_locked:
            score = max(1, score - 3)
        
        return score


@dataclass
class WiFiClient:
    """WiFi Client/Station Data Structure"""
    mac: str
    bssid: str = ""
    power: int = 0
    packets: int = 0
    first_seen: str = ""
    last_seen: str = ""
    vendor: str = ""
    probe_requests: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class NetworkScanner:
    """Advanced WiFi Network Scanner"""
    
    # OUI database for vendor lookup
    OUI_DB = {}
    
    # Common default credentials by vendor
    DEFAULT_CREDS = {
        'TP-LINK': [('admin', 'admin'), ('admin', 'password')],
        'NETGEAR': [('admin', 'password'), ('admin', 'admin')],
        'D-LINK': [('admin', 'admin'), ('admin', '(blank)')],
        'LINKSYS': [('admin', 'admin'), ('', 'admin')],
        'ASUS': [('admin', 'admin'), ('admin', 'password')],
        'CISCO': [('admin', 'admin'), ('cisco', 'cisco')],
        'BELKIN': [('admin', 'admin'), ('', 'admin')],
        'TENDA': [('admin', 'admin'), ('admin', '')],
        'HUAWEI': [('admin', 'admin'), ('user', 'user')],
        'ZTE': [('admin', 'admin'), ('user', 'user')],
    }
    
    def __init__(self, interface: str):
        self.interface = interface
        self.networks: Dict[str, WiFiNetwork] = {}
        self.clients: Dict[str, WiFiClient] = {}
        self.scan_process = None
        self.scanning = False
        self.scan_queue = queue.Queue()
        self.callbacks: List[Callable] = []
        self.scan_stats = {
            'start_time': None,
            'end_time': None,
            'packets_captured': 0,
            'networks_found': 0,
            'clients_found': 0
        }
        self._load_oui_db()
    
    def _load_oui_db(self):
        """Load OUI database for vendor lookup"""
        oui_paths = [
            '/usr/share/ieee-data/oui.txt',
            '/usr/share/wireshark/manuf',
            '/etc/manuf',
        ]
        
        for path in oui_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        for line in f:
                            if ':' in line:
                                parts = line.strip().split('\t') if '\t' in line else line.strip().split(None, 2)
                                if len(parts) >= 2:
                                    prefix = parts[0].replace(':', '').upper()[:6]
                                    vendor = parts[-1].split('#')[0].strip()
                                    self.OUI_DB[prefix] = vendor
                except Exception:
                    pass
                break
    
    def _get_vendor(self, mac: str) -> str:
        """Get vendor from MAC address"""
        prefix = mac.replace(':', '').upper()[:6]
        return self.OUI_DB.get(prefix, 'Unknown')
    
    def _get_frequency(self, channel: int) -> int:
        """Convert channel to frequency in MHz"""
        if channel == 14:
            return 2484
        elif 1 <= channel <= 13:
            return 2407 + (channel * 5)
        elif 36 <= channel <= 165:
            return 5000 + (channel * 5)
        return 0
    
    def _get_band(self, channel: int) -> str:
        """Determine band from channel"""
        if 1 <= channel <= 14:
            return "2.4GHz"
        elif 36 <= channel <= 165:
            return "5GHz"
        elif 183 <= channel <= 196:
            return "4.9GHz"
        elif channel > 196:
            return "6GHz"
        return "Unknown"
    
    def scan(self, duration: int = 30, channel: Optional[int] = None) -> List[WiFiNetwork]:
        """Scan for WiFi networks using airodump-ng"""
        import subprocess
        
        self.scan_stats['start_time'] = datetime.now()
        output_file = f"/tmp/rs_scan_{int(time.time())}"
        
        cmd = ['sudo', 'airodump-ng', self.interface, '-w', output_file, 
               '--output-format', 'csv', '--write-interval', '1']
        
        if channel:
            cmd.extend(['-c', str(channel)])
        
        try:
            self.scan_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.scanning = True
            
            # Wait and parse results
            csv_file = f"{output_file}-01.csv"
            
            for elapsed in range(duration):
                if not self.scanning:
                    break
                
                time.sleep(1)
                
                # Periodically parse partial results
                if os.path.exists(csv_file) and elapsed % 5 == 0:
                    self._parse_airodump_csv(csv_file)
            
            self.scanning = False
            self.scan_process.terminate()
            
            # Final parse
            if os.path.exists(csv_file):
                self._parse_airodump_csv(csv_file)
                os.remove(csv_file)
                # Clean up other files
                for f in Path('/tmp').glob(f"rs_scan_{int(self.scan_stats['start_time'].timestamp())}*"):
                    try:
                        f.unlink()
                    except:
                        pass
            
            self.scan_stats['end_time'] = datetime.now()
            self.scan_stats['networks_found'] = len(self.networks)
            
            return list(self.networks.values())
            
        except FileNotFoundError:
            # Fallback to nmcli
            return self._scan_nmcli()
        except Exception as e:
            print(f"Scan error: {e}")
            return []
    
    def _parse_airodump_csv(self, csv_file: str) -> None:
        """Parse airodump-ng CSV output"""
        try:
            with open(csv_file, 'r', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            in_networks = False
            in_clients = False
            
            for line in lines:
                # Find sections
                if 'BSSID, First time seen,' in line:
                    in_networks = True
                    in_clients = False
                    continue
                elif 'Station MAC, First time seen,' in line:
                    in_networks = False
                    in_clients = True
                    continue
                
                if not line.strip():
                    continue
                
                if in_networks:
                    self._parse_network_line(line)
                elif in_clients:
                    self._parse_client_line(line)
                    
        except Exception as e:
            print(f"Parse error: {e}")
    
    def _parse_network_line(self, line: str) -> None:
        """Parse a single network line from airodump CSV"""
        parts = line.split(',')
        
        if len(parts) < 14:
            return
        
        try:
            bssid = parts[0].strip()
            if not bssid or bssid == 'BSSID':
                return
            
            # Parse power
            power = int(parts[8].strip()) if parts[8].strip().lstrip('-').isdigit() else -100
            
            # Parse channel
            channel_str = parts[3].strip()
            channel = int(channel_str) if channel_str.isdigit() else 0
            
            # Parse ESSID
            essid = parts[13].strip().strip('"')
            if not essid:
                essid = "[Hidden]"
                hidden = True
            else:
                hidden = False
            
            # Parse encryption info
            encryption = parts[5].strip()
            cipher = parts[6].strip()
            auth = parts[7].strip()
            
            # Check for WPA3
            wpa3 = 'WPA3' in encryption or 'SAE' in auth
            owe = 'OWE' in encryption
            
            # Check for WPS
            wps = 'WPS' in line
            wps_locked = 'WPS Locked' in line or 'LOCKED' in line
            
            # Get frequency and band
            frequency = self._get_frequency(channel)
            band = self._get_band(channel)
            
            # Get vendor
            vendor = self._get_vendor(bssid)
            
            # Parse client count
            clients = int(parts[11].strip()) if parts[11].strip().isdigit() else 0
            
            # Create or update network
            if bssid in self.networks:
                network = self.networks[bssid]
                network.power = power
                network.last_seen = datetime.now().isoformat()
                network.packets += 1
            else:
                network = WiFiNetwork(
                    bssid=bssid,
                    essid=essid,
                    channel=channel,
                    power=power,
                    encryption=encryption,
                    cipher=cipher,
                    auth=auth,
                    clients=clients,
                    wps=wps,
                    wps_locked=wps_locked,
                    band=band,
                    frequency=frequency,
                    vendor=vendor,
                    hidden=hidden,
                    wpa3=wpa3,
                    owe=owe
                )
                self.networks[bssid] = network
                
        except (ValueError, IndexError) as e:
            pass
    
    def _parse_client_line(self, line: str) -> None:
        """Parse a single client line from airodump CSV"""
        parts = line.split(',')
        
        if len(parts) < 6:
            return
        
        try:
            mac = parts[0].strip()
            if not mac or mac == 'Station MAC':
                return
            
            bssid = parts[5].strip() if len(parts) > 5 else ""
            power = int(parts[3].strip()) if parts[3].strip().lstrip('-').isdigit() else -100
            
            vendor = self._get_vendor(mac)
            
            client = WiFiClient(
                mac=mac,
                bssid=bssid,
                power=power,
                vendor=vendor,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat()
            )
            
            if mac not in self.clients:
                self.clients[mac] = client
            else:
                self.clients[mac].bssid = bssid
                self.clients[mac].power = power
                self.clients[mac].last_seen = datetime.now().isoformat()
                
        except (ValueError, IndexError):
            pass
    
    def _scan_nmcli(self) -> List[WiFiNetwork]:
        """Fallback scan using nmcli"""
        networks = []
        
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'BSSID,SSID,SIGNAL,CHAN,SECURITY', 'dev', 'wifi', 'list'],
                capture_output=True, text=True, timeout=30
            )
            
            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 5:
                    bssid = parts[0]
                    essid = parts[1] if parts[1] else "[Hidden]"
                    signal = int(parts[2]) if parts[2].isdigit() else 0
                    channel = int(parts[3]) if parts[3].isdigit() else 0
                    encryption = parts[4] if len(parts) > 4 else "Unknown"
                    
                    network = WiFiNetwork(
                        bssid=bssid,
                        essid=essid,
                        channel=channel,
                        power=signal,
                        encryption=encryption,
                        vendor=self._get_vendor(bssid),
                        band=self._get_band(channel),
                        frequency=self._get_frequency(channel)
                    )
                    networks.append(network)
                    self.networks[bssid] = network
                    
        except FileNotFoundError:
            print("nmcli not found")
        except Exception as e:
            print(f"nmcli scan error: {e}")
        
        return networks
    
    def scan_continuous(self, callback: Optional[Callable] = None) -> None:
        """Start continuous scanning"""
        self.scanning = True
        output_file = f"/tmp/rs_scan_continuous_{int(time.time())}"
        
        cmd = ['sudo', 'airodump-ng', self.interface, '-w', output_file,
               '--output-format', 'csv', '--write-interval', '1']
        
        self.scan_process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        csv_file = f"{output_file}-01.csv"
        
        def _monitor():
            last_size = 0
            while self.scanning:
                time.sleep(2)
                
                if os.path.exists(csv_file):
                    try:
                        size = os.path.getsize(csv_file)
                        if size != last_size:
                            self._parse_airodump_csv(csv_file)
                            last_size = size
                            
                            if callback:
                                callback(list(self.networks.values()))
                    except:
                        pass
        
        monitor_thread = threading.Thread(target=_monitor, daemon=True)
        monitor_thread.start()
    
    def scan_channel(self, channel: int, duration: int = 30) -> List[WiFiNetwork]:
        """Scan specific channel"""
        return self.scan(duration, channel)
    
    def scan_bands(self, bands: List[str] = ['2.4GHz', '5GHz']) -> List[WiFiNetwork]:
        """Scan multiple bands"""
        all_networks = []
        
        if '2.4GHz' in bands:
            for ch in range(1, 14):
                networks = self.scan_channel(ch, 5)
                all_networks.extend(networks)
        
        if '5GHz' in bands:
            for ch in [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 
                       116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 
                       157, 161, 165]:
                networks = self.scan_channel(ch, 3)
                all_networks.extend(networks)
        
        return all_networks
    
    def scan_scapy(self, duration: int = 30, channel: Optional[int] = None) -> List[WiFiNetwork]:
        """Scan using Scapy (requires monitor mode)"""
        if not SCAPY_AVAILABLE:
            print("Scapy not available")
            return []
        
        def _packet_handler(pkt):
            if pkt.haslayer(Dot11Beacon):
                # Extract network info
                bssid = pkt[Dot11].addr2
                if not bssid or bssid in self.networks:
                    return
                
                # Get ESSID
                try:
                    essid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                except:
                    essid = "[Hidden]"
                
                # Get channel
                try:
                    channel = ord(pkt[Dot11Elt:3].info)
                except:
                    channel = 0
                
                # Get encryption
                encryption = "Unknown"
                cap = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}")
                if 'privacy' in cap:
                    encryption = "WEP"
                    # Check for WPA/WPA2
                    if pkt.haslayer(Dot11Elt):
                        elt = pkt[Dot11Elt]
                        while elt:
                            if elt.ID == 221 and 'WPA' in str(elt.info):
                                encryption = "WPA/WPA2"
                                break
                            elt = elt.payload
                
                # Get signal strength (approximate)
                power = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -50
                
                network = WiFiNetwork(
                    bssid=bssid,
                    essid=essid,
                    channel=channel,
                    power=power,
                    encryption=encryption,
                    vendor=self._get_vendor(bssid),
                    band=self._get_band(channel),
                    frequency=self._get_frequency(channel)
                )
                self.networks[bssid] = network
        
        # Set channel if specified
        if channel:
            subprocess.run(['sudo', 'iwconfig', self.interface, 'channel', str(channel)],
                         capture_output=True)
        
        # Start sniffing
        sniff(iface=self.interface, prn=_packet_handler, timeout=duration)
        
        return list(self.networks.values())
    
    def stop_scan(self) -> None:
        """Stop ongoing scan"""
        self.scanning = False
        if self.scan_process:
            self.scan_process.terminate()
            self.scan_process = None
    
    def get_network(self, bssid: str) -> Optional[WiFiNetwork]:
        """Get network by BSSID"""
        return self.networks.get(bssid)
    
    def get_networks_by_essid(self, essid: str) -> List[WiFiNetwork]:
        """Get networks by ESSID"""
        return [n for n in self.networks.values() if n.essid == essid]
    
    def get_clients(self, bssid: str) -> List[WiFiClient]:
        """Get clients connected to a network"""
        return [c for c in self.clients.values() if c.bssid == bssid]
    
    def export_results(self, format: str = 'json', output_file: str = None) -> str:
        """Export scan results"""
        data = {
            'scan_time': self.scan_stats['start_time'].isoformat() if self.scan_stats['start_time'] else None,
            'duration': str(self.scan_stats['end_time'] - self.scan_stats['start_time']) if self.scan_stats['end_time'] else None,
            'networks_count': len(self.networks),
            'clients_count': len(self.clients),
            'networks': [n.to_dict() for n in self.networks.values()],
            'clients': [c.to_dict() for c in self.clients.values()]
        }
        
        if format == 'json':
            output = json.dumps(data, indent=2)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=WiFiNetwork.__dataclass_fields__.keys())
            writer.writeheader()
            for n in self.networks.values():
                writer.writerow(n.to_dict())
            output = output.getvalue()
        else:
            output = str(data)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        
        return output
    
    def get_stats(self) -> Dict:
        """Get scan statistics"""
        return {
            **self.scan_stats,
            'networks_count': len(self.networks),
            'clients_count': len(self.clients),
            'crackable_networks': sum(1 for n in self.networks.values() if n.is_crackable),
            'wps_vulnerable': sum(1 for n in self.networks.values() if n.wps and not n.wps_locked),
            'open_networks': sum(1 for n in self.networks.values() if 'Open' in n.encryption or not n.encryption),
            'wpa3_networks': sum(1 for n in self.networks.values() if n.wpa3),
            'hidden_networks': sum(1 for n in self.networks.values() if n.hidden),
        }
    
    def suggest_attacks(self, bssid: str) -> List[Dict]:
        """Suggest possible attacks for a network"""
        network = self.networks.get(bssid)
        if not network:
            return []
        
        attacks = []
        
        # WPS attacks
        if network.wps and not network.wps_locked:
            attacks.append({
                'type': 'wps',
                'name': 'WPS Pixie Dust',
                'difficulty': 'easy',
                'success_rate': 'high',
                'time': '1-60 seconds'
            })
            attacks.append({
                'type': 'wps',
                'name': 'WPS PIN Brute Force',
                'difficulty': 'medium',
                'success_rate': 'medium',
                'time': 'hours to days'
            })
        
        # PMKID attack (no client needed)
        if 'WPA' in network.encryption:
            attacks.append({
                'type': 'pmkid',
                'name': 'PMKID Attack',
                'difficulty': 'medium',
                'success_rate': 'high',
                'time': 'minutes'
            })
        
        # Handshake capture
        if 'WPA' in network.encryption and network.clients > 0:
            attacks.append({
                'type': 'handshake',
                'name': 'Handshake Capture + Crack',
                'difficulty': 'medium',
                'success_rate': 'depends on password',
                'time': 'varies'
            })
        
        # Evil Twin
        attacks.append({
            'type': 'evil_twin',
            'name': 'Evil Twin Attack',
            'difficulty': 'medium',
            'success_rate': 'high (requires client interaction)',
            'time': 'varies'
        })
        
        # WEP attacks
        if 'WEP' in network.encryption:
            attacks.append({
                'type': 'wep',
                'name': 'WEP Cracking',
                'difficulty': 'easy',
                'success_rate': 'very high',
                'time': 'minutes to hours'
            })
        
        return attacks


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scanner.py <interface> [duration]")
        sys.exit(1)
    
    interface = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    scanner = NetworkScanner(interface)
    
    print(f"Scanning for {duration} seconds...")
    networks = scanner.scan(duration)
    
    print(f"\nFound {len(networks)} networks:")
    for n in networks:
        print(f"  {n.essid} ({n.bssid}) - {n.encryption} - Ch:{n.channel} - {n.power}dBm")
