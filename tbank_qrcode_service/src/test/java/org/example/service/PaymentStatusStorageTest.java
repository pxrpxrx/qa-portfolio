package org.example.service;

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.HashOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.Duration;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit-тесты PaymentStatusStorage.
 * Проверяют работу с Redis (с моками).
 */
@ExtendWith(MockitoExtension.class)
class PaymentStatusStorageTest {

    @InjectMocks
    private PaymentStatusStorage paymentStatusStorage;

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    @Mock
    private HashOperations<String, Object, Object> hashOps;

    @BeforeEach
    void setUp() {
        lenient().when(redisTemplate.opsForValue()).thenReturn(valueOps);
        lenient().when(redisTemplate.opsForHash()).thenReturn(hashOps);
    }

    @Test
    @DisplayName("createNewStatus: сохраняет статус в Redis с TTL 30 минут")
    void createNewStatus_storesInRedis() {
        String orderId = "order-123";
        String status = "AWAITING_PAYMENT";
        String userId = "user-1";

        paymentStatusStorage.createNewStatus(orderId, status, userId);

        verify(valueOps, times(1)).set(eq("payment:status:order-123"), eq("AWAITING_PAYMENT"), eq(Duration.ofMinutes(30)));
    }

    @Test
    @DisplayName("updateStatus: обновляет статус, если текущий не финальный")
    void updateStatus_nonFinalStatus_updates() {
        String orderId = "order-123";
        String newStatus = "CONFIRMED";

        when(valueOps.get("payment:status:order-123")).thenReturn("AWAITING_PAYMENT");

        paymentStatusStorage.updateStatus(orderId, newStatus);

        verify(valueOps, times(1)).set(eq("payment:status:order-123"), eq("CONFIRMED"), eq(Duration.ofMinutes(30)));
    }

    @Test
    @DisplayName("updateStatus: не обновляет, если текущий статус финальный")
    void updateStatus_finalStatus_skipsUpdate() {
        String orderId = "order-123";
        String newStatus = "CONFIRMED";

        when(valueOps.get("payment:status:order-123")).thenReturn("CONFIRMED");

        paymentStatusStorage.updateStatus(orderId, newStatus);

        // Не должен вызываться set, так как статус уже финальный
        verify(valueOps, never()).set(eq("payment:status:order-123"), eq("CONFIRMED"), any());
    }

    @Test
    @DisplayName("getStatus: возвращает статус из Redis")
    void getStatus_returnsFromRedis() {
        String orderId = "order-123";
        String expectedStatus = "AWAITING_PAYMENT";

        when(valueOps.get("payment:status:order-123")).thenReturn(expectedStatus);

        String actualStatus = paymentStatusStorage.getStatus(orderId);

        assertEquals(expectedStatus, actualStatus);
    }

    @Test
    @DisplayName("deleteStatus: удаляет статус и метаданные из Redis")
    void deleteStatus_removesFromRedis() {
        String orderId = "order-123";

        paymentStatusStorage.deleteStatus(orderId);

        verify(redisTemplate, times(1)).delete("payment:status:order-123");
        verify(redisTemplate, times(1)).delete("payment:meta:order-123");
    }

    @Test
    @DisplayName("saveMetadata: сохраняет userId и email в Redis hash")
    void saveMetadata_storesInRedisHash() {
        String orderId = "order-123";
        String userId = "user-1";
        String email = "test@mail.com";

        paymentStatusStorage.saveMetadata(orderId, userId, email);

        verify(redisTemplate.opsForHash(), times(1)).put(eq("payment:meta:order-123"), eq("userId"), eq("user-1"));
        verify(redisTemplate.opsForHash(), times(1)).put(eq("payment:meta:order-123"), eq("email"), eq("test@mail.com"));
        verify(redisTemplate, times(1)).expire(eq("payment:meta:order-123"), eq(Duration.ofHours(24)));
    }

    @Test
    @DisplayName("getMetadata: возвращает метаданные из Redis")
    void getMetadata_returnsFromRedis() {
        String orderId = "order-123";
        Map<Object, Object> expectedMetadata = Map.of((Object)"userId", (Object)"user-1", (Object)"email", (Object)"test@mail.com");

        when(redisTemplate.opsForHash().entries("payment:meta:order-123"))
            .thenReturn(expectedMetadata);

        Map<String, String> actualMetadata = paymentStatusStorage.getMetadata(orderId);

        assertEquals("user-1", actualMetadata.get("userId"));
        assertEquals("test@mail.com", actualMetadata.get("email"));
    }
}
