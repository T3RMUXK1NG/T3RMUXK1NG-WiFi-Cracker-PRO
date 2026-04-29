#!/bin/bash
# Quick WiFi Scan Script
# RS WiFi Cracker PRO

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              RS WiFi Cracker PRO - Quick Scan                     ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo $0"
    exit 1
fi

# Find wireless interface
IFACE=$(iw dev | grep Interface | awk '{print $2}' | head -1)

if [ -z "$IFACE" ]; then
    echo "[!] No wireless interface found"
    exit 1
fi

echo "[*] Using interface: $IFACE"

# Set monitor mode
echo "[*] Setting monitor mode..."
airmon-ng check kill >/dev/null 2>&1
ip link set $IFACE down
iw dev $IFACE set type monitor
ip link set $IFACE up

# Scan
echo "[*] Scanning for 30 seconds..."
timeout 30 airodump-ng $IFACE --output-format csv -w /tmp/quick_scan

# Show results
if [ -f "/tmp/quick_scan-01.csv" ]; then
    echo ""
    echo "[+] Scan Results:"
    cat /tmp/quick_scan-01.csv
fi

# Cleanup
rm -f /tmp/quick_scan-*

echo ""
echo "[+] Done!"
