#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Network Scanner Module"""
import os
import re
import time
import subprocess
from typing import List, Dict, Optional
from datetime import datetime
from .types import WiFiNetwork, WiFiClient, SecurityType


class NetworkScanner:
    """Advanced WiFi network scanner"""
    
    VENDOR_OUI = {
        '00:0A': 'Cisco', '00:0B': 'Cisco', '00:0C': 'Cisco', '00:0D': 'Cisco',
        '00:0E': 'Cisco', '00:0F': 'Cisco', '00:10': 'Cisco', '00:11': 'Cisco',
        '00:12': 'Cisco', '00:13': 'Cisco', '00:14': 'Cisco', '00:15': 'Cisco',
        '00:50': 'Intel', '00:1E': 'Intel', '00:1F': 'Intel', '00:22': 'Intel',
        '00:23': 'Intel', '00:24': 'Intel', '00:25': 'Intel', '00:26': 'Intel',
        'DC:A6': 'Raspberry Pi', 'B8:27': 'Raspberry Pi',
        '28:2E': 'Xiaomi', '34:CE': 'Xiaomi', '4C:66': 'Xiaomi',
        '00:26': 'Samsung', '00:27': 'Samsung', 'A4:83': 'Samsung',
        '08:00': 'Dell', '00:06': 'Dell', '00:08': 'Dell', '00:DD': 'Dell',
        'F0:1F': 'Dell', 'F0:4D': 'Dell', '00:1A': 'Dell',
    }
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.networks: Dict[str, WiFiNetwork] = {}
        self.clients: Dict[str, WiFiClient] = {}
        self.scanning = False
        self.scan_results_file = ""
    
    def get_vendor(self, mac: str) -> str:
        """Get vendor from MAC address OUI"""
        if not mac:
            return "Unknown"
        oui = mac[:8].upper()
        for prefix, vendor in self.VENDOR_OUI.items():
            if oui.startswith(prefix.upper()):
                return vendor
        return "Unknown"
    
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
            process.wait(timeout=5)
            
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
            with open(csv_file, 'r', errors='ignore') as f:
                lines = f.readlines()
            
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
                            line_upper = line.upper()
                            if 'WPA3' in line_upper:
                                security = SecurityType.WPA3
                            elif 'WPA2' in line_upper:
                                security = SecurityType.WPA2
                            elif 'WPA' in line_upper:
                                security = SecurityType.WPA
                            elif 'WEP' in line_upper:
                                security = SecurityType.WEP
                            elif 'OPN' in line_upper:
                                security = SecurityType.OPEN
                            
                            network = WiFiNetwork(
                                bssid=bssid,
                                essid=essid,
                                channel=channel,
                                power=power,
                                security=security
                            )
                            self.networks[bssid] = network
                            if self.db:
                                self.db.save_network(network)
                        except Exception as e:
                            pass
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
                    if self.db:
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
        
        if current_network and current_bssid:
            self.networks[current_bssid] = current_network
            if self.db:
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
                            if self.db:
                                self.db.save_network(network)
                
                self.logger.success(f"Found {len(self.networks)} networks")
        except Exception as e:
            self.logger.error(f"nmcli scan failed: {e}")
        
        return list(self.networks.values())
    
    def scan_scapy(self, timeout: int = 10) -> List[WiFiNetwork]:
        """Scan using scapy"""
        self.logger.info("Scanning with scapy...")
        
        try:
            from scapy.all import Dot11, Dot11Beacon, Dot11Elt, sniff
            
            def packet_handler(pkt):
                if pkt.haslayer(Dot11Beacon):
                    bssid = pkt[Dot11].addr2
                    if bssid and bssid not in self.networks:
                        try:
                            essid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                            capability = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}")
                            
                            security = SecurityType.OPEN
                            if 'privacy' in capability:
                                security = SecurityType.WPA
                            
                            stats = pkt[Dot11].dBm_AntSignal if hasattr(pkt[Dot11], 'dBm_AntSignal') else -50
                            
                            network = WiFiNetwork(
                                bssid=bssid,
                                essid=essid,
                                channel=1,
                                power=stats,
                                security=security
                            )
                            self.networks[bssid] = network
                        except:
                            pass
            
            sniff(iface=self.interface, prn=packet_handler, timeout=timeout)
            self.logger.success(f"Found {len(self.networks)} networks")
        except ImportError:
            self.logger.warning("Scapy not available")
        except Exception as e:
            self.logger.error(f"Scapy scan failed: {e}")
        
        return list(self.networks.values())
    
    def get_clients(self, bssid: str = None) -> List[WiFiClient]:
        """Get connected clients"""
        if bssid:
            return [c for c in self.clients.values() if c.bssid == bssid]
        return list(self.clients.values())
    
    def display_networks(self, networks: List[WiFiNetwork] = None):
        """Display networks in a formatted table"""
        networks = networks or list(self.networks.values())
        
        colors = {
            'RED': '\033[91m',
            'GREEN': '\033[92m', 
            'YELLOW': '\033[93m',
            'CYAN': '\033[96m',
            'BOLD': '\033[1m',
            'DIM': '\033[2m',
            'RESET': '\033[0m'
        }
        
        print(f"\n{colors['BOLD']}{'#':<4} {'BSSID':<18} {'ESSID':<25} {'CH':<4} {'PWR':<6} {'Security':<12} {'WPS'}{colors['RESET']}")
        print("-" * 85)
        
        for i, net in enumerate(networks, 1):
            wps_str = f"{colors['GREEN']}Yes{colors['RESET']}" if net.wps else f"{colors['DIM']}No{colors['RESET']}"
            sec_color = colors['RED'] if net.security in [SecurityType.OPEN, SecurityType.WEP] else colors['GREEN']
            essid = net.essid[:22] + "..." if len(net.essid) > 25 else net.essid
            
            print(f"{i:<4} {net.bssid:<18} {essid:<25} {net.channel:<4} {net.power:<6} "
                  f"{sec_color}{net.security.name:<12}{colors['RESET']} {wps_str}")
    
    def clear_results(self):
        """Clear scan results"""
        self.networks.clear()
        self.clients.clear()
