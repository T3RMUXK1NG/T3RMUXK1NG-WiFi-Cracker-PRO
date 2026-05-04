<div align="center">

# 📡 T3RMUXK1NG WiFi Cracker PRO

**Advanced WiFi security testing suite with AI-powered cracking, GPU acceleration, and 8+ attack modules**

[![Language](https://img.shields.io/badge/Language-Python-yellow?logo=python)](https://python.org)
[![Version](https://img.shields.io/badge/Version-3.0-red)](https://github.com/T3RMUXK1NG/T3RMUXK1NG-WiFi-Cracker-PRO/releases)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-blue?logo=linux)](https://www.kali.org)
[![YouTube](https://img.shields.io/badge/YouTube-T3rmuxk1ng-red?logo=youtube)](https://youtube.com/@T3rmuxk1ng)
[![License](https://img.shields.io/badge/License-Educational-yellow)](./LICENSE)

*Built with 💚 by [T3rmuxk1ng](https://youtube.com/@T3rmuxk1ng)*

</div>

---

## 🎬 Demo & Tutorials

📺 **Watch on YouTube**: [https://youtube.com/@T3rmuxk1ng](https://youtube.com/@T3rmuxk1ng)

Subscribe for WiFi hacking tutorials, security tool demos, and exclusive walkthroughs!

---

## ✨ Features

### 🎯 Core Attack Modules

| Module | Description |
|--------|-------------|
| **Network Scanner** | Advanced WiFi network discovery with real-time monitoring |
| **Handshake Capture** | Multi-target simultaneous handshake capture |
| **Password Cracker** | Dictionary, brute-force, and rule-based attacks |
| **WPS Attack Suite** | Pixie Dust, PIN brute-force, and null PIN attacks |
| **Evil Twin** | Full rogue AP with captive portal and credential harvesting |
| **Deauth Attack** | Targeted and broadcast deauthentication attacks |
| **PMKID Attack** | Offline attack without client interaction |
| **Karma Attack** | Auto-connect probing and exploitation |

### 🚀 Advanced Features

- **GPU-Accelerated Cracking** — Hashcat integration for fast hash cracking
- **AI-Powered Password Generation** — Smart wordlist creation
- **Distributed Cracking** — Across multiple machines
- **Real-Time Dashboard** — Live monitoring of attacks
- **Report Generation** — Auto-generated security audit reports
- **Plugin System** — Extensible architecture for custom modules
- **MITM Module** — Man-in-the-middle attack capabilities

---

## 🛠️ Requirements

| Requirement | Details |
|-------------|---------|
| OS | Kali Linux 2024.x (recommended) |
| Python | 3.11+ |
| WiFi Adapter | Must support monitor mode & packet injection |
| Privileges | Root (sudo) required |

---

## 🚀 Installation

### Quick Install
```bash
git clone https://github.com/T3RMUXK1NG/T3RMUXK1NG-WiFi-Cracker-PRO.git
cd T3RMUXK1NG-WiFi-Cracker-PRO
chmod +x install.sh
sudo ./install.sh
python3 t3rmuxk1ng_wifi_pro.py
```

### Manual Install
```bash
pip3 install -r requirements.txt 2>/dev/null || pip3 install scapy colorama requests
sudo python3 t3rmuxk1ng_wifi_pro.py
```

---

## 📖 Usage

### Interactive Mode
```bash
sudo python3 t3rmuxk1ng_wifi_pro.py
```

### CLI Mode
```bash
# Scan for networks
sudo python3 t3rmuxk1ng_wifi_pro.py --interface wlan0 --scan

# WPS attack on specific target
sudo python3 t3rmuxk1ng_wifi_pro.py --interface wlan0 --attack wps --target AA:BB:CC:DD:EE:FF

# Evil Twin AP
sudo python3 t3rmuxk1ng_wifi_pro.py --interface wlan0 --evil-twin --ssid "FreeWiFi"

# PMKID attack
sudo python3 t3rmuxk1ng_wifi_pro.py --interface wlan0 --attack pmkid --target AA:BB:CC:DD:EE:FF
```

---

## 📁 Project Structure

```
T3RMUXK1NG-WiFi-Cracker-PRO/
├── t3rmuxk1ng_wifi_pro.py          # Main entry point
├── install.sh              # Installation script
├── core/                   # Core functionality
│   ├── scanner.py          # Network scanning
│   ├── capturer.py         # Handshake capture
│   ├── cracker.py          # Password cracking
│   ├── attacker.py         # Attack modules
│   ├── monitor.py          # Real-time monitoring
│   ├── dashboard.py        # Dashboard UI
│   └── database.py         # SQLite storage
├── modules/                # Feature modules
│   ├── wps_attack.py       # WPS attacks
│   ├── evil_twin.py        # Evil Twin AP
│   ├── pmkid.py            # PMKID attacks
│   ├── deauth.py           # Deauthentication
│   ├── karma.py            # Karma attacks
│   ├── mitm.py             # Man-in-the-middle
│   ├── ai_cracker.py       # AI-powered cracking
│   ├── hashcat_bridge.py   # GPU acceleration
│   └── report_gen.py       # Report generation
├── utils/                  # Utilities
│   ├── interface.py        # Interface management
│   ├── wordlist.py         # Wordlist generation
│   ├── display.py          # Display/UI helpers
│   ├── logger.py           # Logging system
│   └── config.py           # Configuration
├── plugins/                # Plugin system
├── config/                 # Configuration files
└── data/                   # Data storage
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](./.github/README.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

**This tool is for AUTHORIZED SECURITY TESTING and EDUCATIONAL purposes only.**

- Only use on networks you own or have explicit written permission to test
- Unauthorized access to computer networks is illegal in most jurisdictions
- The developers are not liable for any misuse or damage caused
- Always comply with local laws and regulations

---

## 📺 YouTube

📺 **T3rmuxk1ng** — [https://youtube.com/@T3rmuxk1ng](https://youtube.com/@T3rmuxk1ng)

Subscribe for:
- WiFi hacking tutorials & demos
- Network security walkthroughs
- Cybersecurity tips & tricks
- Exclusive tool releases

---

<div align="center">

**Built with 💚 by [T3rmuxk1ng](https://youtube.com/@T3rmuxk1ng)**

⭐ If you like this project, give it a star!

</div>
