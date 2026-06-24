def positionSizing(capital=5000, price=None, atr=None, direction="UP", 
                   risk_percent=0.02, stop_loss_mult=1.25, take_profit_mult=2.5, target_position_usdt=5.5,
                   remaining_capital=None):
    
    if not price:
        return {'error': 'Нет цены'}
    
    # Минимальные стопы для защиты от шума (0.4% для 1m)

    COMMISSION_PCT = 0.05
    
    # ATR если нет
    if not atr or atr == 0:
        atr = price * 0.005  # 0.5% как запасной вариант
    
    # Проценты
    atr_pct = (atr / price) * 100
    
    # Правильный расчет стопа ===
    stop_loss_pct = atr_pct * stop_loss_mult
    take_profit_pct = atr_pct * take_profit_mult

    MIN_STOP_PCT = 0.2
    MIN_TAKE_PCT = 0.6
    
    # Защита от слишком маленьких стопов
    if stop_loss_pct < MIN_STOP_PCT:
        stop_loss_pct = MIN_STOP_PCT
    if take_profit_pct < MIN_TAKE_PCT:
        take_profit_pct = MIN_TAKE_PCT
    
    # Учет комиссий
    effective_stop_pct = stop_loss_pct + COMMISSION_PCT * 2
    effective_take_pct = take_profit_pct - COMMISSION_PCT * 2
    
    if effective_take_pct <= 0:
        take_profit_pct = max(take_profit_pct, MIN_TAKE_PCT)
        effective_take_pct = take_profit_pct - COMMISSION_PCT * 2
    
    # R/R
    rr = effective_take_pct / effective_stop_pct if effective_stop_pct > 0 else 0
    
    # Правильный расчет размера ===
    risk_amount = capital * risk_percent
    stop_distance = price * (stop_loss_pct / 100)  # Стоп в деньгах
    size = target_position_usdt / price
    position_value = size * price
    
    # Ограничение: не более 5% капитала в одной позиции
    max_value = capital * 0.05
    if position_value > max_value:
        size = max_value / price
        position_value = max_value
    
    # Уровни
    if direction == "UP":
        stop = price * (1 - stop_loss_pct / 100)
        take = price * (1 + take_profit_pct / 100)
        exp_loss = (price - stop) * size
        exp_profit = (take - price) * size
    else:
        stop = price * (1 + stop_loss_pct / 100)
        take = price * (1 - take_profit_pct / 100)
        exp_loss = (stop - price) * size
        exp_profit = (price - take) * size
    
    # Округление
    precision = 8
    stop = round(stop, precision)
    take = round(take, precision)
    
    return {
        'size': size,
        'entry': price,
        'stop_loss': stop,
        'take_profit': take,
        'stop_percent': stop_loss_pct,
        'take_percent': take_profit_pct,
        'expected_net_loss': exp_loss,
        'expected_net_profit': exp_profit,
        'risk_reward_ratio': rr,
        'position_value': position_value,
        'direction': direction,
        'atr': atr,
        'atr_pct': atr_pct
    }