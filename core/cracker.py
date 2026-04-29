#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO - Password Cracker Module
Multi-method password cracking with GPU acceleration support
"""

import os
import re
import time
import json
import subprocess
import threading
import queue
import hashlib
import hmac
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Generator
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import math


@dataclass
class CrackingResult:
    """Password cracking result"""
    success: bool
    target: str
    password: str = ""
    method: str = ""
    time_taken: float = 0.0
    attempts: int = 0
    speed: float = 0.0  # passwords per second
    wordlist: str = ""
    error: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'target': self.target,
            'password': self.password,
            'method': self.method,
            'time_taken': self.time_taken,
            'attempts': self.attempts,
            'speed': self.speed,
            'wordlist': self.wordlist,
            'error': self.error,
            'timestamp': self.timestamp or datetime.now().isoformat()
        }


class PasswordCracker:
    """Advanced Password Cracking Engine"""
    
    # Common password patterns
    PATTERNS = {
        'numeric': r'^\d+$',
        'alpha_lower': r'^[a-z]+$',
        'alpha_upper': r'^[A-Z]+$',
        'alpha_mixed': r'^[a-zA-Z]+$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'special': r'.*[!@#$%^&*(),.?":{}|<>].*',
    }
    
    def __init__(self):
        self.results: List[CrackingResult] = []
        self.stop_flag = False
        self.current_attempt = 0
        self.start_time = None
        self.progress_callback: Optional[Callable] = None
        self.stats = {
            'total_cracked': 0,
            'total_failed': 0,
            'total_time': 0.0,
            'total_attempts': 0
        }
    
    def crack(self, cap_file: str, wordlist: str, method: str = "dictionary",
              rules: str = None, mask: str = None) -> CrackingResult:
        """Main cracking method dispatcher"""
        start_time = time.time()
        
        if not os.path.exists(cap_file):
            return CrackingResult(
                success=False, target=cap_file, error="Capture file not found"
            )
        
        methods = {
            'dictionary': self._crack_dictionary,
            'brute': self._crack_brute,
            'rule': self._crack_rule,
            'combo': self._crack_combo,
            'hybrid': self._crack_hybrid,
            'mask': self._crack_mask,
            'incremental': self._crack_incremental,
            'ai': self._crack_ai,
        }
        
        cracker = methods.get(method, self._crack_dictionary)
        result = cracker(cap_file, wordlist, rules=rules, mask=mask)
        
        result.time_taken = time.time() - start_time
        result.timestamp = datetime.now().isoformat()
        
        self.results.append(result)
        self._update_stats(result)
        
        return result
    
    def _crack_dictionary(self, cap_file: str, wordlist: str, **kwargs) -> CrackingResult:
        """Dictionary attack using aircrack-ng"""
        if not os.path.exists(wordlist):
            return CrackingResult(
                success=False, target=cap_file, error="Wordlist not found"
            )
        
        try:
            cmd = ['aircrack-ng', '-w', wordlist, cap_file]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output, _ = process.communicate(timeout=3600)  # 1 hour timeout
            
            if 'KEY FOUND!' in output:
                # Extract password
                match = re.search(r'\[\s*([^\]]+)\s*\]', output.split('KEY FOUND!')[1])
                if match:
                    password = match.group(1).strip()
                    return CrackingResult(
                        success=True,
                        target=cap_file,
                        password=password,
                        method='dictionary',
                        wordlist=wordlist
                    )
            
            return CrackingResult(
                success=False,
                target=cap_file,
                method='dictionary',
                wordlist=wordlist,
                error="Password not in wordlist"
            )
            
        except subprocess.TimeoutExpired:
            return CrackingResult(
                success=False, target=cap_file, error="Cracking timeout"
            )
        except FileNotFoundError:
            return CrackingResult(
                success=False, target=cap_file, error="aircrack-ng not found"
            )
        except Exception as e:
            return CrackingResult(
                success=False, target=cap_file, error=str(e)
            )
    
    def _crack_brute(self, cap_file: str, wordlist: str = None, 
                     charset: str = None, max_len: int = 8, **kwargs) -> CrackingResult:
        """Brute force attack"""
        start_time = time.time()
        
        # Default charset
        if not charset:
            charset = 'abcdefghijklmnopqrstuvwxyz0123456789'
        
        # Generate passwords on the fly
        passwords = self._generate_brute(charset, max_len)
        temp_wordlist = f"/tmp/brute_{int(time.time())}.txt"
        
        attempts = 0
        found = False
        password = ""
        
        with open(temp_wordlist, 'w') as f:
            for pwd in passwords:
                if self.stop_flag:
                    break
                f.write(pwd + '\n')
                attempts += 1
                
                # Crack in batches
                if attempts % 10000 == 0:
                    f.flush()
                    result = self._crack_dictionary(cap_file, temp_wordlist)
                    if result.success:
                        found = True
                        password = result.password
                        break
                    
                    # Clear temp file
                    open(temp_wordlist, 'w').close()
                    
                    if self.progress_callback:
                        self.progress_callback(attempts, time.time() - start_time)
        
        # Final attempt
        if not found and os.path.exists(temp_wordlist):
            result = self._crack_dictionary(cap_file, temp_wordlist)
            if result.success:
                found = True
                password = result.password
        
        # Cleanup
        if os.path.exists(temp_wordlist):
            os.remove(temp_wordlist)
        
        return CrackingResult(
            success=found,
            target=cap_file,
            password=password,
            method='brute',
            attempts=attempts,
            time_taken=time.time() - start_time
        )
    
    def _generate_brute(self, charset: str, max_len: int) -> Generator[str, None, None]:
        """Generate brute force passwords"""
        from itertools import product
        
        for length in range(1, max_len + 1):
            for combo in product(charset, repeat=length):
                yield ''.join(combo)
    
    def _crack_rule(self, cap_file: str, wordlist: str, 
                    rules: str = "best64", **kwargs) -> CrackingResult:
        """Rule-based attack"""
        # Try hashcat with rules first
        result = self._crack_hashcat(cap_file, wordlist, rules=rules)
        
        if result.success:
            result.method = 'rule'
            return result
        
        # Fallback: manual rule application
        if not os.path.exists(wordlist):
            return CrackingResult(
                success=False, target=cap_file, error="Wordlist not found"
            )
        
        # Apply common rules
        temp_wordlist = f"/tmp/rule_{int(time.time())}.txt"
        passwords = set()
        
        with open(wordlist, 'r') as f:
            for line in f:
                pwd = line.strip()
                if not pwd:
                    continue
                
                # Original
                passwords.add(pwd)
                
                # Common mutations
                passwords.add(pwd.upper())
                passwords.add(pwd.lower())
                passwords.add(pwd.capitalize())
                passwords.add(pwd + '1')
                passwords.add(pwd + '12')
                passwords.add(pwd + '123')
                passwords.add(pwd + '1234')
                passwords.add(pwd + '!')
                passwords.add(pwd + '@')
                passwords.add('1' + pwd)
                passwords.add('123' + pwd)
                passwords.add(pwd[::-1])  # Reverse
                passwords.add(pwd.replace('a', '@'))
                passwords.add(pwd.replace('e', '3'))
                passwords.add(pwd.replace('i', '1'))
                passwords.add(pwd.replace('o', '0'))
                passwords.add(pwd.replace('s', '$'))
                
                # Leet speak
                leet = pwd
                for old, new in [('a', '4'), ('e', '3'), ('i', '1'), ('o', '0'), ('s', '5')]:
                    leet = leet.replace(old, new)
                passwords.add(leet)
        
        with open(temp_wordlist, 'w') as f:
            for pwd in passwords:
                f.write(pwd + '\n')
        
        result = self._crack_dictionary(cap_file, temp_wordlist)
        result.method = 'rule'
        
        os.remove(temp_wordlist)
        return result
    
    def _crack_combo(self, cap_file: str, wordlist: str, **kwargs) -> CrackingResult:
        """Combinator attack"""
        if not os.path.exists(wordlist):
            return CrackingResult(
                success=False, target=cap_file, error="Wordlist not found"
            )
        
        # Split wordlist into two halves
        with open(wordlist, 'r') as f:
            words = [line.strip() for line in f if line.strip()]
        
        mid = len(words) // 2
        left = words[:mid]
        right = words[mid:]
        
        temp_wordlist = f"/tmp/combo_{int(time.time())}.txt"
        
        with open(temp_wordlist, 'w') as f:
            for l in left:
                for r in right:
                    f.write(l + r + '\n')
                    f.write(r + l + '\n')
        
        result = self._crack_dictionary(cap_file, temp_wordlist)
        result.method = 'combo'
        
        os.remove(temp_wordlist)
        return result
    
    def _crack_hybrid(self, cap_file: str, wordlist: str, **kwargs) -> CrackingResult:
        """Hybrid attack (dictionary + mask)"""
        if not os.path.exists(wordlist):
            return CrackingResult(
                success=False, target=cap_file, error="Wordlist not found"
            )
        
        temp_wordlist = f"/tmp/hybrid_{int(time.time())}.txt"
        masks = ['?d', '?d?d', '?d?d?d', '?d?d?d?d']
        
        with open(wordlist, 'r') as rf:
            words = [line.strip() for line in rf if line.strip()]
        
        with open(temp_wordlist, 'w') as wf:
            for word in words:
                wf.write(word + '\n')
                for mask in masks:
                    for i in range(10 ** len(mask.replace('?d', ''))):
                        suffix = str(i).zfill(len(mask.replace('?d', '')))
                        wf.write(word + suffix + '\n')
                        wf.write(suffix + word + '\n')
        
        result = self._crack_dictionary(cap_file, temp_wordlist)
        result.method = 'hybrid'
        
        os.remove(temp_wordlist)
        return result
    
    def _crack_mask(self, cap_file: str, wordlist: str = None,
                    mask: str = "?l?l?l?l?l?l?l?l", **kwargs) -> CrackingResult:
        """Mask attack"""
        # Convert hashcat mask to actual passwords
        mask_chars = {
            '?l': 'abcdefghijklmnopqrstuvwxyz',
            '?u': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '?d': '0123456789',
            '?s': '!@#$%^&*()_+-=[]{}|;:,.<>?',
            '?a': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?',
        }
        
        # Parse mask
        charsets = []
        i = 0
        while i < len(mask):
            if mask[i] == '?' and i + 1 < len(mask):
                char_type = mask[i:i+2]
                charsets.append(mask_chars.get(char_type, ''))
                i += 2
            else:
                charsets.append(mask[i])
                i += 1
        
        temp_wordlist = f"/tmp/mask_{int(time.time())}.txt"
        
        from itertools import product
        count = 0
        
        with open(temp_wordlist, 'w') as f:
            for combo in product(*charsets):
                if self.stop_flag:
                    break
                f.write(''.join(combo) + '\n')
                count += 1
                
                if count % 100000 == 0:
                    f.flush()
                    result = self._crack_dictionary(cap_file, temp_wordlist)
                    if result.success:
                        result.method = 'mask'
                        return result
                    open(temp_wordlist, 'w').close()
                    count = 0
        
        result = self._crack_dictionary(cap_file, temp_wordlist)
        result.method = 'mask'
        
        if os.path.exists(temp_wordlist):
            os.remove(temp_wordlist)
        
        return result
    
    def _crack_incremental(self, cap_file: str, wordlist: str = None, **kwargs) -> CrackingResult:
        """Incremental brute force attack"""
        charsets = [
            '0123456789',
            'abcdefghijklmnopqrstuvwxyz',
            'abcdefghijklmnopqrstuvwxyz0123456789',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*',
        ]
        
        for charset in charsets:
            result = self._crack_brute(cap_file, charset=charset, max_len=8)
            if result.success:
                result.method = 'incremental'
                return result
            if self.stop_flag:
                break
        
        return CrackingResult(
            success=False,
            target=cap_file,
            method='incremental',
            error="Password not found in incremental search"
        )
    
    def _crack_ai(self, cap_file: str, wordlist: str = None, **kwargs) -> CrackingResult:
        """AI-powered password cracking"""
        # This would integrate with the AI module
        # For now, generate common patterns
        
        common_patterns = [
            # Company name + year
            r'[A-Za-z]+\d{4}',
            r'[A-Za-z]+@\d{4}',
            # Phone patterns
            r'\d{10}',
            r'\d{3}-\d{3}-\d{4}',
            # Common words with numbers
            r'password\d+',
            r'admin\d+',
            r'welcome\d+',
            r'letmein\d+',
            # Keyboard patterns
            r'qwerty\d*',
            r'asdfgh\d*',
            r'zxcvbn\d*',
        ]
        
        temp_wordlist = f"/tmp/ai_{int(time.time())}.txt"
        
        with open(temp_wordlist, 'w') as f:
            for pattern in common_patterns:
                # Generate passwords matching pattern
                if r'\d{4}' in pattern:
                    for word in ['password', 'admin', 'welcome', 'user', 'wifi']:
                        for year in range(2000, 2026):
                            f.write(f"{word}{year}\n")
                elif r'\d{10}' in pattern:
                    for prefix in ['98', '99', '70', '80', '90']:
                        for i in range(10000000):
                            f.write(f"{prefix}{i:08d}\n")
                            if i > 100000:
                                break
                else:
                    for word in ['qwerty', 'asdfgh', 'zxcvbn', 'password', 'admin']:
                        for suffix in ['', '1', '12', '123', '1234', '!', '@']:
                            f.write(f"{word}{suffix}\n")
        
        result = self._crack_dictionary(cap_file, temp_wordlist)
        result.method = 'ai'
        
        os.remove(temp_wordlist)
        return result
    
    def _crack_hashcat(self, cap_file: str, wordlist: str, 
                       rules: str = None, hash_mode: int = 22000) -> CrackingResult:
        """Crack using hashcat GPU acceleration"""
        # Convert cap to hccapx
        hccapx_file = cap_file.replace('.cap', '.hccapx')
        
        try:
            # Convert using cap2hccapx or aircrack
            subprocess.run(
                ['aircrack-ng', '-J', hccapx_file.replace('.hccapx', ''), cap_file],
                capture_output=True
            )
        except:
            pass
        
        if not os.path.exists(hccapx_file):
            return CrackingResult(
                success=False, target=cap_file, error="Failed to convert to hccapx"
            )
        
        try:
            cmd = ['hashcat', '-m', str(hash_mode), hccapx_file, wordlist, '--force']
            
            if rules:
                cmd.extend(['-r', rules])
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output, _ = process.communicate(timeout=7200)  # 2 hour timeout
            
            # Check if cracked
            if 'Cracked' in output or process.returncode == 0:
                # Get password from output
                for line in output.split('\n'):
                    if hccapx_file in line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            password = parts[-1].strip()
                            return CrackingResult(
                                success=True,
                                target=cap_file,
                                password=password,
                                method='hashcat',
                                wordlist=wordlist
                            )
            
            return CrackingResult(
                success=False,
                target=cap_file,
                method='hashcat',
                wordlist=wordlist,
                error="Password not found"
            )
            
        except FileNotFoundError:
            return CrackingResult(
                success=False, target=cap_file, error="hashcat not found"
            )
        except subprocess.TimeoutExpired:
            return CrackingResult(
                success=False, target=cap_file, error="Hashcat timeout"
            )
        except Exception as e:
            return CrackingResult(
                success=False, target=cap_file, error=str(e)
            )
    
    def crack_pmkid(self, pmkid_file: str, wordlist: str = None) -> CrackingResult:
        """Crack PMKID capture"""
        if not wordlist:
            wordlist = "/usr/share/wordlists/rockyou.txt"
        
        return self._crack_hashcat(pmkid_file, wordlist, hash_mode=16800)
    
    def stop(self):
        """Stop ongoing cracking"""
        self.stop_flag = True
    
    def _update_stats(self, result: CrackingResult):
        """Update cracking statistics"""
        if result.success:
            self.stats['total_cracked'] += 1
        else:
            self.stats['total_failed'] += 1
        
        self.stats['total_time'] += result.time_taken
        self.stats['total_attempts'] += result.attempts
    
    def get_stats(self) -> Dict:
        """Get cracking statistics"""
        return self.stats.copy()
    
    def get_results(self) -> List[CrackingResult]:
        """Get all cracking results"""
        return self.results.copy()
    
    def save_results(self, output_file: str):
        """Save results to file"""
        data = {
            'stats': self.stats,
            'results': [r.to_dict() for r in self.results]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)


class DistributedCracker:
    """Distributed cracking across multiple machines"""
    
    def __init__(self, nodes: List[str] = None):
        self.nodes = nodes or []
        self.results = queue.Queue()
        self.stop_flag = False
    
    def add_node(self, host: str, port: int = 22):
        """Add cracking node"""
        self.nodes.append(f"{host}:{port}")
    
    def distribute_crack(self, cap_file: str, wordlist: str):
        """Distribute cracking across nodes"""
        # Split wordlist
        total_lines = sum(1 for _ in open(wordlist))
        lines_per_node = total_lines // len(self.nodes)
        
        threads = []
        
        for i, node in enumerate(self.nodes):
            start_line = i * lines_per_node
            end_line = start_line + lines_per_node if i < len(self.nodes) - 1 else total_lines
            
            t = threading.Thread(
                target=self._crack_node,
                args=(node, cap_file, wordlist, start_line, end_line)
            )
            t.start()
            threads.append(t)
        
        # Wait for first success
        while not self.stop_flag:
            try:
                result = self.results.get(timeout=1)
                if result['success']:
                    self.stop_flag = True
                    break
            except queue.Empty:
                pass
        
        for t in threads:
            t.join(timeout=5)
        
        return result if 'result' in dir() else {'success': False}
    
    def _crack_node(self, node: str, cap_file: str, wordlist: str, 
                    start_line: int, end_line: int):
        """Crack on remote node"""
        import paramiko
        
        host, port = node.split(':')
        
        try:
            client = paramiko.SSHClient()
            client.connect(host, port=int(port))
            
            # Extract wordlist portion
            cmd = f"sed -n '{start_line},{end_line}p' {wordlist} | aircrack-ng -w - {cap_file}"
            stdin, stdout, stderr = client.exec_command(cmd)
            
            output = stdout.read().decode()
            
            if 'KEY FOUND!' in output:
                match = re.search(r'\[\s*([^\]]+)\s*\]', output)
                if match:
                    self.results.put({
                        'success': True,
                        'password': match.group(1).strip()
                    })
                    return
            
            self.results.put({'success': False})
            
        except Exception as e:
            self.results.put({'success': False, 'error': str(e)})


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python cracker.py <capture_file> <wordlist> [method]")
        print("Methods: dictionary, brute, rule, combo, hybrid, mask, ai")
        sys.exit(1)
    
    cap_file = sys.argv[1]
    wordlist = sys.argv[2]
    method = sys.argv[3] if len(sys.argv) > 3 else 'dictionary'
    
    cracker = PasswordCracker()
    
    print(f"Cracking {cap_file} using {method} attack...")
    result = cracker.crack(cap_file, wordlist, method)
    
    if result.success:
        print(f"\nPassword found: {result.password}")
        print(f"Time: {result.time_taken:.2f}s")
    else:
        print(f"\nFailed: {result.error}")
