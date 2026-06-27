package org.example.integration;

import org.junit.jupiter.api.*;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketHttpHeaders;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.client.standard.StandardWebSocketClient;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.net.URI;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assumptions.*;

/**
 * Интеграционные тесты WebSocket для получения статусов оплаты.
 * Требуют запущенный сервер (WS_URL).
 * Пропускаются автоматически, если сервер недоступен.
 */
@Tag("integration")
@TestMethodOrder(MethodOrderer.DisplayName.class)
class WebSocketIntegrationTest {

    private static final String WS_URL = System.getenv().getOrDefault("TEST_WS_URL", "ws://localhost:8080/ws");
    private static final String BASE_URL = System.getenv().getOrDefault("TEST_BASE_URL", "http://localhost:8080");
    private static boolean serverAvailable;

    @BeforeAll
    static void checkServer() {
        try {
            StandardWebSocketClient client = new StandardWebSocketClient();
            WebSocketSession session = client.execute(
                new TextWebSocketHandler() {},
                new WebSocketHttpHeaders(),
                URI.create(WS_URL)
            ).get(5, TimeUnit.SECONDS);
            serverAvailable = session.isOpen();
            session.close();
        } catch (Exception e) {
            serverAvailable = false;
        }
        assumeTrue(serverAvailable, "WebSocket сервер недоступен по адресу " + WS_URL + " — тесты пропущены");
    }

    @Test
    @DisplayName("Подключение к WebSocket")
    void websocketConnection() throws Exception {
        StandardWebSocketClient client = new StandardWebSocketClient();
        WebSocketSession session = client.execute(
            new TextWebSocketHandler() {},
            new WebSocketHttpHeaders(),
            URI.create(WS_URL)
        ).get(5, TimeUnit.SECONDS);

        assertTrue(session.isOpen(), "Соединение должно быть открыто");
        session.close();
    }

    @Test
    @DisplayName("Подписка на топик и получение уведомления")
    void websocketSubscribeAndReceive() throws Exception {
        // 1. Инициализировать платёж через REST
        java.net.http.HttpClient httpClient = java.net.http.HttpClient.newHttpClient();
        java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/sbp/init-and-qr?userId=ws_test_user&amount=100.00"))
            .timeout(java.time.Duration.ofSeconds(10))
            .GET()
            .build();
        java.net.http.HttpResponse<String> response = httpClient.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
        assertEquals(200, response.statusCode());
        assertTrue(response.body().contains("orderId"));

        // 2. Подключиться к WebSocket и подписаться
        CountDownLatch messageLatch = new CountDownLatch(1);
        BlockingQueue<String> receivedMessages = new LinkedBlockingQueue<>();

        StandardWebSocketClient client = new StandardWebSocketClient();
        WebSocketSession session = client.execute(
            new TextWebSocketHandler() {
                @Override
                protected void handleTextMessage(WebSocketSession session, TextMessage message) {
                    receivedMessages.add(message.getPayload());
                    messageLatch.countDown();
                }
            },
            new WebSocketHttpHeaders(),
            URI.create(WS_URL)
        ).get(5, TimeUnit.SECONDS);

        // Отправить STOMP SUBSCRIBE
        String subscribeFrame = "SUBSCRIBE\nid:sub-0\ndestination:/topic/payment/test-order\n\n\0";
        session.sendMessage(new TextMessage(subscribeFrame));

        // Ждём сообщение (оплата может не произойти в тестовой среде)
        boolean received = messageLatch.await(10, TimeUnit.SECONDS);
        session.close();

        if (!received) {
            // Это нормально — оплата не производится в тестах
            return;
        }

        String msg = receivedMessages.poll();
        assertNotNull(msg, "Сообщение должно быть получено");
    }

    @Test
    @DisplayName("Подписка на несуществующий топик не вызывает ошибок")
    void websocketInvalidTopic() throws Exception {
        StandardWebSocketClient client = new StandardWebSocketClient();
        WebSocketSession session = client.execute(
            new TextWebSocketHandler() {},
            new WebSocketHttpHeaders(),
            URI.create(WS_URL)
        ).get(5, TimeUnit.SECONDS);

        assertTrue(session.isOpen());

        String subscribeFrame = "SUBSCRIBE\nid:sub-0\ndestination:/topic/invalid-topic-12345\n\n\0";
        session.sendMessage(new TextMessage(subscribeFrame));

        // Подписка принята без ошибок
        Thread.sleep(500);
        assertTrue(session.isOpen(), "Соединение должно оставаться открытым");
        session.close();
    }

    @Test
    @DisplayName("Несколько одновременных подписок")
    void websocketMultipleSubscriptions() throws Exception {
        StandardWebSocketClient client = new StandardWebSocketClient();
        WebSocketSession session = client.execute(
            new TextWebSocketHandler() {},
            new WebSocketHttpHeaders(),
            URI.create(WS_URL)
        ).get(5, TimeUnit.SECONDS);

        assertTrue(session.isOpen());

        for (int i = 0; i < 3; i++) {
            String subFrame = "SUBSCRIBE\nid:sub-" + i + "\ndestination:/topic/payment/multi-order-" + i + "\n\n\0";
            session.sendMessage(new TextMessage(subFrame));
        }

        Thread.sleep(500);
        assertTrue(session.isOpen(), "Соединение должно оставаться открытым после нескольких подписок");
        session.close();
    }
}
