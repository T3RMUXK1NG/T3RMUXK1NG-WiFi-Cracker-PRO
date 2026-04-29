#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Hashcat Bridge Module"""

import os
import subprocess
from typing import Optional, Dict

class HashcatBridge:
    def __init__(self):
        self.hashcat_path = 'hashcat'
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        try:
            result = subprocess.run(['hashcat', '--version'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def crack_wpa(self, hccapx_file: str, wordlist: str, rules: str = None) -> Dict:
        if not self.available:
            return {'success': False, 'error': 'Hashcat not available'}
        
        cmd = ['hashcat', '-m', '22000', hccapx_file, wordlist, '--force']
        if rules:
            cmd.extend(['-r', rules])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            
            if result.returncode == 0 or 'Cracked' in result.stdout:
                password = self._extract_password(result.stdout, hccapx_file)
                return {'success': True, 'password': password}
            
            return {'success': False, 'error': 'Password not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_password(self, output: str, target: str) -> Optional[str]:
        for line in output.split('\n'):
            if target in line and ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    return parts[-1].strip()
        return None
    
    def get_status(self) -> Dict:
        return {'available': self.available}
