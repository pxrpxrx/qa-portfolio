package org.example.controller;

import org.example.service.TinkoffApiService;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit-тесты SbpController.
 * Проверяют обработку запросов инициализации СБП.
 */
@ExtendWith(MockitoExtension.class)
class SbpControllerTest {

    @InjectMocks
    private SbpController sbpController;

    @Mock
    private TinkoffApiService tinkoffApiService;

    @Test
    @DisplayName("initSbpQrAndGetId: успешная инициализация возвращает orderId и qrSvg")
    void initSbpQrAndGetId_success() throws Exception {
        // Arrange
        String userId = "test_user";
        double amount = 500.0;
        String email = "test@mail.com";

        Map<String, Object> initResponse = Map.of(
            "Success", true,
            "OrderId", "order-123",
            "PaymentId", "payment-456"
        );
        Map<String, Object> qrResponse = Map.of(
            "Success", true,
            "Data", "<svg>QR Code</svg>"
        );

        when(tinkoffApiService.initCardPayment(eq(amount), eq(userId), eq(email)))
            .thenReturn(initResponse);
        when(tinkoffApiService.getQrCode(eq("payment-456"), eq("IMAGE")))
            .thenReturn(qrResponse);

        // Act
        Map<String, String> response = sbpController.initSbpQrAndGetId(userId, amount, email);

        // Assert
        assertEquals("SUCCESS", response.get("status"));
        assertEquals("order-123", response.get("orderId"));
        assertEquals("<svg>QR Code</svg>", response.get("qrSvg"));
    }

    @Test
    @DisplayName("initSbpQrAndGetId: ошибка Tinkoff Init возвращает ERROR")
    void initSbpQrAndGetId_tinkoffInitError() throws Exception {
        // Arrange
        String userId = "test_user";
        double amount = 500.0;
        String email = "test@mail.com";

        Map<String, Object> initResponse = Map.of(
            "Success", false,
            "Message", "Invalid terminal key"
        );

        when(tinkoffApiService.initCardPayment(eq(amount), eq(userId), eq(email)))
            .thenReturn(initResponse);

        // Act
        Map<String, String> response = sbpController.initSbpQrAndGetId(userId, amount, email);

        // Assert
        assertEquals("ERROR", response.get("status"));
        assertTrue(response.get("message").contains("Tinkoff Init failed"));
    }

    @Test
    @DisplayName("initSbpQrAndGetId: ошибка Tinkoff GetQr возвращает ERROR")
    void initSbpQrAndGetId_tinkoffGetQrError() throws Exception {
        // Arrange
        String userId = "test_user";
        double amount = 500.0;
        String email = "test@mail.com";

        Map<String, Object> initResponse = Map.of(
            "Success", true,
            "OrderId", "order-123",
            "PaymentId", "payment-456"
        );
        Map<String, Object> qrResponse = Map.of(
            "Success", false,
            "Message", "Invalid PaymentId"
        );

        when(tinkoffApiService.initCardPayment(eq(amount), eq(userId), eq(email)))
            .thenReturn(initResponse);
        when(tinkoffApiService.getQrCode(eq("payment-456"), eq("IMAGE")))
            .thenReturn(qrResponse);

        // Act
        Map<String, String> response = sbpController.initSbpQrAndGetId(userId, amount, email);

        // Assert
        assertEquals("ERROR", response.get("status"));
        assertTrue(response.get("message").contains("Tinkoff GetQr failed"));
    }

    @Test
    @DisplayName("initSbpQrAndGetId: исключение в сервисе возвращает ERROR с UNKNOWN orderId")
    void initSbpQrAndGetId_serviceException() throws Exception {
        // Arrange
        String userId = "test_user";
        double amount = 500.0;
        String email = "test@mail.com";

        when(tinkoffApiService.initCardPayment(eq(amount), eq(userId), eq(email)))
            .thenThrow(new RuntimeException("Network error"));

        // Act
        Map<String, String> response = sbpController.initSbpQrAndGetId(userId, amount, email);

        // Assert
        assertEquals("ERROR", response.get("status"));
        assertEquals("UNKNOWN", response.get("orderId"));
    }
}
