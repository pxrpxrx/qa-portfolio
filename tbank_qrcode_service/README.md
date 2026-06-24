# TBank QR Code Service — микросервис приёма платежей через СБП Тинькофф

Микросервис на **Java 17 + Spring Boot 3.3.4** для генерации QR-кодов и приёма платежей через Систему Быстрых Платежей (СБП) Тинькофф Банка.

## Возможности

- Генерация QR-кода для оплаты (SVG) через API Тинькофф
- WebSocket-уведомления о статусе оплаты в реальном времени
- Хранение заказов в PostgreSQL
- Кэширование статусов в Redis
- Интеграция с Tinkoff API (v2)

## Технологический стек

| Компонент        | Технология                                |
|------------------|-------------------------------------------|
| Язык             | Java 17                                   |
| Фреймворк        | Spring Boot 3.3.4                         |
| Сборщик          | Maven                                     |
| База данных      | PostgreSQL                                |
| Кэш              | Redis                                     |
| WebSocket        | Spring WebSocket (STOMP)                  |
| HTTP-клиент      | Apache HttpClient 5                       |
| QR-коды          | ZXing 3.5.3 (core + javase)              |
| JSON             | Jackson                                   |

## API

### 1. Инициализация платежа и получение QR-кода

```
GET /api/sbp/init-and-qr?userId=STRING&amount=DOUBLE
```

**Параметры:**

| Параметр | Тип    | Обязательный | Описание                |
|----------|--------|-------------|-------------------------|
| userId   | String | да          | Уникальный ID клиента   |
| amount   | Double | да          | Сумма к оплате          |

**Ответ (200 OK):**
```json
{
  "qrSvg": "<svg>...</svg>",
  "orderId": "order-xxxxxxxx-xxxx"
}
```

**Ошибки:**
- `400 Bad Request` — отсутствует userId, amount <= 0 или передан неверный тип
- `500 Internal Server Error` — ошибка интеграции с Тинькофф

### 2. WebSocket — уведомления об оплате

```
ws://<host>:8080/ws
```

Подписка:
```
SUBSCRIBE /topic/payment/{orderId}
```

Сообщение при оплате:
```json
{
  "orderId": "order-xxxxxxxx-xxxx",
  "status": "CONFIRMED"
}
```

### 3. Health Check

```
GET /actuator/health
```

## Быстрый старт

### Требования

- Java 17+
- Maven 3.8+
- PostgreSQL 14+
- Redis 6+

### Запуск

```bash
# 1. Настройка БД
createdb payments_db

# 2. Сборка
mvn clean package -DskipTests

# 3. Запуск
java -jar target/payment-api-3.0.jar
```

### Конфигурация

Основные параметры в `application.properties`:

```properties
tinkoff.api.url=https://securepay.tinkoff.ru/v2/
tinkoff.terminal.key=1765518875198DEMO
tinkoff.secret.key=<ваш-секретный-ключ>
tinkoff.notification.url=https://ваш-домен/tinkoff/notify

spring.datasource.url=jdbc:postgresql://localhost:5433/payments_db
spring.datasource.username=payments
spring.datasource.password=<your-db-password>

spring.data.redis.host=localhost
spring.data.redis.port=6379
```

## Тестирование

### Python (интеграционные тесты)

```bash
pip install -r tests/requirements-test.txt
cd tests
pytest -v
```

### Java (модульные тесты)

```bash
mvn test
```

## Структура проекта

```
src/main/java/org/example/
├── Main.java
├── config/WebSocketConfig.java
├── controller/
│   ├── QrCodeController.java
│   ├── QrSbpController.java
│   └── SbpController.java
├── dto/
│   ├── PaymentInitResponse.java
│   └── PaymentManagerRequest.java
├── entity/PaymentEntity.java
├── repository/PaymentRepository.java
├── service/
│   ├── TinkoffApiService.java
│   ├── QrCodeService.java
│   ├── PaymentStatusStorage.java
│   ├── WebSocketNotificationService.java
│   └── TinkoffNotificationController.java
└── web/
    ├── PaymentController.java
    └── PaymentManagerController.java
```
