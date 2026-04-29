#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS WiFi Cracker PRO - Interface Manager Utility
Network interface management
"""

import os
import re
import subprocess
from typing import List, Dict, Optional


class InterfaceManager:
    """WiFi Interface Management"""
    
    def __init__(self):
        self.interfaces: List[Dict] = []
        self.selected: Optional[str] = None
    
    def list_wireless(self) -> List[Dict]:
        """List all wireless interfaces"""
        self.interfaces = []
        
        try:
            # Get interfaces from /sys/class/net
            net_dir = '/sys/class/net'
            if os.path.exists(net_dir):
                for iface in os.listdir(net_dir):
                    # Check if wireless
                    wireless_path = os.path.join(net_dir, iface, 'wireless')
                    if os.path.exists(wireless_path):
                        iface_info = self._get_interface_info(iface)
                        self.interfaces.append(iface_info)
        
        except Exception:
            pass
        
        # Fallback: use iwconfig
        if not self.interfaces:
            self.interfaces = self._list_iwconfig()
        
        return self.interfaces
    
    def _get_interface_info(self, name: str) -> Dict:
        """Get detailed interface info"""
        info = {
            'name': name,
            'mode': 'Managed',
            'status': 'down',
            'mac': '',
            'ip': '',
            'connected': False,
            'essid': ''
        }
        
        try:
            # Get status
            operstate = f'/sys/class/net/{name}/operstate'
            if os.path.exists(operstate):
                with open(operstate, 'r') as f:
                    info['status'] = f.read().strip()
            
            # Get MAC
            address = f'/sys/class/net/{name}/address'
            if os.path.exists(address):
                with open(address, 'r') as f:
                    info['mac'] = f.read().strip()
            
            # Get IP
            result = subprocess.run(['ip', 'addr', 'show', name], capture_output=True, text=True)
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                info['ip'] = match.group(1)
            
            # Get mode
            result = subprocess.run(['iwconfig', name], capture_output=True, text=True)
            if 'Mode:Monitor' in result.stdout:
                info['mode'] = 'Monitor'
            
            # Get connected ESSID
            match = re.search(r'ESSID:"([^"]*)"', result.stdout)
            if match:
                info['essid'] = match.group(1)
                info['connected'] = True
        
        except Exception:
            pass
        
        return info
    
    def _list_iwconfig(self) -> List[Dict]:
        """List interfaces using iwconfig"""
        interfaces = []
        
        try:
            result = subprocess.run(['iwconfig'], capture_output=True, text=True)
            
            current = None
            for line in result.stdout.split('\n'):
                if 'IEEE 802.11' in line:
                    match = re.match(r'^(\S+)', line)
                    if match:
                        current = {
                            'name': match.group(1),
                            'mode': 'Monitor' if 'Mode:Monitor' in line else 'Managed',
                            'status': 'up' if 'UP' in line else 'down'
                        }
                        interfaces.append(current)
        
        except FileNotFoundError:
            pass
        
        return interfaces
    
    def select(self, interfaces: List[Dict] = None) -> Optional[str]:
        """Select interface interactively"""
        if interfaces is None:
            interfaces = self.interfaces
        
        if not interfaces:
            print("No wireless interfaces found!")
            return None
        
        print("\nAvailable Interfaces:")
        for i, iface in enumerate(interfaces, 1):
            mode_color = '\033[95m' if iface['mode'] == 'Monitor' else '\033[0m'
            status_color = '\033[92m' if iface['status'] == 'up' else '\033[91m'
            
            print(f"  {i}. {iface['name']} "
                  f"{status_color}[{iface['status']}]{mode_color} [{iface['mode']}]{iface.get('essid', '')}")
        
        try:
            choice = int(input("\nSelect interface: "))
            if 1 <= choice <= len(interfaces):
                self.selected = interfaces[choice - 1]['name']
                return self.selected
        except (ValueError, IndexError):
            pass
        
        return None
    
    def enable_monitor_mode(self, interface: str = None) -> bool:
        """Enable monitor mode"""
        interface = interface or self.selected
        if not interface:
            return False
        
        # Kill interfering processes
        try:
            subprocess.run(['sudo', 'airmon-ng', 'check', 'kill'],
                         capture_output=True, timeout=10)
        except:
            pass
        
        commands = [
            ['sudo', 'ip', 'link', 'set', interface, 'down'],
            ['sudo', 'iw', 'dev', interface, 'set', 'type', 'monitor'],
            ['sudo', 'ip', 'link', 'set', interface, 'up'],
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                if result.returncode != 0:
                    # Try airmon-ng
                    return self._enable_monitor_airmon(interface)
            except:
                pass
        
        # Verify
        return self._verify_monitor_mode(interface)
    
    def _enable_monitor_airmon(self, interface: str) -> bool:
        """Enable monitor mode using airmon-ng"""
        try:
            result = subprocess.run(
                ['sudo', 'airmon-ng', 'start', interface],
                capture_output=True, text=True, timeout=30
            )
            
            # Check for new monitor interface
            if 'monitor mode enabled' in result.stdout.lower():
                # Get new interface name
                match = re.search(r'monitor mode enabled on (\S+)', result.stdout.lower())
                if match:
                    self.selected = match.group(1)
                return True
        except:
            pass
        
        return False
    
    def _verify_monitor_mode(self, interface: str) -> bool:
        """Verify interface is in monitor mode"""
        try:
            result = subprocess.run(['iwconfig', interface], capture_output=True, text=True)
            return 'Mode:Monitor' in result.stdout
        except:
            return False
    
    def disable_monitor_mode(self, interface: str = None) -> bool:
        """Disable monitor mode"""
        interface = interface or self.selected
        if not interface:
            return False
        
        commands = [
            ['sudo', 'ip', 'link', 'set', interface, 'down'],
            ['sudo', 'iw', 'dev', interface, 'set', 'type', 'managed'],
            ['sudo', 'ip', 'link', 'set', interface, 'up'],
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=10)
            except:
                pass
        
        # Restart NetworkManager
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'],
                         capture_output=True, timeout=10)
        except:
            pass
        
        return True
    
    def set_channel(self, interface: str, channel: int) -> bool:
        """Set interface channel"""
        interface = interface or self.selected
        if not interface:
            return False
        
        try:
            subprocess.run(
                ['sudo', 'iwconfig', interface, 'channel', str(channel)],
                capture_output=True, timeout=5
            )
            return True
        except:
            return False
    
    def change_mac(self, interface: str, new_mac: str) -> bool:
        """Change MAC address"""
        interface = interface or self.selected
        if not interface:
            return False
        
        commands = [
            ['sudo', 'ip', 'link', 'set', interface, 'down'],
            ['sudo', 'ip', 'link', 'set', interface, 'address', new_mac],
            ['sudo', 'ip', 'link', 'set', interface, 'up'],
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=10)
            except:
                return False
        
        return True
    
    def random_mac(self, interface: str = None) -> bool:
        """Set random MAC address"""
        import random
        
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        
        new_mac = ':'.join(map(lambda x: "%02x" % x, mac))
        
        return self.change_mac(interface or self.selected, new_mac)
    
    def get_monitor_interface(self, interface: str = None) -> Optional[str]:
        """Get or create monitor interface"""
        interface = interface or self.selected
        
        if self._verify_monitor_mode(interface):
            return interface
        
        if self.enable_monitor_mode(interface):
            return self.selected
        
        return None


if __name__ == '__main__':
    mgr = InterfaceManager()
    interfaces = mgr.list_wireless()
    
    print(f"Found {len(interfaces)} wireless interfaces:")
    for iface in interfaces:
        print(f"  {iface}")
