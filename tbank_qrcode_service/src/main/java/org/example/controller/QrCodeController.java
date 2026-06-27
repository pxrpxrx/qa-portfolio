/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.http.MediaType
 *  org.springframework.http.ResponseEntity
 *  org.springframework.web.bind.annotation.GetMapping
 *  org.springframework.web.bind.annotation.RequestParam
 *  org.springframework.web.bind.annotation.RestController
 */
package org.example.controller;

import java.util.Map;
import org.example.service.QrCodeService;
import org.example.service.TinkoffApiService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class QrCodeController {
    private final TinkoffApiService tinkoffApiService;
    private final QrCodeService qrCodeService;

    public QrCodeController(TinkoffApiService tinkoffApiService, QrCodeService qrCodeService) {
        this.tinkoffApiService = tinkoffApiService;
        this.qrCodeService = qrCodeService;
    }

    @GetMapping(value={"/api/qr/generate"}, produces={"image/png"})
    public ResponseEntity<byte[]> generateTbankQrCode(@RequestParam(value="amount") double amount, @RequestParam(value="email") String email) {
        try {
            String userId = "USER_FROM_SESSION_OR_AUTH";
            Map<String, Object> tinkoffResponse = this.tinkoffApiService.initCardPayment(amount, userId, email);
            String paymentUrl = (String)tinkoffResponse.get("PaymentUrl");
            String orderId = (String)tinkoffResponse.get("OrderId");
            if (paymentUrl == null) {
                throw new IllegalStateException("\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c PaymentURL \u043e\u0442 \u0422-\u0411\u0430\u043d\u043a\u0430. OrderId: " + orderId);
            }
            System.out.println("\u2705 QR Code: PaymentUrl \u043f\u043e\u043b\u0443\u0447\u0435\u043d \u0434\u043b\u044f OrderId: " + orderId);
            byte[] qrCodeImage = this.qrCodeService.generateQrCodeImage(paymentUrl, 350, 350);
            return ResponseEntity.ok().contentType(MediaType.IMAGE_PNG).body(qrCodeImage);
        }
        catch (IllegalArgumentException e) {
            System.err.println("Ошибка входных данных: " + e.getMessage());
            return ResponseEntity.badRequest().body(("Ошибка: " + e.getMessage()).getBytes());
        }
        catch (IllegalStateException e) {
            System.err.println("Критическая ошибка Init: " + e.getMessage());
            return ResponseEntity.status(503).body(e.getMessage().getBytes());
        }
        catch (Exception e) {
            System.err.println("\u041a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u0438 QR-\u043a\u043e\u0434\u0430: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.internalServerError().build();
        }
    }
}
