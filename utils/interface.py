#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Interface Manager"""
import os
import re
import subprocess
import random
from typing import List, Optional
from datetime import datetime


class InterfaceManager:
    """Network interface management"""
    
    VENDOR_OUI = {
        '00:0A': 'Cisco', '00:0B': 'Cisco', '00:0C': 'Cisco', '00:0D': 'Cisco',
        '00:0E': 'Cisco', '00:0F': 'Cisco', '00:10': 'Cisco', '00:11': 'Cisco',
        '00:12': 'Cisco', '00:13': 'Cisco', '00:14': 'Cisco', '00:15': 'Cisco',
        '00:50': 'Intel', '00:1E': 'Intel', '00:1F': 'Intel', '00:22': 'Intel',
        '00:23': 'Intel', '00:24': 'Intel', '00:25': 'Intel', '00:26': 'Intel',
        'DC:A6': 'Raspberry Pi', 'B8:27': 'Raspberry Pi',
        '28:2E': 'Xiaomi', '34:CE': 'Xiaomi', '4C:66': 'Xiaomi', '50:EC': 'Xiaomi',
        '00:26': 'Samsung', '00:27': 'Samsung', 'A4:83': 'Samsung', 'A4:C3': 'Samsung',
        '08:00': 'Dell', '00:06': 'Dell', '00:08': 'Dell', '00:DD': 'Dell',
        'F0:1F': 'Dell', 'F0:4D': 'Dell', 'F0:F6': 'Dell',
    }
    
    def __init__(self, logger=None):
        self.logger = logger
        self.interfaces = []
    
    def list_wireless(self) -> List[dict]:
        """List all wireless interfaces"""
        interfaces = []
        
        # Check /sys/class/net
        net_path = "/sys/class/net"
        if os.path.exists(net_path):
            for iface in os.listdir(net_path):
                wireless_path = os.path.join(net_path, iface, "wireless")
                if os.path.exists(wireless_path):
                    info = self._get_info(iface)
                    if info:
                        interfaces.append(info)
        
        # Alternative using iw
        if not interfaces:
            try:
                result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Interface' in line:
                        iface = line.split()[-1]
                        info = self._get_info(iface)
                        if info:
                            interfaces.append(info)
            except:
                pass
        
        self.interfaces = interfaces
        return interfaces
    
    def _get_info(self, name: str) -> Optional[dict]:
        """Get interface information"""
        try:
            # MAC address
            mac_path = f"/sys/class/net/{name}/address"
            mac = ""
            if os.path.exists(mac_path):
                with open(mac_path, 'r') as f:
                    mac = f.read().strip()
            
            # Status
            operstate_path = f"/sys/class/net/{name}/operstate"
            status = "down"
            if os.path.exists(operstate_path):
                with open(operstate_path, 'r') as f:
                    status = f.read().strip()
            
            # Mode
            mode = "managed"
            try:
                result = subprocess.run(['iw', 'dev', name, 'info'], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'type' in line:
                        mode = line.split()[-1]
                        break
            except:
                pass
            
            # Driver
            driver = ""
            try:
                device_link = f"/sys/class/net/{name}/device/driver"
                if os.path.islink(device_link):
                    driver = os.path.basename(os.readlink(device_link))
            except:
                pass
            
            return {
                'name': name,
                'mac': mac,
                'mode': mode,
                'status': status,
                'vendor': self._get_vendor(mac),
                'driver': driver
            }
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error getting info for {name}: {e}")
            return None
    
    def _get_vendor(self, mac: str) -> str:
        """Get vendor from MAC"""
        if not mac:
            return "Unknown"
        oui = mac[:8].upper()
        for prefix, vendor in self.VENDOR_OUI.items():
            if oui.startswith(prefix.upper()):
                return vendor
        return "Unknown"
    
    def set_monitor_mode(self, interface: str) -> bool:
        """Set interface to monitor mode"""
        if self.logger:
            self.logger.info(f"Setting {interface} to monitor mode...")
        
        try:
            # Kill interfering processes
            subprocess.run(['airmon-ng', 'check', 'kill'], capture_output=True)
            
            # Stop interface
            subprocess.run(['ip', 'link', 'set', interface, 'down'], capture_output=True)
            
            # Set monitor mode
            subprocess.run(['iw', 'dev', interface, 'set', 'type', 'monitor'], capture_output=True)
            
            # Start interface
            subprocess.run(['ip', 'link', 'set', interface, 'up'], capture_output=True)
            
            # Verify
            result = subprocess.run(['iw', 'dev', interface, 'info'], 
                                  capture_output=True, text=True)
            if 'monitor' in result.stdout:
                if self.logger:
                    self.logger.success(f"{interface} in monitor mode")
                return True
            else:
                # Try airmon-ng
                subprocess.run(['airmon-ng', 'start', interface], capture_output=True)
                time.sleep(2)
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to set monitor mode: {e}")
            return False
    
    def set_managed_mode(self, interface: str) -> bool:
        """Set interface to managed mode"""
        if self.logger:
            self.logger.info(f"Setting {interface} to managed mode...")
        
        try:
            subprocess.run(['ip', 'link', 'set', interface, 'down'], capture_output=True)
            subprocess.run(['iw', 'dev', interface, 'set', 'type', 'managed'], capture_output=True)
            subprocess.run(['ip', 'link', 'set', interface, 'up'], capture_output=True)
            
            # Restart NetworkManager
            subprocess.run(['systemctl', 'restart', 'NetworkManager'], capture_output=True)
            
            if self.logger:
                self.logger.success(f"{interface} in managed mode")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to set managed mode: {e}")
            return False
    
    def set_channel(self, interface: str, channel: int) -> bool:
        """Set interface channel"""
        try:
            subprocess.run(['iw', 'dev', interface, 'set', 'channel', str(channel)],
                         capture_output=True)
            return True
        except:
            return False
    
    def change_mac(self, interface: str, new_mac: str) -> bool:
        """Change MAC address"""
        try:
            subprocess.run(['ip', 'link', 'set', interface, 'down'], capture_output=True)
            subprocess.run(['ip', 'link', 'set', interface, 'address', new_mac],
                         capture_output=True)
            subprocess.run(['ip', 'link', 'set', interface, 'up'], capture_output=True)
            
            if self.logger:
                self.logger.success(f"MAC changed to {new_mac}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"MAC change failed: {e}")
            return False
    
    def random_mac(self, interface: str) -> str:
        """Generate and set random MAC"""
        new_mac = "02:%02x:%02x:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        self.change_mac(interface, new_mac)
        return new_mac
    
    def get_current_mac(self, interface: str) -> str:
        """Get current MAC address"""
        try:
            with open(f"/sys/class/net/{interface}/address", 'r') as f:
                return f.read().strip()
        except:
            return ""
    
    def is_monitor_mode(self, interface: str) -> bool:
        """Check if interface is in monitor mode"""
        try:
            result = subprocess.run(['iw', 'dev', interface, 'info'],
                                  capture_output=True, text=True)
            return 'monitor' in result.stdout
        except:
            return False


# Required import
import time
