/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.fasterxml.jackson.databind.ObjectMapper
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.web.bind.annotation.CrossOrigin
 *  org.springframework.web.bind.annotation.GetMapping
 *  org.springframework.web.bind.annotation.RequestParam
 *  org.springframework.web.bind.annotation.RestController
 */
package org.example.web;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import org.example.dto.PaymentInitResponse;
import org.example.service.TinkoffApiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@CrossOrigin(origins={"http://localhost:63342"})
public class PaymentController {
    @Autowired
    private TinkoffApiService tinkoffApiService;
    private final ObjectMapper mapper = new ObjectMapper();

    @GetMapping(value={"/api/card/init"})
    public PaymentInitResponse initPayment(@RequestParam(value="userId") String userId, @RequestParam(value="amount") double amount, @RequestParam(value="email") String email) {
        System.out.println("\n>>> 1. \u041a\u041e\u041d\u0422\u0420\u041e\u041b\u041b\u0415\u0420 \u041f\u041e\u041b\u0423\u0427\u0418\u041b \u0417\u0410\u041f\u0420\u041e\u0421! UserID: " + userId + ", Amount: " + amount + ", Email: " + email);
        String orderId = null;
        try {
            Map<String, Object> tinkoffResponse = this.tinkoffApiService.initCardPayment(amount, userId, email);
            System.out.println("====== RESPONSE BODY (FROM TINKOFF) ======");
            System.out.println(this.mapper.writerWithDefaultPrettyPrinter().writeValueAsString(tinkoffResponse));
            orderId = (String)tinkoffResponse.get("OrderId");
            String paymentUrl = (String)tinkoffResponse.get("PaymentURL");
            String status = (String)tinkoffResponse.get("Status");
            String details = (String)tinkoffResponse.get("Details");
            if ("NEW".equalsIgnoreCase(status) && paymentUrl != null) {
                return new PaymentInitResponse(paymentUrl, orderId);
            }
            String errorMessage = details != null ? details : (String)tinkoffResponse.get("Message");
            System.err.println("\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043e\u0442\u0432\u0435\u0442\u0430 \u0422-\u0411\u0430\u043d\u043a\u0430. \u0421\u0442\u0430\u0442\u0443\u0441: " + status + ", \u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435: " + errorMessage);
            return new PaymentInitResponse("\u041e\u0448\u0438\u0431\u043a\u0430 \u0422-\u0411\u0430\u043d\u043a\u0430: " + (errorMessage != null ? errorMessage : "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430."), orderId, true);
        }
        catch (IllegalArgumentException e) {
            System.err.println("\u041e\u0448\u0438\u0431\u043a\u0430 \u0432\u0445\u043e\u0434\u043d\u044b\u0445 \u0434\u0430\u043d\u043d\u044b\u0445: " + e.getMessage());
            return new PaymentInitResponse("\u041d\u0435\u0432\u0435\u0440\u043d\u0430\u044f \u0441\u0443\u043c\u043c\u0430: " + e.getMessage(), 400);
        }
        catch (Exception e) {
            System.err.println("\u041a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0438\u043d\u0438\u0446\u0438\u0430\u0446\u0438\u0438 \u043f\u043b\u0430\u0442\u0435\u0436\u0430: " + e.getMessage());
            e.printStackTrace();
            return new PaymentInitResponse("\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0430: " + e.getMessage(), 500);
        }
    }
}
