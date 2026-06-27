/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.fasterxml.jackson.databind.ObjectMapper
 *  org.apache.hc.client5.http.classic.methods.HttpPost
 *  org.apache.hc.client5.http.impl.classic.CloseableHttpClient
 *  org.apache.hc.client5.http.impl.classic.HttpClients
 *  org.apache.hc.core5.http.ClassicHttpRequest
 *  org.apache.hc.core5.http.HttpEntity
 *  org.apache.hc.core5.http.io.entity.EntityUtils
 *  org.apache.hc.core5.http.io.entity.StringEntity
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.beans.factory.annotation.Value
 *  org.springframework.stereotype.Service
 */
package org.example.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ClassicHttpRequest;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.example.service.PaymentStatusStorage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class TinkoffApiService {
    @Autowired
    private PaymentStatusStorage paymentStatusStorage;
    @Value(value="${tinkoff.api.url}")
    private String apiUrl;
    @Value(value="${tinkoff.terminal.key}")
    private String terminalKey;
    @Value(value="${tinkoff.secret.key}")
    private String secretKey;
    private final ObjectMapper mapper = new ObjectMapper();

    public Map<String, Object> initCardPayment(double amount, String userId, String email) throws Exception {
        if (amount <= 0.0) {
            throw new IllegalArgumentException("\u0421\u0443\u043c\u043c\u0430 \u0434\u043e\u043b\u0436\u043d\u0430 \u0431\u044b\u0442\u044c > 0");
        }
        long amountKopecks = Math.round(amount * 100.0);
        String orderId = UUID.randomUUID().toString().substring(0, 10);
        try {
            System.out.println("-> [Redis] \u0417\u0430\u043f\u0438\u0441\u044c \u0441\u0442\u0430\u0442\u0443\u0441\u0430 \u0434\u043b\u044f OrderId: " + orderId);
            this.paymentStatusStorage.createNewStatus(orderId, "AWAITING_PAYMENT", userId);
            this.paymentStatusStorage.saveMetadata(orderId, userId, email);
        }
        catch (Exception e) {
            System.err.println("\u274c \u041e\u0428\u0418\u0411\u041a\u0410 REDIS: " + e.getMessage());
            throw new RuntimeException("\u041e\u0448\u0438\u0431\u043a\u0430 Redis: " + e.getMessage(), e);
        }
        LinkedHashMap<String, String> dataMap = new LinkedHashMap<String, String>();
        dataMap.put("userId", userId);
        dataMap.put("orderId", orderId);
        dataMap.put("email", email);
        LinkedHashMap<String, Object> body = new LinkedHashMap<String, Object>();
        body.put("TerminalKey", this.terminalKey);
        body.put("Amount", amountKopecks);
        body.put("OrderId", orderId);
        body.put("Description", "\u041e\u043f\u043b\u0430\u0442\u0430 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0438 \u0434\u043b\u044f User ID: " + userId);
        body.put("PayType", "O");
        body.put("DATA", dataMap);
        body.put("Receipt", this.createReceipt(amountKopecks, email));
        String token = this.generateToken(body);
        body.put("Token", token);
        System.out.println("\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430 Init JSON: " + this.mapper.writeValueAsString(body));
        String json = this.executePost(this.apiUrl + "Init", body);
        Map resp = (Map)this.mapper.readValue(json, Map.class);
        if (Boolean.TRUE.equals(resp.get("Success"))) {
            resp.put("OrderId", orderId);
            return resp;
        }
        this.paymentStatusStorage.deleteStatus(orderId);
        throw new RuntimeException("\u041e\u0448\u0438\u0431\u043a\u0430 Init: " + json);
    }

    public Map<String, Object> getQrCode(String paymentId, String dataType) throws Exception {
        LinkedHashMap<String, Object> body = new LinkedHashMap<String, Object>();
        body.put("TerminalKey", this.terminalKey);
        body.put("PaymentId", paymentId);
        body.put("DataType", dataType.toUpperCase());
        String token = this.generateToken(body);
        body.put("Token", token);
        String json = this.executePost(this.apiUrl + "GetQr", body);
        Map resp = (Map)this.mapper.readValue(json, Map.class);
        if (Boolean.TRUE.equals(resp.get("Success"))) {
            return resp;
        }
        throw new RuntimeException("\u041e\u0448\u0438\u0431\u043a\u0430 GetQr: " + String.valueOf(resp.get("Message")));
    }

    private String generateToken(Map<String, Object> allParams) throws Exception {
        HashMap<String, Object> flat = new HashMap<String, Object>();
        for (Map.Entry<String, Object> e : allParams.entrySet()) {
            String key = e.getKey();
            Object value = e.getValue();
            if ("Token".equals(key) || value instanceof Map || value instanceof List) continue;
            flat.put(key, value);
        }
        flat.put("Password", this.secretKey);
        TreeMap sorted = new TreeMap(Comparator.naturalOrder());
        sorted.putAll(flat);
        StringBuilder sb = new StringBuilder();
        sorted.values().forEach(v -> {
            if (v != null) {
                sb.append(String.valueOf(v));
            }
        });
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] hash = md.digest(sb.toString().getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (byte b : hash) {
            hex.append(String.format("%02x", b));
        }
        return hex.toString();
    }

    private String executePost(String url, Map<String, Object> body) throws Exception {
        try (CloseableHttpClient http = HttpClients.createDefault();){
            HttpPost post = new HttpPost(url);
            post.addHeader("Content-Type", (Object)"application/json");
            String json = this.mapper.writeValueAsString(body);
            post.setEntity((HttpEntity)new StringEntity(json, StandardCharsets.UTF_8));
            String string = (String)http.execute((ClassicHttpRequest)post, response -> EntityUtils.toString((HttpEntity)response.getEntity()));
            return string;
        }
    }

    private Map<String, Object> createReceipt(long amountKopecks, String email) {
        HashMap<String, Object> receipt = new HashMap<String, Object>();
        receipt.put("Email", email != null && !email.isEmpty() ? email : "test@example.com");
        receipt.put("Taxation", "usn_income");
        HashMap<String, Object> item = new HashMap<String, Object>();
        item.put("Name", "\u041f\u043e\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0431\u0430\u043b\u0430\u043d\u0441\u0430");
        item.put("Price", amountKopecks);
        item.put("Quantity", 1);
        item.put("Amount", amountKopecks);
        item.put("PaymentMethod", "full_payment");
        item.put("PaymentObject", "service");
        item.put("Tax", "none");
        receipt.put("Items", Collections.singletonList(item));
        return receipt;
    }
}
