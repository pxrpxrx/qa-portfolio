/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.web.bind.annotation.CrossOrigin
 *  org.springframework.web.bind.annotation.GetMapping
 *  org.springframework.web.bind.annotation.RequestParam
 *  org.springframework.web.bind.annotation.RestController
 */
package org.example.controller;

import java.util.HashMap;
import java.util.Map;
import org.example.service.TinkoffApiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@CrossOrigin(origins={"http://localhost:63342"})
public class SbpController {
    private final TinkoffApiService tinkoffApiService;

    @Autowired
    public SbpController(TinkoffApiService tinkoffApiService) {
        this.tinkoffApiService = tinkoffApiService;
    }

    @GetMapping(value={"/api/sbp/init-and-qr"})
    public Map<String, String> initSbpQrAndGetId(@RequestParam(value="userId") String userId, @RequestParam(value="amount") double amount, @RequestParam(value="email") String email) {
        HashMap<String, String> response = new HashMap<String, String>();
        String rawOrderId = null;
        String paymentId = null;
        try {
            System.out.println(">>> SBP: \u0417\u0430\u043f\u0440\u043e\u0441 Init \u043f\u043e\u043b\u0443\u0447\u0435\u043d. UserID: " + userId + ", Amount: " + amount + ", Email: " + email);
            Map<String, Object> initResponse = this.tinkoffApiService.initCardPayment(amount, userId, email);
            if (!Boolean.TRUE.equals(initResponse.get("Success"))) {
                String message = (String)initResponse.get("Message");
                throw new IllegalStateException("Tinkoff Init failed: " + (message != null ? message : "\u041e\u0448\u0438\u0431\u043a\u0430 Init."));
            }
            rawOrderId = (String)initResponse.get("OrderId");
            paymentId = String.valueOf(initResponse.get("PaymentId"));
            System.out.println(">>> SBP: Init \u0443\u0441\u043f\u0435\u0448\u0435\u043d. OrderId: " + rawOrderId);
            Map<String, Object> qrResponse = this.tinkoffApiService.getQrCode(paymentId, "IMAGE");
            if (Boolean.TRUE.equals(qrResponse.get("Success"))) {
                String svgData = (String)qrResponse.get("Data");
                response.put("status", "SUCCESS");
                response.put("orderId", rawOrderId);
                response.put("qrSvg", svgData);
                return response;
            }
            throw new IllegalStateException("Tinkoff GetQr failed.");
        }
        catch (Exception e) {
            System.err.println("\u274c \u041e\u0428\u0418\u0411\u041a\u0410 SBP: " + e.getMessage());
            response.put("status", "ERROR");
            response.put("message", e.getMessage());
            response.put("orderId", rawOrderId != null ? rawOrderId : "UNKNOWN");
            return response;
        }
    }
}
