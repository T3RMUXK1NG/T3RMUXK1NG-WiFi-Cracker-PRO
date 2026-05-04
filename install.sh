#!/bin/bash
#
#  RS WiFi Cracker PRO - Installation Script
#  T3rmuxk1ng Private Release
#

set -e

R='\033[91m'
G='\033[92m'
Y='\033[93m'
C='\033[96m'
W='\033[97m'
RESET='\033[0m'

echo -e "${C}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          RS WiFi Cracker PRO - Installation Script                ║"
echo "║                 T3rmuxk1ng Private Release                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${Y}[!] Run with sudo: sudo bash install.sh${RESET}"
    exit 1
fi

# Install dependencies
echo -e "${C}[*] Installing dependencies...${RESET}"

apt-get update -y
apt-get install -y \
    python3 python3-pip python3-dev \
    aircrack-ng reaver bully hashcat john hydra \
    macchanger wireless-tools iw net-tools \
    hostapd dnsmasq nmap tshark \
    git wget curl tmux htop \
    bettercap hcxdumptool hcxtools \
    2>/dev/null || true

# Python packages
echo -e "${C}[*] Installing Python packages...${RESET}"
pip3 install --upgrade pip
pip3 install scapy requests colorama tqdm rich tabulate psutil netifaces 2>/dev/null || true

# Create directories
echo -e "${C}[*] Creating directories...${RESET}"
mkdir -p /opt/t3rmuxk1ng-wifi-pro
mkdir -p /usr/share/wordlists/rs-wordlists
mkdir -p /var/log/t3rmuxk1ng-wifi-pro
mkdir -p ~/.config/t3rmuxk1ng-wifi-pro

# Copy files
echo -e "${C}[*] Installing RS WiFi Cracker PRO...${RESET}"
cp -r . /opt/t3rmuxk1ng-wifi-pro/
chmod +x /opt/t3rmuxk1ng-wifi-pro/t3rmuxk1ng_wifi_pro.py

# Create symlink
ln -sf /opt/t3rmuxk1ng-wifi-pro/t3rmuxk1ng_wifi_pro.py /usr/local/bin/t3rmuxk1ng-wifi-pro 2>/dev/null || true

# Generate wordlists
echo -e "${C}[*] Generating wordlists...${RESET}"
python3 -c "
from utils.wordlist import WordlistGenerator
gen = WordlistGenerator()
gen.common('/usr/share/wordlists/rs-wordlists/wifi_common.txt', 500000)
print('Wordlist generated')
" 2>/dev/null || echo "Wordlist generation skipped"

# Create alias
echo "alias rs-wifi='sudo python3 /opt/t3rmuxk1ng-wifi-pro/t3rmuxk1ng_wifi_pro.py'" >> /etc/bash.bashrc 2>/dev/null || true

echo -e "${G}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              INSTALLATION COMPLETE!                               ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""
echo -e "${G}Usage:${RESET}"
echo -e "  ${W}t3rmuxk1ng-wifi-pro${RESET}              # Interactive mode"
echo -e "  ${W}sudo python3 /opt/t3rmuxk1ng-wifi-pro/t3rmuxk1ng_wifi_pro.py${RESET}"
echo ""
echo -e "${G}Wordlists:${RESET}"
echo -e "  ${W}/usr/share/wordlists/rs-wordlists/wifi_common.txt${RESET}"
echo ""
echo -e "${Y}Disclaimer: For authorized security testing only!${RESET}"
