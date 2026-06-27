# Regression Checklist — Macro Dashboard

## Перед каждым релизом

### Unit-тесты
- [ ] Все 64 теста проходят (`mvn test`)
- [ ] DataManager: pctChange, mean, std, zScore, priorValue
- [ ] MacroContext: GREEN/YELLOW/RED сценарии
- [ ] BtcFrame: оценка BTC, support/resistance
- [ ] DivergenceScanner: поиск дивергенций
- [ ] GannSquare9: price-to-angle, S/R уровни

### Интеграционные тесты
- [ ] Приложение запускается без ошибок
- [ ] HTML-дашборд генерируется корректно
- [ ] Все API-вызовы возвращают данные (FRED, Yahoo, Binance)

### Функциональные проверки
- [ ] Macro статус отображается (GREEN/YELLOW/RED)
- [ ] BTC статус отображается
- [ ] Дивергенции отображаются
- [ ] Горизонты (1-2w, 1-3m, 3-12m) заполнены
- [ ] Сценарии отображаются с вероятностями

### Производительность
- [ ] Время выполнения < 30 секунд
- [ ] Память < 512 MB

### Документация
- [ ] README актуален
- [ ] Test-plan обновлён
- [ ] Changelog заполнен

## После релиза
- [ ] GitHub Actions CI проходит
- [ ] Allure отчёт генерируется
- [ ] Dashboard.html доступен
