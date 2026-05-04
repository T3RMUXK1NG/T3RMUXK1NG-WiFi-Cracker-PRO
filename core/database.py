#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3RMUXK1NG WiFi Cracker PRO - Database Module"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path.home() / '.local' / 'share' / 't3rmuxk1ng-wifi-pro' / 'data.db')
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
    
    def initialize(self):
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS networks (
                bssid TEXT PRIMARY KEY,
                essid TEXT,
                channel INTEGER,
                encryption TEXT,
                power INTEGER,
                wps BOOLEAN,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bssid TEXT,
                cap_file TEXT,
                handshake BOOLEAN,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bssid TEXT,
                essid TEXT,
                password TEXT,
                method TEXT,
                time_taken REAL,
                timestamp TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def save_network(self, network: Dict):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO networks 
            (bssid, essid, channel, encryption, power, wps, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            network.get('bssid'),
            network.get('essid'),
            network.get('channel'),
            network.get('encryption'),
            network.get('power'),
            network.get('wps', False),
            network.get('first_seen', datetime.now().isoformat()),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def save_capture(self, bssid: str, cap_file: str, handshake: bool):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO captures (bssid, cap_file, handshake, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (bssid, cap_file, handshake, datetime.now().isoformat()))
        self.conn.commit()
    
    def save_result(self, bssid: str, essid: str, password: str, method: str, time_taken: float):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO results (bssid, essid, password, method, time_taken, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (bssid, essid, password, method, time_taken, datetime.now().isoformat()))
        self.conn.commit()
    
    def save_results(self, results: Dict):
        for bssid, result in results.items():
            if result.get('password'):
                self.save_result(
                    bssid,
                    result.get('essid', ''),
                    result.get('password'),
                    result.get('method', 'unknown'),
                    result.get('time_taken', 0)
                )
    
    def get_results(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM results ORDER BY timestamp DESC')
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def close(self):
        if self.conn:
            self.conn.close()
