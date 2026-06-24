# Инструкция по работе с Postman

## Импорт коллекции

1. Открыть Postman
2. Нажать **Import** → **File** → выбрать `postman-collection.json`
3. Нажать **Import**

## Настройка переменных

1. В коллекции нажать **"..."** → **Edit**
2. Перейти на вкладку **Variables**
3. В поле `api_key` указать свой ключ BestChange

## Запуск тестов

1. Открыть коллекцию
2. Нажать **"..."** → **Run collection**
3. Выбрать окружение (если есть)
4. Нажать **Run**

## Ожидаемые результаты

| Эндпоинт | Статус | Структура ответа |
|:---|:---|:---|
| `rates/93-105` | 200 OK | Объект с полем `rates` |
| `rates/93-10` | 200 OK | Объект с полем `rates` |
| `rates/10-105` | 200 OK | Объект с полем `rates` |
| `INVALID_KEY/rates/93-105` | 401 Unauthorized | Ошибка авторизации |

## Пример теста в Postman (JavaScript)

```javascript
pm.test("Статус 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Ответ содержит поле rates", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('rates');
});

pm.test("Ответ содержит курс для пары 93-105", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.rates).to.have.property('93-105');
});