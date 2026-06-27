/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.http.ResponseEntity
 *  org.springframework.web.bind.annotation.GetMapping
 *  org.springframework.web.bind.annotation.RequestParam
 *  org.springframework.web.bind.annotation.RestController
 */
package org.example.controller;

import java.util.Map;
import org.example.service.TinkoffApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class QrSbpController {
    private final TinkoffApiService tinkoffApiService;

    public QrSbpController(TinkoffApiService tinkoffApiService) {
        this.tinkoffApiService = tinkoffApiService;
    }

    @GetMapping(value={"/api/sbp/init-and-qr"}, produces={"application/json"})
    public ResponseEntity<?> getSbpQrCode(@RequestParam(value="userId") String userId, @RequestParam(value="amount") double amount, @RequestParam(value="email") String email) {
        try {
            Map<String, Object> initResponse = this.tinkoffApiService.initCardPayment(amount, userId, email);
            if (!Boolean.TRUE.equals(initResponse.get("Success"))) {
                return ResponseEntity.badRequest().body(Map.of("status", "ERROR", "message", initResponse.getOrDefault("Message", "\u041e\u0448\u0438\u0431\u043a\u0430 Init")));
            }
            String paymentId = String.valueOf(initResponse.get("PaymentId"));
            String orderId = String.valueOf(initResponse.get("OrderId"));
            Map<String, Object> qrResponse = this.tinkoffApiService.getQrCode(paymentId, "IMAGE");
            if (Boolean.TRUE.equals(qrResponse.get("Success"))) {
                String svgData = (String)qrResponse.get("Data");
                return ResponseEntity.ok(Map.of("status", "SUCCESS", "qrSvg", svgData, "orderId", orderId));
            }
            return ResponseEntity.internalServerError().body(Map.of("status", "ERROR", "message", "\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u044f QR"));
        }
        catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError().body(Map.of("status", "ERROR", "message", e.getMessage()));
        }
    }
}
