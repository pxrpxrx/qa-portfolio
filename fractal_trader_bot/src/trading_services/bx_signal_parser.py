# bx_signal_parser.py
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger('TradeExecutor')

@dataclass
class BingXOrder:
    """Структура ордера для BingX API (USDT-M futures)"""
    symbol: str          # В формате BTC-USDT
    side: str            # BUY или SELL
    positionSide: str    # LONG или SHORT
    type: str            # MARKET, LIMIT, STOP_MARKET, TAKE_PROFIT_MARKET
    quantity: str        # Дробное число (количество монет)
    price: Optional[str] = None
    stopPrice: Optional[str] = None
    workingType: str = "MARK_PRICE"
    timeInForce: str = "GTC"
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class BingXOrderPreparer:
    """
    Сервис для подготовки сигналов к отправке на BingX API (USDT-M)
    Использует ТОЛЬКО эталонные значения из positionSizing:
    - stop_loss_mult = 0.2 ATR
    - take_profit_mult = 0.5 ATR
    - risk_percent = 1% от капитала
    """
    
    def __init__(self):
        self.prepared_orders = []
    
    def prepare_signals(self, signals: List[Dict]) -> List[Dict]:
        """
        Подготовка сигналов для USDT-M фьючерсов
        
        Args:
            signals: список сигналов от analyze_and_record()
        """
        if not signals:
            logger.info("Нет сигналов для подготовки")
            return []
        
        logger.info(f"Подготовка {len(signals)} сигналов для USDT-M...")
        prepared_orders = []
        
        for signal in signals:
            try:
                symbol = signal['symbol']
                
                # Определяем сторону ордера
                if signal['trend'] == "UP":
                    side = "BUY"
                    position_side = "LONG"
                else:  # DOWN
                    side = "SELL"
                    position_side = "SHORT"
                
                # Количество монет (уже рассчитано positionSizing)
                quantity = str(round(signal['position_size'], 8))
                
                # Создаем entry ордер
                entry_order = BingXOrder(
                    symbol=symbol,
                    side=side,
                    positionSide=position_side,
                    type="MARKET",
                    quantity=quantity
                )
                
                # ЭТАЛОННЫЕ ЗНАЧЕНИЯ из positionSizing
                stop_loss_pct = signal.get('stop_percent', 0.99)
                take_profit_pct = signal.get('take_percent', 2.5)  
                atr_value = signal.get('atr', 0)
                atr_pct = signal.get('atr_pct', 0)
                
                # Формируем summary с эталонной информацией
                summary = {
                    'original_symbol': symbol,
                    'direction': signal['trend'],
                    'entry_price': signal['price'],
                    'quantity': signal['position_size'],
                    'stop_loss': signal.get('stop_loss'),
                    'take_profit': signal.get('take_profit'),
                    # ЭТАЛОННЫЕ ПРОЦЕНТЫ (никаких минимальных границ!)
                    'stop_percent': stop_loss_pct,
                    'take_percent': take_profit_pct,
                    # ATR информация
                    'atr': atr_value,
                    'atr_pct': atr_pct,
                    # Метаданные
                    'final_score': signal.get('final_score', 0),
                    'risk_amount': signal.get('risk_amount', 0),
                    'position_value': signal['price'] * signal['position_size'],
                    'position_value_usdt': signal['price'] * signal['position_size'],
                    'risk_reward_ratio': signal.get('risk_reward_ratio', 0),
                    'expected_net_profit': signal.get('expected_net_profit', 0),
                    'expected_net_loss': signal.get('expected_net_loss', 0),
                }
                
                prepared = {
                    'original_symbol': symbol,
                    'symbol': symbol,
                    'direction': signal['trend'],
                    'entry_order': entry_order.to_dict(),
                    'summary': summary
                }
                
                # Добавляем стоп-лосс ордер если есть (по абсолютной цене)
                if signal.get('stop_loss'):
                    stop_order = self._create_stop_order(
                        symbol=symbol,
                        direction=signal['trend'],
                        position_side=position_side,
                        quantity=quantity,
                        stop_price=signal['stop_loss']
                    )
                    if stop_order:
                        prepared['stop_loss_order'] = stop_order.to_dict()
                        logger.info(f"   Стоп-лосс ордер создан по цене {signal['stop_loss']:.4f}")
                
                # Добавляем тейк-профит ордер если есть
                if signal.get('take_profit'):
                    take_order = self._create_take_order(
                        symbol=symbol,
                        direction=signal['trend'],
                        position_side=position_side,
                        quantity=quantity,
                        take_price=signal['take_profit']
                    )
                    if take_order:
                        prepared['take_profit_order'] = take_order.to_dict()
                        logger.info(f"   Тейк-профит ордер создан по цене {signal['take_profit']:.4f}")
                
                prepared_orders.append(prepared)
                
                # Логируем подготовленный ордер с эталонными процентами
                log_msg = f"📦 {symbol} {side} {position_side} | {quantity} монет"
                if atr_pct > 0:
                    log_msg += f" | ATR: {atr_pct:.2f}%"
                    log_msg += f" | Стоп: {stop_loss_pct:.2f}%"
                    log_msg += f" | Тейк: {take_profit_pct:.2f}%"
                logger.info(log_msg)
                
            except Exception as e:
                logger.error(f"❌ Ошибка подготовки {signal.get('symbol')}: {e}")
                continue
        
        logger.info(f"✅ Подготовлено ордеров: {len(prepared_orders)}")
        return prepared_orders
    
    def _create_stop_order(self, symbol: str, direction: str, position_side: str, 
                          quantity: str, stop_price: float) -> Optional[BingXOrder]:
        """
        Создает стоп-лосс ордер (абсолютная цена)
        """
        try:
            # Для закрытия позиции side противоположен входу
            close_side = "SELL" if direction == "UP" else "BUY"
            
            # Определяем точность для цены
            precision = self._get_price_precision(stop_price)
            
            return BingXOrder(
                symbol=symbol,
                side=close_side,
                positionSide=position_side,
                type="STOP_MARKET",
                quantity=quantity,
                stopPrice=str(round(stop_price, precision)),
                workingType="MARK_PRICE"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка создания стоп-ордера: {e}")
            return None
    
    def _create_take_order(self, symbol: str, direction: str, position_side: str,
                          quantity: str, take_price: float) -> Optional[BingXOrder]:
        """
        Создает тейк-профит ордер (абсолютная цена)
        """
        try:
            # Для закрытия позиции side противоположен входу
            close_side = "SELL" if direction == "UP" else "BUY"
            
            # Определяем точность для цены
            precision = self._get_price_precision(take_price)
            
            return BingXOrder(
                symbol=symbol,
                side=close_side,
                positionSide=position_side,
                type="TAKE_PROFIT_MARKET",
                quantity=quantity,
                stopPrice=str(round(take_price, precision)),
                workingType="MARK_PRICE"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка создания тейк-ордера: {e}")
            return None
    
    def _get_price_precision(self, price: float) -> int:
        """Определяет нужное количество знаков после запятой для цены"""
        if price < 0.0001:
            return 8
        elif price < 0.001:
            return 7
        elif price < 0.01:
            return 6
        elif price < 0.1:
            return 5
        elif price < 1:
            return 4
        elif price < 10:
            return 3
        else:
            return 2
    
    def format_for_display(self, prepared: Dict) -> str:
        """Форматирование для вывода с эталонной информацией"""
        lines = []
        lines.append("\n" + "="*90)
        lines.append("📋 ПОДГОТОВЛЕННЫЙ ОРДЕР (ЭТАЛОННАЯ СТРАТЕГИЯ)")
        lines.append("="*90)
        
        summary = prepared['summary']
        lines.append(f"\n📊 СВОДКА:")
        lines.append(f"   Монета: {summary['original_symbol']}")
        lines.append(f"   Направление: {'🟢 LONG' if summary['direction'] == 'UP' else '🔴 SHORT'}")
        lines.append(f"   Цена входа: {summary['entry_price']:.4f}")
        lines.append(f"   Количество: {summary['quantity']:.4f} монет")
        lines.append(f"   Стоимость: {summary['quantity'] * summary['entry_price']:.2f} USDT")
        
        if summary['atr'] > 0:
            lines.append(f"\n📈 ЭТАЛОННЫЕ ПАРАМЕТРЫ (positionSizing):")
            lines.append(f"   ATR: {summary['atr']:.4f} ({summary['atr_pct']:.2f}%)")
            lines.append(f"   Риск (1%): {summary['risk_amount']:.2f} USDT")
            lines.append(f"   Стоп (0.2 ATR): {summary['stop_percent']:.2f}%")
            lines.append(f"   Тейк (0.5 ATR): {summary['take_percent']:.2f}%")
        
        if summary.get('stop_loss'):
            stop_dist = abs(summary['entry_price'] - summary['stop_loss'])
            stop_dist_pct = (stop_dist / summary['entry_price']) * 100
            lines.append(f"\n🛑 СТОП-ЛОСС (абсолютный):")
            lines.append(f"   Цена: {summary['stop_loss']:.4f}")
            lines.append(f"   Дистанция: {stop_dist:.4f} ({stop_dist_pct:.2f}%)")
        
        if summary.get('take_profit'):
            take_dist = abs(summary['take_profit'] - summary['entry_price'])
            take_dist_pct = (take_dist / summary['entry_price']) * 100
            lines.append(f"\n🎯 ТЕЙК-ПРОФИТ (абсолютный):")
            lines.append(f"   Цена: {summary['take_profit']:.4f}")
            lines.append(f"   Дистанция: {take_dist:.4f} ({take_dist_pct:.2f}%)")
        
        lines.append(f"\n📈 СКОР: {summary['final_score']:.3f}")
        
        if prepared.get('entry_order'):
            lines.append(f"\n🚀 ENTRY ORDER:")
            lines.append(f"   {json.dumps(prepared['entry_order'], indent=2)}")
        
        lines.append("="*90)
        return '\n'.join(lines)