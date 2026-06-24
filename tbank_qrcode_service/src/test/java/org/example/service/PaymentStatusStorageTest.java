package org.example.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.Duration;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PaymentStatusStorageTest {

    @InjectMocks
    private PaymentStatusStorage paymentStatusStorage;

    @Mock
    private RedisTemplate<String, String> redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOperations;

    @Test
    void saveStatus_ShouldStoreInRedis() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);

        paymentStatusStorage.saveStatus("order-001", "NEW");

        verify(valueOperations).set(
            eq("payment:status:order-001"),
            eq("NEW"),
            any(Duration.class));
    }

    @Test
    void getStatus_WhenExists_ShouldReturnStatus() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("payment:status:order-001")).thenReturn("CONFIRMED");

        Optional<String> result = paymentStatusStorage.getStatus("order-001");

        assertTrue(result.isPresent());
        assertEquals("CONFIRMED", result.get());
    }

    @Test
    void getStatus_WhenNotExists_ShouldReturnEmpty() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("payment:status:non-existent")).thenReturn(null);

        Optional<String> result = paymentStatusStorage.getStatus("non-existent");

        assertFalse(result.isPresent());
    }
}
