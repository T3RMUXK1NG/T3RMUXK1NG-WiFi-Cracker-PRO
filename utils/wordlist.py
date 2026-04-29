#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO - Wordlist Generator Utility
Advanced password wordlist generation
"""

import os
import re
import json
import itertools
from datetime import datetime
from typing import List, Dict, Optional, Generator
from pathlib import Path


class WordlistGenerator:
    """Advanced Wordlist Generator"""
    
    # Common password bases
    COMMON_BASES = [
        'password', 'admin', 'user', 'guest', 'root', 'toor',
        'wifi', 'router', 'network', 'internet', 'wireless',
        'home', 'house', 'office', 'company', 'business',
        'demo', 'test', 'temp', 'default', 'login',
        'samsung', 'apple', 'android', 'iphone', 'phone',
        'linksys', 'netgear', 'dlink', 'tplink', 'belkin',
        'cisco', 'huawei', 'zte', 'xiaomi', 'asus'
    ]
    
    # Common suffixes
    SUFFIXES = [
        '', '1', '12', '123', '1234', '12345', '123456', '1234567', '12345678',
        '!', '@', '#', '$', '!1', '@1', '#1', '!123', '@123', '#123',
        '01', '02', '11', '22', '69', '99', '00', '420', '666',
        'password', 'admin', 'wifi', 'router', 'pass'
    ]
    
    # Year patterns
    YEARS = list(range(1990, datetime.now().year + 2))
    
    def __init__(self):
        self.output_dir = Path("/home/z/my-project/download/RS-WiFi-Cracker-PRO/wordlists")
        self.output_dir.mkdir(exist_ok=True)
        self.stats = {
            'wordlists_generated': 0,
            'total_passwords': 0
        }
    
    def from_essid(self, essid: str, output_path: str = None,
                   variations: bool = True) -> str:
        """Generate wordlist from ESSID"""
        passwords = set()
        
        # Base variations
        passwords.add(essid)
        passwords.add(essid.lower())
        passwords.add(essid.upper())
        passwords.add(essid.capitalize())
        passwords.add(essid.replace(' ', ''))
        passwords.add(essid.replace(' ', '_'))
        passwords.add(essid.replace(' ', '-'))
        
        if variations:
            # Number suffixes
            for i in range(10000):
                passwords.add(f"{essid}{i}")
                passwords.add(f"{essid.lower()}{i}")
            
            # Year patterns
            for year in self.YEARS:
                passwords.add(f"{essid}{year}")
                passwords.add(f"{essid.lower()}{year}")
            
            # Common suffixes
            for suffix in self.SUFFIXES:
                passwords.add(f"{essid}{suffix}")
                passwords.add(f"{essid.lower()}{suffix}")
                passwords.add(f"{essid.upper()}{suffix}")
            
            # Reverse
            passwords.add(essid[::-1])
            passwords.add(essid.lower()[::-1])
            
            # Leet speak
            leet = self._to_leet(essid)
            passwords.add(leet)
        
        output_path = output_path or str(self.output_dir / f"wordlist_{essid}.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def from_company(self, company: str, output_path: str = None) -> str:
        """Generate wordlist from company name"""
        passwords = set()
        
        # Company name variations
        base_words = [
            company,
            company.lower(),
            company.upper(),
            company.replace(' ', ''),
            company.replace(' ', '_'),
            company.replace(' ', '-'),
            ''.join(word[0].upper() for word in company.split()),  # Acronym
        ]
        
        for base in base_words:
            passwords.add(base)
            
            # With numbers
            for i in range(1000):
                passwords.add(f"{base}{i}")
            
            # With years
            for year in self.YEARS:
                passwords.add(f"{base}{year}")
            
            # With suffixes
            for suffix in ['!', '@', '#', '$', '123', '1234', '12345']:
                passwords.add(f"{base}{suffix}")
        
        # Add common corporate patterns
        corporate_patterns = [
            f"{company}admin",
            f"{company}guest",
            f"{company}wifi",
            f"{company}2024",
            f"{company}2025",
            f"Welcome{company}",
            f"{company}@123",
        ]
        
        for pattern in corporate_patterns:
            passwords.add(pattern)
            passwords.add(pattern.lower())
        
        output_path = output_path or str(self.output_dir / f"wordlist_{company}.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def from_social(self, username: str, output_path: str = None) -> str:
        """Generate wordlist from social media username"""
        passwords = set()
        
        # Username variations
        passwords.add(username)
        passwords.add(username.lower())
        passwords.add(username.upper())
        
        # With numbers
        for i in range(10000):
            passwords.add(f"{username}{i}")
            passwords.add(f"{username.lower()}{i}")
        
        # With years
        for year in self.YEARS:
            passwords.add(f"{username}{year}")
        
        # Common patterns
        patterns = [
            f"{username}password",
            f"{username}123",
            f"{username}@123",
            f"{username}!",
            f"Hello{username}",
            f"Welcome{username}",
            f"ILove{username}",
            f"{username}Love",
        ]
        
        for pattern in patterns:
            passwords.add(pattern)
            passwords.add(pattern.lower())
        
        output_path = output_path or str(self.output_dir / f"wordlist_{username}.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def common(self, output_path: str = None, top: int = 100000) -> str:
        """Generate common passwords wordlist"""
        passwords = set()
        
        # Add common bases
        passwords.update(self.COMMON_BASES)
        
        # Variations of common bases
        for base in self.COMMON_BASES:
            passwords.add(base)
            passwords.add(base.upper())
            passwords.add(base.capitalize())
            
            # With numbers
            for i in range(100):
                passwords.add(f"{base}{i}")
            
            # With years
            for year in self.YEARS:
                passwords.add(f"{base}{year}")
            
            # With suffixes
            for suffix in self.SUFFIXES:
                passwords.add(f"{base}{suffix}")
        
        # Add numeric patterns
        for i in range(100000):
            passwords.add(str(i))
            passwords.add(str(i).zfill(4))
            passwords.add(str(i).zfill(6))
            passwords.add(str(i).zfill(8))
        
        # Keyboard patterns
        keyboard_patterns = [
            'qwerty', 'qwertyuiop', 'asdfgh', 'asdfghjkl', 'zxcvbn', 'zxcvbnm',
            '123qwe', 'qwe123', 'qweasd', 'asdzxc', '1qaz2wsx', '2wsx3edc',
            'qazwsx', 'wsxqaz', 'password', 'passw0rd', 'p@ssword', 'p@ssw0rd'
        ]
        passwords.update(keyboard_patterns)
        
        # Limit to top N
        passwords = set(list(passwords)[:top])
        
        output_path = output_path or str(self.output_dir / "wifi_common.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def mega(self, output_path: str = None) -> str:
        """Generate mega wordlist combining all sources"""
        passwords = set()
        
        # Add all common passwords
        for base in self.COMMON_BASES:
            passwords.add(base)
            passwords.add(base.upper())
            passwords.add(base.lower())
            passwords.add(base.capitalize())
            
            # All number combinations
            for i in range(10000):
                passwords.add(f"{base}{i}")
            
            # All years
            for year in self.YEARS:
                passwords.add(f"{base}{year}")
            
            # All suffixes
            for suffix in self.SUFFIXES:
                passwords.add(f"{base}{suffix}")
        
        # Numeric patterns
        for i in range(1000000):
            passwords.add(str(i))
        
        # Keyboard patterns
        keyboard = ['qwerty', 'asdfgh', 'zxcvbn', '123456', '12345678']
        for k in keyboard:
            passwords.add(k)
            for i in range(1000):
                passwords.add(f"{k}{i}")
        
        output_path = output_path or str(self.output_dir / "mega_wordlist.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def generate_targeted(self, essid: str) -> str:
        """Generate targeted wordlist for specific network"""
        return self.from_essid(essid, variations=True)
    
    def rules_based(self, base_wordlist: str, rules: List[str],
                    output_path: str = None) -> str:
        """Apply rules to wordlist"""
        passwords = set()
        
        with open(base_wordlist, 'r') as f:
            for line in f:
                word = line.strip()
                if not word:
                    continue
                
                passwords.add(word)
                
                for rule in rules:
                    if rule == 'upper':
                        passwords.add(word.upper())
                    elif rule == 'lower':
                        passwords.add(word.lower())
                    elif rule == 'capitalize':
                        passwords.add(word.capitalize())
                    elif rule == 'reverse':
                        passwords.add(word[::-1])
                    elif rule == 'leet':
                        passwords.add(self._to_leet(word))
                    elif rule == 'double':
                        passwords.add(word + word)
                    elif rule.startswith('append:'):
                        suffix = rule.split(':')[1]
                        passwords.add(word + suffix)
                    elif rule.startswith('prepend:'):
                        prefix = rule.split(':')[1]
                        passwords.add(prefix + word)
        
        output_path = output_path or str(self.output_dir / "rules_wordlist.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def combinator(self, wordlist1: str, wordlist2: str,
                   output_path: str = None) -> str:
        """Combine two wordlists"""
        passwords = set()
        
        words1 = set()
        words2 = set()
        
        with open(wordlist1, 'r') as f:
            words1 = {line.strip() for line in f if line.strip()}
        
        with open(wordlist2, 'r') as f:
            words2 = {line.strip() for line in f if line.strip()}
        
        # Combine all ways
        for w1 in words1:
            for w2 in words2:
                passwords.add(w1 + w2)
                passwords.add(w2 + w1)
                passwords.add(w1 + '_' + w2)
                passwords.add(w2 + '_' + w1)
        
        output_path = output_path or str(self.output_dir / "combined_wordlist.txt")
        self._write_wordlist(passwords, output_path)
        
        return output_path
    
    def mask_attack(self, mask: str, output_path: str = None) -> str:
        """Generate passwords from mask"""
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
        
        # Generate all combinations
        output_path = output_path or str(self.output_dir / "mask_wordlist.txt")
        
        count = 0
        with open(output_path, 'w') as f:
            for combo in itertools.product(*charsets):
                f.write(''.join(combo) + '\n')
                count += 1
        
        self.stats['wordlists_generated'] += 1
        self.stats['total_passwords'] += count
        
        return output_path
    
    def _to_leet(self, text: str) -> str:
        """Convert to leet speak"""
        replacements = {
            'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5',
            't': '7', 'l': '1', 'b': '8', 'g': '9'
        }
        
        result = text.lower()
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result
    
    def _write_wordlist(self, passwords: set, output_path: str):
        """Write passwords to file"""
        with open(output_path, 'w') as f:
            for pwd in sorted(passwords):
                f.write(pwd + '\n')
        
        self.stats['wordlists_generated'] += 1
        self.stats['total_passwords'] += len(passwords)
    
    def get_stats(self) -> Dict:
        """Get generation statistics"""
        return self.stats.copy()


if __name__ == '__main__':
    gen = WordlistGenerator()
    
    print("Generating wordlists...")
    
    # Generate common wordlist
    output = gen.common()
    print(f"Common wordlist: {output}")
    
    # Generate from ESSID
    output = gen.from_essid("MyWiFi")
    print(f"ESSID wordlist: {output}")
    
    print(f"Stats: {gen.get_stats()}")
