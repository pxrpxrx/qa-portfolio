/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.beans.factory.annotation.Value
 *  org.springframework.data.redis.core.StringRedisTemplate
 *  org.springframework.http.ResponseEntity
 *  org.springframework.web.bind.annotation.PostMapping
 *  org.springframework.web.bind.annotation.RequestBody
 *  org.springframework.web.bind.annotation.RestController
 */
package org.example.service;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.TimeUnit;
import org.example.entity.PaymentEntity;
import org.example.repository.PaymentRepository;
import org.example.service.PaymentStatusStorage;
import org.example.service.WebSocketNotificationService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class TinkoffNotificationController {
    @Value(value="${tinkoff.secret.key}")
    private String secretKey;
    private final StringRedisTemplate redisTemplate;
    private final PaymentStatusStorage paymentStatusStorage;
    private final WebSocketNotificationService notificationService;
    private final PaymentRepository paymentRepository;
    private static final long REDIS_KEY_TTL_DAYS = 7L;
    private static final String REDIS_PREFIX = "tinkoff:notify:";

    public TinkoffNotificationController(StringRedisTemplate redisTemplate, PaymentStatusStorage paymentStatusStorage, WebSocketNotificationService notificationService, PaymentRepository paymentRepository) {
        this.redisTemplate = redisTemplate;
        this.paymentStatusStorage = paymentStatusStorage;
        this.notificationService = notificationService;
        this.paymentRepository = paymentRepository;
    }

    @PostMapping(value={"/tinkoff/notify"}, consumes={"application/json"}, produces={"text/plain"})
    public ResponseEntity<String> handleNotification(@RequestBody Map<String, Object> notification) {
        System.out.println("\n--- \u041f\u041e\u041b\u0423\u0427\u0415\u041d\u041e \u0423\u0412\u0415\u0414\u041e\u041c\u041b\u0415\u041d\u0418\u0415 \u041e\u0422 \u0422-\u0411\u0410\u041d\u041a\u0410 ---");
        Object orderIdObj = notification.get("OrderId");
        Object paymentIdObj = notification.get("PaymentId");
        String orderId = orderIdObj != null ? String.valueOf(orderIdObj) : null;
        String paymentId = paymentIdObj != null ? String.valueOf(paymentIdObj) : null;
        String status = (String)notification.get("Status");
        if (orderId == null || status == null) {
            System.err.println("❌ ОШИБКА: Отсутствуют OrderId или Status.");
            return ResponseEntity.status(400).body("Missing required data");
        }
        String uniqueKey = REDIS_PREFIX + (paymentId != null ? paymentId : orderId) + ":" + status;
        Boolean isNewNotification = this.redisTemplate.opsForValue().setIfAbsent(uniqueKey, "processed", 7L, TimeUnit.DAYS);
        if (Boolean.FALSE.equals(isNewNotification)) {
            System.out.println("⚠️ УВЕДОМЛЕНИЕ ПОВТОРНОЕ (" + status + "). Пропускаем.");
            return ResponseEntity.ok("OK");
        }
        try {
            String receivedToken = (String)notification.get("Token");
            String calculatedToken = this.calculateNotificationToken(notification);
            if (!calculatedToken.equalsIgnoreCase(receivedToken)) {
                System.err.println("❌ ОШИБКА БЕЗОПАСНОСТИ: Токен не совпадает!");
                this.redisTemplate.delete(uniqueKey);
                return ResponseEntity.status(403).body("Invalid Token");
            }
            System.out.println("\u2705 \u041e\u0411\u0420\u0410\u0411\u041e\u0422\u041a\u0410 \u0421\u0422\u0410\u0422\u0423\u0421\u0410: " + status);
            if ("CONFIRMED".equalsIgnoreCase(status)) {
                try {
                    Map<String, String> meta;
                    PaymentEntity payment = this.paymentRepository.findByOrderId(orderId).orElse(new PaymentEntity());
                    payment.setOrderId(orderId);
                    payment.setPaymentId(paymentId);
                    payment.setPaymentDate(LocalDateTime.now());
                    Object amountObj = notification.get("Amount");
                    if (amountObj != null) {
                        payment.setAmount(new BigDecimal(amountObj.toString()).divide(new BigDecimal(100)));
                    }
                    if ((meta = this.paymentStatusStorage.getMetadata(orderId)) != null && !meta.isEmpty()) {
                        payment.setClientId(meta.get("userId"));
                        payment.setEmail(meta.get("email"));
                        System.out.println("\ud83d\udd17 \u041c\u0435\u0442\u0430\u0434\u0430\u043d\u043d\u044b\u0435 \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u044b \u0438\u0437 Redis (userId: " + meta.get("userId") + ")");
                    } else {
                        System.err.println("\ud83d\udea8 \u041f\u0420\u0415\u0414\u0423\u041f\u0420\u0415\u0416\u0414\u0415\u041d\u0418\u0415: \u041c\u0435\u0442\u0430\u0434\u0430\u043d\u043d\u044b\u0435 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b \u0432 Redis \u0434\u043b\u044f " + orderId);
                    }
                    this.paymentRepository.save(payment);
                    System.out.println("\ud83d\udcbe \u0414\u0430\u043d\u043d\u044b\u0435 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b \u0432 \u0411\u0414 \u0434\u043b\u044f OrderId: " + orderId);
                }
                catch (Exception dbEx) {
                    System.err.println("\u26a0\ufe0f \u041e\u0448\u0438\u0431\u043a\u0430 \u0411\u0414 \u043f\u0440\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0438: " + dbEx.getMessage());
                }
            }
            String statusForRedis = status;
            if ("REJECTED".equalsIgnoreCase(status) || "AUTH_FAIL".equalsIgnoreCase(status)) {
                statusForRedis = "REJECTED";
            }
            this.paymentStatusStorage.updateStatus(orderId, statusForRedis);
            this.notificationService.notifyClientStatusUpdate(orderId, statusForRedis);
            return ResponseEntity.ok("OK");
        }
        catch (Exception e) {
            System.err.println("Критическая ошибка обработки: " + e.getMessage());
            e.printStackTrace();
            this.redisTemplate.delete(uniqueKey);
            return ResponseEntity.status(500).body("Internal Error");
        }
    }

    private String calculateNotificationToken(Map<String, Object> params) throws Exception {
        HashMap<String, Object> flat = new HashMap<String, Object>();
        for (Map.Entry<String, Object> e : params.entrySet()) {
            if ("Token".equalsIgnoreCase(e.getKey()) || e.getValue() instanceof Map || e.getValue() instanceof List) continue;
            flat.put(e.getKey(), e.getValue());
        }
        flat.put("Password", this.secretKey);
        TreeMap<String, Object> sorted = new TreeMap<String, Object>(String.CASE_INSENSITIVE_ORDER);
        sorted.putAll(flat);
        StringBuilder sb = new StringBuilder();
        sorted.values().forEach(v -> {
            if (v != null) {
                sb.append(v);
            }
        });
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] hash = md.digest(sb.toString().getBytes(StandardCharsets.UTF_8));
        StringBuilder hexString = new StringBuilder();
        for (byte b : hash) {
            hexString.append(String.format("%02x", b));
        }
        return hexString.toString();
    }
}
