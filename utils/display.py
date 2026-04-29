#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RS WiFi Cracker PRO - Display Utility"""

import os

R = '\033[91m'
G = '\033[92m'
Y = '\033[93m'
B = '\033[94m'
M = '\033[95m'
C = '\033[96m'
W = '\033[97m'
RESET = '\033[0m'

class Display:
    def clear(self):
        os.system('clear')
    
    def banner(self):
        print(f"""{R}
╔═══════════════════════════════════════════════════════════════════╗
║{W}      ██████╗ ██████╗ ███████╗    █████╗ ██╗     ██╗   ██╗ █████╗ {R}║
║{W}      ██╔══██╗██╔══██╗██╔════╝   ██╔══██╗██║     ██║   ██║██╔══██╗{R}║
║{W}      ██████╔╝██████╔╝█████╗     ███████║██║     ██║   ██║███████║{R}║
║{W}      ██╔══██╗██╔══██╗██╔══╝     ██╔══██║██║     ╚██╗ ██╔╝██╔══██║{R}║
║{W}      ██║  ██║██████╔╝███████╗   ██║  ██║███████╗ ╚████╔╝ ██║  ██║{R}║
║{W}      ╚═╝  ╚═╝╚═════╝ ╚══════╝   ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝  ╚═╝{R}║
║{C}                        PRO EDITION v3.0{R}                        ║
║{Y}                      T3rmuxk1ng Private{R}                        ║
╚═══════════════════════════════════════════════════════════════════╝{RESET}
""")
    
    def main_menu(self):
        print(f"\n{B}═══════════════════════════════════════════════════{RESET}")
        print(f"{W}  {G}1.{W} Scan Networks          {G}10.{W} Karma Attack")
        print(f"{W}  {G}2.{W} Select Targets         {G}11.{W} MITM Attack")
        print(f"{W}  {G}3.{W} Capture Handshake      {G}12.{W} Auto Attack")
        print(f"{W}  {G}4.{W} Crack Passwords        {G}13.{W} Mass Attack")
        print(f"{W}  {G}5.{W} WPS Attack             {G}14.{W} Web Dashboard")
        print(f"{W}  {G}6.{W} Evil Twin              {G}15.{W} Generate Wordlist")
        print(f"{W}  {G}7.{W} PMKID Attack           {G}16.{W} Generate Report")
        print(f"{W}  {G}8.{W} Deauth Attack          {G}17.{W} Plugins")
        print(f"{W}  {G}9.{W} Karma Attack           {G}18.{W} Settings")
        print(f"{W}  {R}0.{W} Exit                   {G}99.{W} Help")
        print(f"{B}═══════════════════════════════════════════════════{RESET}")
    
    def info(self, msg): print(f"{B}[*]{W} {msg}{RESET}")
    def success(self, msg): print(f"{G}[+]{W} {msg}{RESET}")
    def error(self, msg): print(f"{R}[-]{W} {msg}{RESET}")
    def warning(self, msg): print(f"{Y}[!]{W} {msg}{RESET}")
    def target(self, msg): print(f"{C}[→]{W} {msg}{RESET}")
    
    def section(self, title):
        print(f"\n{M}═══ {title} ═══{RESET}\n")
    
    def menu_item(self, num, text):
        print(f"  {G}{num}.{W} {text}{RESET}")
    
    def table_header(self, columns):
        header = '  '.join(f"{name:<{width}}" for name, width in columns)
        print(f"\n{B}{header}{RESET}")
    
    def table_row(self, values):
        row = '  '.join(str(v) for v in values)
        print(f"{W}{row}{RESET}")
    
    def color(self, color_name):
        colors = {'red': R, 'green': G, 'yellow': Y, 'blue': B, 'magenta': M, 'cyan': C, 'white': W}
        return colors.get(color_name, W)
    
    def help(self):
        print(f"""
{C}RS WiFi Cracker PRO - Help{RESET}

{G}Workflow:{RESET}
  1. Select interface (auto-detected on start)
  2. Scan for networks (Option 1)
  3. Select target(s) (Option 2)
  4. Choose attack method

{G}Attack Methods:{RESET}
  • Handshake Capture - Captures WPA/WPA2 4-way handshake
  • WPS Attack - Pixie Dust and PIN brute force
  • PMKID Attack - Offline attack without clients
  • Evil Twin - Rogue AP with captive portal
  • Deauth - Disconnect clients from network
  • Karma - Exploit auto-connect behavior
  • MITM - Man-in-the-middle attacks

{G}Tips:{RESET}
  • Get close to target for better signal
  • WPS Pixie Dust is fastest (if vulnerable)
  • Use custom wordlists for better results
  • Evil Twin works well with deauth

Press Enter to continue...
""")
        input()
