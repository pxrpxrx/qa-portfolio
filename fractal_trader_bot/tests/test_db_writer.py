import pytest
import sys
import sqlite3
from pathlib import Path

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from bx_db_writer import BingXDBWriter


@pytest.fixture
def db_writer(tmp_path):
    """BingXDBWriter с in-memory SQLite (через временный файл)"""
    db_path = str(tmp_path / "test_positions.db")
    writer = BingXDBWriter(db_path)
    yield writer
    writer.close()


def _reset_singleton():
    """Сброс синглтона между тестами"""
    BingXDBWriter._instance = None
    BingXDBWriter._initialized = False


class TestBingXDBWriter:

    @pytest.fixture(autouse=True)
    def reset(self):
        _reset_singleton()
        yield
        _reset_singleton()

    def test_add_position(self, db_writer):
        """Добавление новой позиции"""
        pos_id = db_writer.add_position(
            symbol='BTC-USDT',
            side='BUY',
            entry_price=50000.0,
            quantity=0.001,
            stop_percent=0.5,
            take_percent=1.5,
            metadata={'strategy': 'fractal'},
        )
        assert pos_id is not None
        assert isinstance(pos_id, int)
        assert pos_id > 0

    def test_update_position(self, db_writer):
        """Обновление позиции при закрытии"""
        db_writer.add_position(
            symbol='ETH-USDT',
            side='BUY',
            entry_price=3000.0,
            quantity=0.1,
            stop_percent=1.0,
            take_percent=2.5,
            metadata={'strategy': 'fractal'},
        )
        result = db_writer.update_position(
            symbol='ETH-USDT',
            exit_price=3100.0,
            realized_pnl=10.0,
            realized_pnl_percent=3.33,
            exit_reason='TAKE_PROFIT',
            metadata={'slippage': 0.01},
        )
        assert result is not None
        assert isinstance(result, int)

    def test_get_open_positions(self, db_writer):
        """Получение списка открытых позиций"""
        db_writer.add_position(
            symbol='BTC-USDT', side='BUY',
            entry_price=50000.0, quantity=0.001,
            stop_percent=0.5, take_percent=1.5,
        )
        db_writer.add_position(
            symbol='ETH-USDT', side='SELL',
            entry_price=3000.0, quantity=0.1,
            stop_percent=1.0, take_percent=2.0,
        )
        open_positions = db_writer.get_open_positions()
        assert len(open_positions) == 2
        symbols = {p['symbol'] for p in open_positions}
        assert 'BTC-USDT' in symbols
        assert 'ETH-USDT' in symbols

    def test_symbol_stats_update(self, db_writer):
        """Обновление статистики по монете при закрытии позиции"""
        db_writer.add_position(
            symbol='SOL-USDT', side='BUY',
            entry_price=100.0, quantity=1.0,
            stop_percent=0.5, take_percent=1.5,
        )
        db_writer.update_position(
            symbol='SOL-USDT',
            exit_price=105.0,
            realized_pnl=5.0,
            realized_pnl_percent=5.0,
            exit_reason='TAKE_PROFIT',
        )
        conn = sqlite3.connect(str(db_writer.db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM symbol_stats WHERE symbol = ?', ('SOL-USDT',))
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        assert row[1] == 1  # total_trades
        assert row[2] == 1  # winning_trades
        assert row[3] == 0  # losing_trades
