#!/bin/bash
# RS WiFi Cracker PRO v4.0.1 - Installation Script
# T3rmuxk1ng Private Release

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          RS WiFi Cracker PRO v4.0.1 - Ultimate Edition            ║"
echo "║                    T3rmuxk1ng Private Release                      ║"
echo "║                      Production Ready Build                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run as root: sudo ./install.sh"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi
echo "[*] Detected OS: $OS"

# Update system
echo "[*] Updating system..."
apt-get update -qq

# Install dependencies
DEPS=(
    python3 python3-pip python3-dev python3-venv
    aircrack-ng reaver bully hashcat john hydra
    macchanger wireless-tools iw net-tools
    hostapd dnsmasq nmap tshark wireshark
    bettercap hcxdumptool hcxtools
    git wget curl tmux htop pciutils usbutils
)

for dep in "${DEPS[@]}"; do
    echo "[*] Installing $dep..."
    apt-get install -y -qq "$dep" 2>/dev/null || echo "[!] $dep already installed"
done

# Install Python packages
echo "[*] Installing Python packages..."
pip3 install -q scapy requests flask colorama tabulate psutil netaddr 2>/dev/null || true

# Create directories
echo "[*] Creating directories..."
mkdir -p /opt/rs-wifi-pro-v4
mkdir -p /var/log/rs-wifi-pro
mkdir -p /var/lib/rs-wifi-pro
mkdir -p /tmp/rs-wifi-captures
mkdir -p /tmp/rs-wifi-reports
mkdir -p /usr/share/wordlists/rs-wordlists

# Install main script
echo "[*] Installing RS WiFi Cracker PRO..."
cp rs_wifi_pro.py /opt/rs-wifi-pro-v4/
cp -r core modules utils config 2>/dev/null || true

# Create symlink
ln -sf /opt/rs-wifi-pro-v4/rs_wifi_pro.py /usr/local/bin/rs-wifi-pro
chmod +x /opt/rs-wifi-pro-v4/rs_wifi_pro.py
chmod +x /usr/local/bin/rs-wifi-pro

# Generate wordlist
echo "[*] Generating wordlists..."
if [ ! -f /usr/share/wordlists/rs-wordlists/common.txt ]; then
    cat > /usr/share/wordlists/rs-wordlists/common.txt << 'WORDLIST'
12345678
password
password123
admin
admin123
qwerty
qwerty123
letmein
welcome
monkey
dragon
master
123456789
1234567890
password1
abc123
111111
baseball
iloveyou
trustno1
sunshine
princess
welcome1
shadow
superman
michael
football
passw0rd
charlie
donald
WORDLIST
fi
echo "Wordlist generated"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              INSTALLATION COMPLETE!                               ║"
echo "║                                                                   ║"
echo "║  RS WiFi Cracker PRO v4.0.1 - Ultimate Edition                   ║"
echo "║  T3rmuxk1ng Private Release                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Usage:"
echo "  rs-wifi-pro              # Interactive mode"
echo "  sudo python3 /opt/rs-wifi-pro-v4/rs_wifi_pro.py"
echo ""
echo "Features:"
echo "  • Network Scanner (airodump, scapy, nmcli)"
echo "  • WPA/WPA2 Handshake Capture"
echo "  • WPS Attack Suite (Pixie Dust, Brute Force)"
echo "  • PMKID Attack"
echo "  • Evil Twin with Captive Portal"
echo "  • Deauthentication Attack"
echo "  • GPU-Accelerated Cracking"
echo ""
echo "Wordlists:"
echo "  /usr/share/wordlists/rs-wordlists/common.txt"
echo ""
echo "For authorized security testing only!"
