import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Tuple, Optional

logger = logging.getLogger('RiskManager')


class RiskManager:
    
    def __init__(self, config_path: str = 'risk_config.json'):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.daily_stats = self._load_daily_stats()
        self.peak_balance = None

    def _load_config(self) -> Dict:
        """Загрузка конфигурации"""
        default = {
            'max_positions': 25,
            'max_position_size_abs': 25,
            'min_position_size': 5.0,
            'daily_loss_limit_abs': 10,
            'max_drawdown_percent': 15.0,
            'blacklist': [],
            'min_atr_percent': 0.255,
            'whitelist': [],
            'trading_hours': {'start': 0, 'end': 24},
            'weekend_trading': True,
            'min_volume_24h': 1000000,
            'min_price': 1e-06,
            'emergency_stop': False
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    default.update(json.load(f))
            except Exception as e:
                logger.error(f"Ошибка загрузки: {e}")
        
        return default

    def _load_daily_stats(self) -> Dict:
        """Загрузка дневной статистики"""
        stats_file = Path('daily_stats.json')
        default_stats = {
            'date': date.today().isoformat(),
            'starting_balance': None,
            'current_balance': None,
            'trades_today': 0,
            'wins_today': 0,
            'losses_today': 0,
            'pnl_today': 0.0
        }
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                if stats.get('date') != date.today().isoformat():
                    return default_stats
                return stats
            except:
                return default_stats
        return default_stats

    def can_trade(self, monitor) -> Tuple[bool, str]:
        """Глобальная проверка - можно ли вообще торговать"""
        if self.config['emergency_stop']:
            return False, "Аварийная остановка"
        
        if not self._check_trading_hours():
            return False, "Вне торговых часов"
        
        if self.daily_stats.get('pnl_today', 0) <= -self.config['daily_loss_limit_abs']:
            return False, "Дневной лимит убытка"
        
        if self.peak_balance:
            current_balance = self.daily_stats.get('current_balance', 0)
            dd = (self.peak_balance - current_balance) / self.peak_balance * 100
            if dd >= self.config['max_drawdown_percent']:
                return False, f"Просадка {dd:.1f}%"
        
        open_positions = len(monitor.positions) if monitor else 0
        if open_positions >= self.config['max_positions']:
            return False, f"Лимит позиций ({self.config['max_positions']})"
        
        return True, "OK"

    def can_trade_symbol(self, symbol: str, market_data: Dict = None) -> Tuple[bool, str]:
        """Проверка конкретной монеты"""
        if symbol in self.config['blacklist']:
            return False, "В черном списке"
        
        if self.config['whitelist'] and symbol not in self.config['whitelist']:
            return False, "Не в белом списке"
        
        if market_data:
            if market_data.get('volume_24h', 0) < self.config['min_volume_24h']:
                return False, "Малый объем"
            
            if market_data.get('price', 0) < self.config['min_price']:
                return False, "Низкая цена"
            
            atr_pct = market_data.get('atr_percent', 0)
            min_atr = self.config.get('min_atr_percent', 0.255)
            if atr_pct < min_atr:
                return False, f"ATR {atr_pct:.3f}% < {min_atr}%"
        
        return True, "OK"

    def check_position_size(self, position_data: Dict) -> Tuple[bool, str]:
        
        print(f"🔍 RiskManager получил: {position_data}")

        # Пробуем получить размер в USDT из разных ключей
        value = position_data.get('position_value', 0)
        if value == 0:
            value = position_data.get('position_value_usdt', 0)
        if value == 0:
            # Пробуем вычислить из цены и количества
            price = position_data.get('entry_price', position_data.get('price', 0))
            qty = position_data.get('quantity', position_data.get('size', 0))
            value = price * qty
        
        if value <= 0:
            return False, "Нет размера"
        
        if value > self.config['max_position_size_abs']:
            return False, f">{self.config['max_position_size_abs']} USDT"
        
        if value < self.config['min_position_size']:
            return False, f"<{self.config['min_position_size']} USDT"
        
        return True, "OK"

    def _check_trading_hours(self) -> bool:
        """Проверка торговых часов"""
        now = datetime.now()
        
        if not self.config['weekend_trading'] and now.weekday() >= 5:
            return False
        
        hour = now.hour + now.minute / 60
        start = self.config['trading_hours']['start']
        end = self.config['trading_hours']['end']
        
        if start <= end:
            return start <= hour < end
        else:
            return hour >= start or hour < end

    def update_balance(self, balance: float):
        """Обновление баланса"""
        if self.peak_balance is None:
            self.peak_balance = balance
        elif balance > self.peak_balance:
            self.peak_balance = balance
        
        self.daily_stats['current_balance'] = balance
        if self.daily_stats['starting_balance'] is None:
            self.daily_stats['starting_balance'] = balance
        self.daily_stats['pnl_today'] = balance - self.daily_stats['starting_balance']

    def register_trade(self, trade: Dict):
        """Регистрация сделки"""
        self.daily_stats['trades_today'] = self.daily_stats.get('trades_today', 0) + 1
        if trade.get('pnl', 0) > 0:
            self.daily_stats['wins_today'] = self.daily_stats.get('wins_today', 0) + 1
        else:
            self.daily_stats['losses_today'] = self.daily_stats.get('losses_today', 0) + 1

    
    def check_rr(self, rr: float) -> Tuple[bool, str]:
        """Проверка соотношения риск/прибыль"""
        min_rr = self.config.get('min_rr', 2.5)  # ← из конфига!
        if rr < min_rr:
            return False, f"R/R {rr:.2f} < {min_rr}"
        return True, "OK"

    def check_profit_risk(self, profit: float, loss: float) -> Tuple[bool, str]:
        """Проверка прибыли и риска"""
        min_profit = self.config.get('min_profit_usdt', 0.5)  # ← из конфига!
        max_risk = self.config.get('max_risk_usdt', 2.5)      # ← из конфига!
        
        if profit < min_profit:
            return False, f"Profit {profit:.2f} < {min_profit}"
        
        if loss > max_risk:
            return False, f"Risk {loss:.2f} > {max_risk}"
        
        return True, "OK"