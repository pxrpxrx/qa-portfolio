# config_loader.py
import json
from pathlib import Path

class ConfigLoader:
    def __init__(self):
        config_path = Path(__file__).parent / "config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
    
    @property
    def api_key(self):
        return self._config['bingx']['api_key']
    
    @property
    def api_secret(self):
        return self._config['bingx']['api_secret']
    
    @property
    def testnet(self):
        return self._config['bingx']['testnet']
    
    @property
    def scan_interval(self):
        return self._config['scan']['interval_seconds']
    
    @property
    def monitor_interval(self):
        return self._config['monitor']['interval_seconds']
    
    @property
    def capital_per_trade(self):
        return self._config['trading']['capital_per_trade']
    
    @property
    def emergency_stop(self):
        return self._config.get('modes', {}).get('emergency_stop', False)

# Единый экземпляр для импорта
config = ConfigLoader()