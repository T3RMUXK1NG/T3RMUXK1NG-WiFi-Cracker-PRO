#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Report Generator Module"""

import os
import json
from datetime import datetime
from typing import Dict, List

class ReportGenerator:
    def __init__(self):
        self.output_dir = "/home/z/my-project/download/RS-WiFi-Cracker-PRO/reports"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate(self, results: Dict, format: str = 'json', output: str = None):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = output or f"{self.output_dir}/report_{timestamp}"
        
        if format == 'json':
            output += '.json'
            with open(output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        
        elif format == 'html':
            output += '.html'
            html = self._generate_html(results)
            with open(output, 'w') as f:
                f.write(html)
        
        elif format == 'markdown':
            output += '.md'
            md = self._generate_markdown(results)
            with open(output, 'w') as f:
                f.write(md)
        
        elif format == 'csv':
            output += '.csv'
            csv = self._generate_csv(results)
            with open(output, 'w') as f:
                f.write(csv)
        
        return output
    
    def _generate_html(self, results: Dict) -> str:
        cracked = sum(1 for r in results.values() if r.get('success'))
        
        return f'''<!DOCTYPE html>
<html><head><title>RS WiFi Cracker Report</title>
<style>body{{font-family:Arial;background:#1a1a2e;color:#eee;padding:20px;}}
table{{width:100%;border-collapse:collapse;margin:20px 0;}}
th,td{{padding:10px;border:1px solid #333;text-align:left;}}
th{{background:#00d4ff;color:#000;}}.success{{color:#0f0;}}.failed{{color:#f00;}}</style>
</head><body><h1>RS WiFi Cracker PRO Report</h1>
<p>Generated: {datetime.now().isoformat()}</p>
<p>Total: {len(results)} | Cracked: {cracked}</p>
<table><tr><th>BSSID</th><th>ESSID</th><th>Status</th><th>Password</th><th>Method</th></tr>
{self._html_rows(results)}</table></body></html>'''
    
    def _html_rows(self, results: Dict) -> str:
        rows = ''
        for bssid, r in results.items():
            status = 'success' if r.get('success') else 'failed'
            password = r.get('password', '-') or '-'
            rows += f'<tr><td>{bssid}</td><td>{r.get("essid","")}</td>'
            rows += f'<td class="{status}">{status.upper()}</td>'
            rows += f'<td>{password}</td><td>{r.get("method","")}</td></tr>'
        return rows
    
    def _generate_markdown(self, results: Dict) -> str:
        md = f'''# RS WiFi Cracker PRO Report

Generated: {datetime.now().isoformat()}

## Summary
- Total Networks: {len(results)}
- Cracked: {sum(1 for r in results.values() if r.get('success'))}

## Results

| BSSID | ESSID | Status | Password | Method |
|-------|-------|--------|----------|--------|
'''
        for bssid, r in results.items():
            status = '✓ Cracked' if r.get('success') else '✗ Failed'
            md += f"| {bssid} | {r.get('essid','')} | {status} | {r.get('password','-')} | {r.get('method','')} |\n"
        
        return md
    
    def _generate_csv(self, results: Dict) -> str:
        csv = 'BSSID,ESSID,Status,Password,Method,Time\n'
        for bssid, r in results.items():
            status = 'cracked' if r.get('success') else 'failed'
            csv += f'{bssid},{r.get("essid","")},{status},{r.get("password","")},{r.get("method","")},{r.get("time_taken",0)}\n'
        return csv
