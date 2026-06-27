package org.example.integration;

import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assumptions.*;

/**
 * Интеграционные тесты REST API платёжного сервиса.
 * Требуют запущенный сервер (BASE_URL).
 * Пропускаются автоматически, если сервер недоступен.
 */
@Tag("integration")
@TestMethodOrder(MethodOrderer.DisplayName.class)
class PaymentApiIntegrationTest {

    private static final String BASE_URL = System.getenv().getOrDefault("TEST_BASE_URL", "http://localhost:8080");
    private static HttpClient client;
    private static boolean serverAvailable;

    @BeforeAll
    static void checkServer() {
        client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/actuator/health"))
                .timeout(Duration.ofSeconds(3))
                .GET()
                .build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            serverAvailable = response.statusCode() == 200;
        } catch (Exception e) {
            serverAvailable = false;
        }
        assumeTrue(serverAvailable, "Сервер недоступен по адресу " + BASE_URL + " — интеграционные тесты пропущены");
    }

    private HttpResponse<String> get(String path) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + path))
            .timeout(Duration.ofSeconds(10))
            .GET()
            .build();
        return client.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> getInitAndQr(String userId, String amount) throws Exception {
        String query = "userId=" + userId + "&amount=" + amount;
        return get("/api/sbp/init-and-qr?" + query);
    }

    // === Smoke tests ===

    @Test
    @DisplayName("Инициализация платежа с корректными параметрами")
    void initPayment_success() throws Exception {
        HttpResponse<String> response = getInitAndQr("test_user_001", "100.50");
        assertEquals(200, response.statusCode());
        String body = response.body();
        assertTrue(body.contains("orderId"), "Ответ должен содержать orderId");
        assertTrue(body.contains("qrSvg"), "Ответ должен содержать qrSvg");
    }

    @Test
    @DisplayName("Инициализация платежа с минимальной суммой")
    void initPayment_minimalAmount() throws Exception {
        HttpResponse<String> response = getInitAndQr("test_user_002", "1.00");
        assertEquals(200, response.statusCode());
        assertTrue(response.body().contains("orderId"));
    }

    @Test
    @DisplayName("Инициализация платежа с большой суммой")
    void initPayment_largeAmount() throws Exception {
        HttpResponse<String> response = getInitAndQr("test_user_003", "999999.99");
        assertEquals(200, response.statusCode());
        assertTrue(response.body().contains("orderId"));
    }

    @Test
    @DisplayName("Health check возвращает 200")
    void healthCheck() throws Exception {
        HttpResponse<String> response = get("/actuator/health");
        assertEquals(200, response.statusCode());
    }

    // === Validation tests ===

    @Test
    @DisplayName("Ошибка при отсутствии userId — 400")
    void initPayment_missingUserId() throws Exception {
        HttpResponse<String> response = get("/api/sbp/init-and-qr?amount=100.50");
        assertEquals(400, response.statusCode());
    }

    @Test
    @DisplayName("Ошибка при отсутствии amount — 400")
    void initPayment_missingAmount() throws Exception {
        HttpResponse<String> response = get("/api/sbp/init-and-qr?userId=test_user_004");
        assertEquals(400, response.statusCode());
    }

    @Test
    @DisplayName("Ошибка при пустом userId — 400")
    void initPayment_emptyUserId() throws Exception {
        HttpResponse<String> response = getInitAndQr("", "100.50");
        assertEquals(400, response.statusCode());
    }

    @Test
    @DisplayName("Ошибка при отрицательной сумме — 400")
    void initPayment_negativeAmount() throws Exception {
        HttpResponse<String> response = getInitAndQr("test_user_005", "-50");
        assertEquals(400, response.statusCode());
    }

    @Test
    @DisplayName("Ошибка при нулевой сумме — 400")
    void initPayment_zeroAmount() throws Exception {
        HttpResponse<String> response = getInitAndQr("test_user_006", "0");
        assertEquals(400, response.statusCode());
    }

    @Test
    @DisplayName("Ошибка при невалидном типе amount — 400")
    void initPayment_invalidAmountType() throws Exception {
        HttpResponse<String> response = getInitAndQr("test_user_007", "not_a_number");
        assertEquals(400, response.statusCode());
    }

    // === Edge cases ===

    @ParameterizedTest
    @ValueSource(strings = {"<script>alert(1)</script>", "user with spaces", "user@#$%"})
    @DisplayName("userId со спецсимволами — допустимый ответ")
    void initPayment_specialCharsUserId(String userId) throws Exception {
        HttpResponse<String> response = getInitAndQr(userId, "100.50");
        assertTrue(response.statusCode() == 200 || response.statusCode() == 400,
            "Допустим ответ 200 или 400, получен: " + response.statusCode());
    }

    @Test
    @DisplayName("userId с длиной >1000 символов — допустимый ответ")
    void initPayment_veryLongUserId() throws Exception {
        String longUserId = "x".repeat(2000);
        HttpResponse<String> response = getInitAndQr(longUserId, "100.50");
        assertTrue(response.statusCode() == 200 || response.statusCode() == 400,
            "Допустим ответ 200 или 400, получен: " + response.statusCode());
    }

    @Test
    @DisplayName("Несуществующий endpoint — 404")
    void unknownEndpoint() throws Exception {
        HttpResponse<String> response = get("/api/nonexistent");
        assertEquals(404, response.statusCode());
    }

    @Test
    @DisplayName("Множественные запросы для одного userId")
    void concurrentSameUser() throws Exception {
        for (int i = 0; i < 5; i++) {
            HttpResponse<String> response = getInitAndQr("concurrent_user", String.valueOf(50 + i));
            assertEquals(200, response.statusCode());
            assertTrue(response.body().contains("orderId"));
        }
    }

    @Test
    @DisplayName("Структура JSON-ответа корректна")
    void responseFormat() throws Exception {
        HttpResponse<String> response = getInitAndQr("format_check_user", "250.00");
        assertEquals(200, response.statusCode());
        String body = response.body();
        assertTrue(body.contains("\"orderId\""), "Ответ должен содержать поле orderId");
        assertTrue(body.contains("\"qrSvg\""), "Ответ должен содержать поле qrSvg");
    }
}
