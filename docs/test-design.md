# Test Design Techniques

Документ демонстрирует применение техник тест-дизайна на реальных проектах портфолио.

## Техники

| # | Техника | Описание | Где применена |
|---|---------|----------|---------------|
| 1 | Boundary Value Analysis (BVA) | Тестирование на границах диапазонов | [tbank_qrcode_service](tbank_qrcode_service/docs/test-design.md) |
| 2 | Equivalence Partitioning (EP) | Разбиение на классы эквивалентности | [tbank_qrcode_service](tbank_qrcode_service/docs/test-design.md), [macro-dashboard](macro-dashboard/docs/test-design.md) |
| 3 | Pairwise Testing | Попарное комбинирование параметров | [arbit_website](arbit_website/docs/test-design.md) |
| 4 | Decision Tables | Таблицы решений для бизнес-логики | [tbank_qrcode_service](tbank_qrcode_service/docs/test-design.md) |
| 5 | State Transition | Переходы между состояниями | [tbank_qrcode_service](tbank_qrcode_service/docs/test-design.md) |

## Почему не для всех проектов?

Тест-дизайн применяется там, где есть:
- **Чёткие бизнес-правила** (платежи, валидация) → Decision Tables, State Transition
- **Числовые диапазоны** (сумма, возраст) → BVA, EP
- **Множество комбинаций параметров** → Pairwise

Для простых проектов (fractal_trader_bot, exchanger_bot) достаточно функциональных тестов без формального тест-дизайна — это реалистичный подход, который ценят на собеседованиях.

## Вопросы для собеседования

**Q: Что такое тест-дизайн?**
A: Систематический подход к созданию тест-кейсов. Цель — покрыть максимум функциональности минимумом тестов.

**Q: Когда использовать BVA, а когда Pairwise?**
A: BVA — когда есть один числовой параметр с известными границами. Pairwise — когда много параметров и их комбинаций (3+ параметра).

**Q: Можно ли комбинировать техники?**
A: Да, и нужно. EP определяет классы, BVA добавляет граничные значения, Decision Table покрывает комбинации условий.
