#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3RMUXK1NG WiFi Cracker PRO - AI Cracker Module"""

import os
import json
import random
from typing import Dict, List, Optional

class AICracker:
    def __init__(self):
        self.models = {}
        self.stats = {'passwords_generated': 0}
    
    def generate_wordlist(self, prompt: str, output_path: str, count: int = 10000) -> str:
        """AI-powered wordlist generation based on prompt"""
        passwords = set()
        
        # Extract keywords from prompt
        keywords = self._extract_keywords(prompt)
        
        # Generate passwords based on patterns
        for keyword in keywords:
            # Common patterns
            patterns = [
                keyword,
                keyword.lower(),
                keyword.upper(),
                keyword.capitalize(),
                f"{keyword}123",
                f"{keyword}1234",
                f"{keyword}!",
                f"{keyword}@",
                f"{keyword}2024",
                f"{keyword}2025",
            ]
            passwords.update(patterns)
        
        # Add variations
        for pwd in list(passwords):
            for i in range(100):
                passwords.add(f"{pwd}{i}")
        
        # Limit to count
        passwords = set(list(passwords)[:count])
        
        # Write to file
        with open(output_path, 'w') as f:
            for pwd in sorted(passwords):
                f.write(pwd + '\n')
        
        self.stats['passwords_generated'] += len(passwords)
        return output_path
    
    def _extract_keywords(self, prompt: str) -> List[str]:
        """Extract keywords from prompt"""
        # Simple keyword extraction
        words = prompt.lower().split()
        keywords = []
        
        for word in words:
            if len(word) > 2 and word not in ['the', 'and', 'for', 'with', 'from']:
                keywords.append(word.capitalize())
        
        return keywords[:5] if keywords else ['Password', 'Admin', 'Wifi']
    
    def predict_password(self, context: Dict) -> List[str]:
        """Predict likely passwords based on context"""
        predictions = []
        
        essid = context.get('essid', '')
        vendor = context.get('vendor', '')
        
        if essid:
            predictions.extend([
                essid,
                f"{essid}123",
                f"{essid}2024",
                essid.lower(),
                essid.upper(),
            ])
        
        if vendor:
            vendor_lower = vendor.lower().replace('-', '').replace(' ', '')
            predictions.extend([
                f"{vendor_lower}",
                f"{vendor_lower}123",
                f"{vendor_lower}admin",
                f"admin{vendor_lower}",
            ])
        
        # Common patterns
        predictions.extend([
            'password', 'admin', 'wifi123', 'router123',
            '12345678', 'password123', 'admin123'
        ])
        
        return list(set(predictions))[:50]
    
    def analyze_password(self, password: str) -> Dict:
        """Analyze password strength and patterns"""
        analysis = {
            'length': len(password),
            'has_upper': any(c.isupper() for c in password),
            'has_lower': any(c.islower() for c in password),
            'has_digit': any(c.isdigit() for c in password),
            'has_special': any(not c.isalnum() for c in password),
            'patterns': [],
            'strength': 0
        }
        
        # Detect patterns
        if password.isdigit():
            analysis['patterns'].append('numeric')
        if password.isalpha():
            analysis['patterns'].append('alpha')
        if password.lower() in ['password', 'admin', 'wifi', 'router']:
            analysis['patterns'].append('common_word')
        if any(year in password for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
            analysis['patterns'].append('year_pattern')
        
        # Calculate strength
        score = 0
        if analysis['length'] >= 8: score += 1
        if analysis['length'] >= 12: score += 1
        if analysis['has_upper']: score += 1
        if analysis['has_lower']: score += 1
        if analysis['has_digit']: score += 1
        if analysis['has_special']: score += 2
        if 'common_word' in analysis['patterns']: score -= 2
        
        analysis['strength'] = max(0, min(5, score))
        
        return analysis
