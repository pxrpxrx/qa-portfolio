# Инструкция по работе с Postman-коллекцией

## Импорт коллекции

1. Открыть Postman
2. Нажать **Import** → **File** → Выбрать файл `arbitrage-api-collection.json`
3. Нажать **Import**

## Запуск тестов

1. В левой панели выбрать коллекцию **Crypto Arbitrage API Tests**
2. Нажать **"..."** → **Run collection**
3. Выбрать окружение (если есть) → нажать **Run**

## Ожидаемые результаты

| Эндпоинт | Статус | Структура ответа |
|:---|:---|:---|
| MEXC | 200 OK | Массив объектов с полями symbol, askPrice, bidPrice |
| Bybit | 200 OK | Объект с полем result.list |
| HTX | 200 OK | Объект с полем data |

## Пример теста в Postman (JavaScript)

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has askPrice field", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData[0]).to.have.property('askPrice');
});