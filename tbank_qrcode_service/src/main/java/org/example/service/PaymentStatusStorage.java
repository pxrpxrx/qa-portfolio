/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.data.redis.core.StringRedisTemplate
 *  org.springframework.stereotype.Service
 */
package org.example.service;

import java.time.Duration;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class PaymentStatusStorage {
    @Autowired
    private StringRedisTemplate redisTemplate;
    private static final Duration TTL_DURATION = Duration.ofMinutes(30L);
    private static final Duration META_TTL_DURATION = Duration.ofHours(24L);
    private static final String KEY_PREFIX = "payment:status:";
    private static final String META_PREFIX = "payment:meta:";
    private static final Set<String> FINAL_STATUSES = Set.of("CONFIRMED", "REJECTED", "REFUNDED", "CANCELED");

    private String buildKey(String orderId) {
        return KEY_PREFIX + orderId;
    }

    private String buildMetaKey(String orderId) {
        return META_PREFIX + orderId;
    }

    public void createNewStatus(String orderId, String initialStatus, String userId) {
        String key = this.buildKey(orderId);
        this.redisTemplate.opsForValue().set(key, initialStatus, TTL_DURATION);
        System.out.println("Создан новый статус в Redis для OrderId: " + orderId + " (" + initialStatus + ")");
    }

    public void updateStatus(String orderId, String newStatus) {
        String key = this.buildKey(orderId);
        String currentStatus = this.redisTemplate.opsForValue().get(key);
        if (currentStatus != null && FINAL_STATUSES.contains(currentStatus.toUpperCase())) {
            System.out.println("⚠️ Пропуск обновления: OrderId " + orderId + " уже имеет финальный статус [" + currentStatus + "].");
            return;
        }
        this.redisTemplate.opsForValue().set(key, newStatus, TTL_DURATION);
        System.out.println("Обновлен статус в Redis для OrderId: " + orderId + " на: " + newStatus);
    }

    public String getStatus(String orderId) {
        return this.redisTemplate.opsForValue().get(this.buildKey(orderId));
    }

    public void deleteStatus(String orderId) {
        this.redisTemplate.delete(this.buildKey(orderId));
        this.redisTemplate.delete(this.buildMetaKey(orderId));
        System.out.println("Все данные для OrderId " + orderId + " удалены из Redis.");
    }

    public void saveMetadata(String orderId, String userId, String email) {
        String key = this.buildMetaKey(orderId);
        if (userId != null) {
            this.redisTemplate.opsForHash().put(key, "userId", userId);
        }
        if (email != null) {
            this.redisTemplate.opsForHash().put(key, "email", email);
        }
        this.redisTemplate.expire(key, META_TTL_DURATION);
        System.out.println("✅ Метаданные сохранены в Redis для OrderId: " + orderId);
    }

    public Map<String, String> getMetadata(String orderId) {
        String key = this.buildMetaKey(orderId);
        Map<Object, Object> entries = this.redisTemplate.opsForHash().entries(key);
        return entries.entrySet().stream().collect(Collectors.toMap(e -> String.valueOf(e.getKey()), e -> String.valueOf(e.getValue())));
    }
}
