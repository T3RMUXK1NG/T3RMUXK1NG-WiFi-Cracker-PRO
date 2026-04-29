#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Wordlist Generator"""
import os
import itertools
from typing import List, Optional
from datetime import datetime


class WordlistGenerator:
    """Custom wordlist generator"""
    
    COMMON_PASSWORDS = [
        "password", "admin", "123456", "qwerty", "letmein", "welcome",
        "monkey", "dragon", "master", "12345678", "password123",
        "admin123", "root", "toor", "kali", "test", "test123",
        "password1", "qwerty123", "111111", "123123", "football",
        "baseball", "iloveyou", "trustno1", "sunshine", "princess",
        "welcome1", "shadow", "superman", "michael", "passw0rd",
    ]
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def generate(self, essid: str = "", keywords: List[str] = None,
                 output_file: str = None, max_length: int = 16,
                 min_length: int = 8, include_common: bool = True) -> str:
        """Generate custom wordlist"""
        output_file = output_file or f"/tmp/wordlist_{essid or 'custom'}.txt"
        keywords = keywords or []
        passwords = set()
        
        if self.logger:
            self.logger.info(f"Generating wordlist for {essid or 'custom'}...")
        
        # Add common passwords
        if include_common:
            passwords.update(self.COMMON_PASSWORDS)
        
        # Add ESSID variations
        if essid:
            passwords.add(essid)
            passwords.add(essid.lower())
            passwords.add(essid.upper())
            passwords.add(essid.replace(" ", ""))
            passwords.add(essid.replace(" ", "_"))
            passwords.add(essid.replace(" ", "-"))
            
            # ESSID with numbers
            for num in ["123", "1234", "12345", "@123", "!123", "1", "01"]:
                passwords.add(essid + num)
                passwords.add(essid.lower() + num)
            
            # ESSID with year
            for year in ["2024", "2025", "2026", "2023"]:
                passwords.add(essid + year)
                passwords.add(essid + "@" + year)
        
        # Add keyword variations
        for kw in keywords:
            passwords.add(kw)
            passwords.add(kw.lower())
            passwords.add(kw.upper())
            passwords.add(kw.capitalize())
            
            for suffix in ["123", "1234", "@123", "!", "@"]:
                passwords.add(kw + suffix)
                passwords.add(kw.lower() + suffix)
        
        # Generate combinations
        if keywords and len(keywords) >= 2:
            for combo in itertools.product(keywords[:3], repeat=2):
                passwords.add(''.join(combo))
                passwords.add(''.join(combo).lower())
        
        # Filter by length
        passwords = {p for p in passwords if min_length <= len(p) <= max_length}
        
        # Write to file
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            for p in sorted(passwords):
                f.write(p + '\n')
        
        if self.logger:
            self.logger.success(f"Generated {len(passwords)} passwords -> {output_file}")
        
        return output_file
    
    def generate_mutation(self, base_word: str, output_file: str = None) -> str:
        """Generate mutations of a word"""
        output_file = output_file or f"/tmp/mutation_{base_word}.txt"
        mutations = set()
        
        # Basic mutations
        mutations.add(base_word)
        mutations.add(base_word.lower())
        mutations.add(base_word.upper())
        mutations.add(base_word.capitalize())
        mutations.add(base_word.swapcase())
        
        # Leet speak
        leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        leet = base_word.lower()
        for char, replacement in leet_map.items():
            leet = leet.replace(char, replacement)
        mutations.add(leet)
        
        # Reverse
        mutations.add(base_word[::-1])
        
        # Double
        mutations.add(base_word * 2)
        
        # Numbers
        for i in range(100):
            mutations.add(base_word + str(i))
            mutations.add(str(i) + base_word)
        
        # Special chars
        for char in ['!', '@', '#', '$', '%']:
            mutations.add(base_word + char)
            mutations.add(char + base_word)
        
        with open(output_file, 'w') as f:
            for m in sorted(mutations):
                f.write(m + '\n')
        
        if self.logger:
            self.logger.success(f"Generated {len(mutations)} mutations")
        
        return output_file
    
    def merge_wordlists(self, wordlists: List[str], output_file: str) -> str:
        """Merge multiple wordlists"""
        all_passwords = set()
        
        for wl in wordlists:
            if os.path.exists(wl):
                with open(wl, 'r', errors='ignore') as f:
                    for line in f:
                        all_passwords.add(line.strip())
        
        with open(output_file, 'w') as f:
            for p in sorted(all_passwords):
                f.write(p + '\n')
        
        if self.logger:
            self.logger.success(f"Merged {len(all_passwords)} unique passwords")
        
        return output_file
    
    def deduplicate(self, wordlist: str, output_file: str = None) -> str:
        """Remove duplicates from wordlist"""
        output_file = output_file or wordlist + ".dedup"
        passwords = set()
        
        with open(wordlist, 'r', errors='ignore') as f:
            for line in f:
                passwords.add(line.strip())
        
        with open(output_file, 'w') as f:
            for p in sorted(passwords):
                f.write(p + '\n')
        
        return output_file
