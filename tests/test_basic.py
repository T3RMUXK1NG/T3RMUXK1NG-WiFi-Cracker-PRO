#!/usr/bin/env python3
"""Basic tests for RS WiFi Cracker PRO"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from core.types import WiFiNetwork, SecurityType, WiFiClient
        from core.scanner import NetworkScanner
        from core.capturer import HandshakeCapturer
        from core.cracker import PasswordCracker
        from core.attacker import DeauthAttacker
        from modules.evil_twin import EvilTwin
        from modules.pmkid import PMKIDAttacker
        from modules.deauth import DeauthAttack
        from modules.wps_attack import WPSAttack
        from modules.karma import KarmaAttack
        from modules.mitm import MITMAttack
        from utils.interface import InterfaceManager
        from utils.wordlist import WordlistGenerator
        from utils.config import Config
        from utils.logger import Logger
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from utils.config import Config
        config = Config()
        assert config.version == "4.0.1"
        assert config.author == "T3rmuxk1ng"
        print("✓ Configuration test passed")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_types():
    """Test data types"""
    try:
        from core.types import WiFiNetwork, SecurityType
        net = WiFiNetwork(
            bssid="AA:BB:CC:DD:EE:FF",
            essid="TestNetwork",
            channel=6,
            power=-50,
            security=SecurityType.WPA2
        )
        assert net.bssid == "AA:BB:CC:DD:EE:FF"
        assert net.security == SecurityType.WPA2
        d = net.to_dict()
        assert isinstance(d, dict)
        print("✓ Types test passed")
        return True
    except Exception as e:
        print(f"✗ Types error: {e}")
        return False

def test_wordlist_generator():
    """Test wordlist generator"""
    try:
        from utils.wordlist import WordlistGenerator
        gen = WordlistGenerator()
        output = gen.generate(
            essid="TestNet",
            keywords=["admin", "password"],
            output_file="/tmp/test_wordlist.txt"
        )
        assert os.path.exists(output)
        with open(output, 'r') as f:
            lines = f.readlines()
        assert len(lines) > 0
        os.remove(output)
        print("✓ Wordlist generator test passed")
        return True
    except Exception as e:
        print(f"✗ Wordlist error: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("RS WiFi Cracker PRO - Test Suite")
    print("="*50 + "\n")
    
    results = []
    results.append(test_imports())
    results.append(test_config())
    results.append(test_types())
    results.append(test_wordlist_generator())
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("="*50 + "\n")
    
    return all(results)

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
