import pytest
import sys
from pathlib import Path
from typing import Dict, List

# Добавляем src со всеми поддиректориями в sys.path
_src_root = Path(__file__).parent.parent / "src"
for _d in [_src_root] + [p for p in _src_root.rglob("*") if p.is_dir()]:
    _d_str = str(_d)
    if _d_str not in sys.path:
        sys.path.insert(0, _d_str)


@pytest.fixture
def mock_klines_small() -> List[Dict]:
    """10 свечей для тестов с недостаточными данными"""
    return [
        {'high': 100 + i, 'low': 99 + i, 'close': 99.5 + i}
        for i in range(10)
    ]


@pytest.fixture
def mock_klines_up_trend() -> List[Dict]:
    """20 свечей с восходящим трендом и известным верхним фракталом"""
    data = []
    for i in range(20):
        base = 100 + i * 2
        data.append({
            'high': base + 5,
            'low': base - 3,
            'close': base + 2,
            'time': 1_600_000_000 + i * 60_000,
        })
    # Форсируем верхний фрактал на индексе 5 (high = 115)
    data[5]['high'] = 115
    data[3]['high'] = 110
    data[4]['high'] = 112
    data[6]['high'] = 113
    data[7]['high'] = 114
    # Форсируем нижний фрактал на индексе 12 (low = 113)
    data[12]['low'] = 113
    data[10]['low'] = 117
    data[11]['low'] = 116
    data[13]['low'] = 115
    data[14]['low'] = 116
    return data


@pytest.fixture
def mock_klines_down_trend() -> List[Dict]:
    """20 свечей с нисходящим трендом и известными фракталами"""
    data = []
    for i in range(20):
        base = 200 - i * 2
        data.append({
            'high': base + 4,
            'low': base - 4,
            'close': base + 1,
            'time': 1_600_000_000 + i * 60_000,
        })
    # Верхний фрактал на индексе 6
    data[6]['high'] = 195
    data[4]['high'] = 190
    data[5]['high'] = 192
    data[7]['high'] = 191
    data[8]['high'] = 189
    # Нижний фрактал на индексе 14
    data[14]['low'] = 168
    data[12]['low'] = 174
    data[13]['low'] = 172
    data[15]['low'] = 170
    data[16]['low'] = 171
    return data


@pytest.fixture
def mock_signal_long() -> Dict:
    """Сигнал LONG (UP) для тестов парсера"""
    return {
        'symbol': 'BTC-USDT',
        'trend': 'UP',
        'price': 50000.0,
        'position_size': 0.001,
        'stop_loss': 49800.0,
        'take_profit': 50500.0,
        'stop_percent': 0.4,
        'take_percent': 1.0,
        'atr': 120.0,
        'atr_pct': 0.24,
        'final_score': 0.85,
        'risk_amount': 5.0,
        'risk_reward_ratio': 2.5,
        'expected_net_profit': 0.5,
        'expected_net_loss': 0.2,
    }


@pytest.fixture
def mock_signal_short() -> Dict:
    """Сигнал SHORT (DOWN) для тестов парсера"""
    return {
        'symbol': 'ETH-USDT',
        'trend': 'DOWN',
        'price': 3000.0,
        'position_size': 0.1,
        'stop_loss': 3090.0,
        'take_profit': 2850.0,
        'stop_percent': 3.0,
        'take_percent': 5.0,
        'atr': 60.0,
        'atr_pct': 2.0,
        'final_score': 0.72,
        'risk_amount': 10.0,
        'risk_reward_ratio': 1.67,
        'expected_net_profit': 15.0,
        'expected_net_loss': 9.0,
    }


@pytest.fixture
def mock_empty_signals() -> List[Dict]:
    """Пустой список сигналов"""
    return []
