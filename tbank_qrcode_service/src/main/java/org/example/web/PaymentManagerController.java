/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.web.bind.annotation.PostMapping
 *  org.springframework.web.bind.annotation.RequestBody
 *  org.springframework.web.bind.annotation.RequestMapping
 *  org.springframework.web.bind.annotation.RestController
 */
package org.example.web;

import java.util.HashMap;
import java.util.Map;
import org.example.dto.PaymentManagerRequest;
import org.example.service.QrCodeService;
import org.example.service.TinkoffApiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(value={"/api/v1/manager/payment"})
public class PaymentManagerController {
    @Autowired
    private TinkoffApiService tinkoffApiService;
    @Autowired
    private QrCodeService qrCodeService;

    @PostMapping(value={"/init"})
    public Map<String, Object> initiatePaymentAndGetQr(@RequestBody PaymentManagerRequest request) {
        HashMap<String, Object> response = new HashMap<String, Object>();
        try {
            Map<String, Object> tinkoffResponse = this.tinkoffApiService.initCardPayment(request.getAmount(), request.getUserId(), request.getEmail());
            String paymentUrl = (String)tinkoffResponse.get("PaymentUrl");
            String orderId = (String)tinkoffResponse.get("OrderId");
            if (paymentUrl == null || orderId == null) {
                throw new IllegalStateException("\u041e\u0442\u0432\u0435\u0442 \u0422-\u0411\u0430\u043d\u043a\u0430 \u043d\u0435 \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 PaymentUrl \u0438\u043b\u0438 OrderId.");
            }
            String qrCodeBase64 = this.qrCodeService.generateQrCodeBase64(paymentUrl, 300, 300);
            response.put("status", "SUCCESS");
            response.put("paymentUrl", paymentUrl);
            response.put("orderId", orderId);
            response.put("qrCodeBase64", qrCodeBase64);
            response.put("message", "\u041f\u043b\u0430\u0442\u0435\u0436 \u0438\u043d\u0438\u0446\u0438\u0438\u0440\u043e\u0432\u0430\u043d. \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 Base64 \u0441\u0442\u0440\u043e\u043a\u0443 \u0434\u043b\u044f \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f QR-\u043a\u043e\u0434\u0430.");
        }
        catch (Exception e) {
            System.err.println("--- \ud83d\udd34 \u041e\u0428\u0418\u0411\u041a\u0410 API \u041c\u0415\u041d\u0415\u0414\u0416\u0415\u0420\u0410: " + e.getMessage());
            e.printStackTrace();
            response.put("status", "ERROR");
            response.put("message", "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043f\u0440\u0438 \u0438\u043d\u0438\u0446\u0438\u0430\u0446\u0438\u0438: " + e.getMessage());
        }
        return response;
    }
}
