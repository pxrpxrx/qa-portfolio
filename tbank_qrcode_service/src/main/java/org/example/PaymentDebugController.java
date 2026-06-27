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
package org.example;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import org.example.dto.PaymentInitResponse;
import org.example.service.TinkoffApiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@CrossOrigin(origins={"*"})
@RestController
public class PaymentDebugController {
    @Autowired
    private TinkoffApiService tinkoffApiService;

    @GetMapping(value={"/pay/init-debug"})
    public PaymentInitResponse initPaymentDebug(@RequestParam(name="amount", defaultValue="1000.00") double amount, @RequestParam(name="userId", defaultValue="DEBUG_DEFAULT_USER") String userId, @RequestParam(value="email") String email) {
        System.out.println("\n--- \ud83d\udfe2 DEBUG: \u0418\u041d\u0418\u0426\u0418\u0410\u0426\u0418\u042f \u041f\u041b\u0410\u0422\u0415\u0416\u0410 ---");
        System.out.println("DEBUG: UserID: " + userId + ", Amount: " + amount + ", Email: " + email);
        String orderId = null;
        try {
            if (this.tinkoffApiService == null) {
                throw new IllegalStateException("\u0421\u0415\u0420\u0412\u0418\u0421 NULL. \u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435, \u0435\u0441\u0442\u044c \u043b\u0438 @Service \u0432 TinkoffApiService.java");
            }
            Map<String, Object> tinkoffResponse = this.tinkoffApiService.initCardPayment(amount, userId, email);
            ObjectMapper mapper = new ObjectMapper();
            System.out.println("====== RESPONSE BODY (FROM TINKOFF) ======");
            System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(tinkoffResponse));
            orderId = (String)tinkoffResponse.get("OrderId");
            String paymentUrl = (String)tinkoffResponse.get("PaymentUrl");
            String status = (String)tinkoffResponse.get("Status");
            String details = (String)tinkoffResponse.get("Details");
            if ("NEW".equalsIgnoreCase(status) && paymentUrl != null) {
                System.out.println("\u2705 \u041f\u043b\u0430\u0442\u0435\u0436 \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u0438\u043d\u0438\u0446\u0438\u0438\u0440\u043e\u0432\u0430\u043d. OrderId: " + orderId);
                return new PaymentInitResponse(paymentUrl, orderId);
            }
            String errorMessage = details != null ? details : (String)tinkoffResponse.get("Message");
            System.err.println("\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043e\u0442\u0432\u0435\u0442\u0430 \u0422-\u0411\u0430\u043d\u043a\u0430. \u0421\u0442\u0430\u0442\u0443\u0441: " + status + ", \u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435: " + errorMessage);
            return new PaymentInitResponse("\u041e\u0448\u0438\u0431\u043a\u0430 \u0422-\u0411\u0430\u043d\u043a\u0430: " + (errorMessage != null ? errorMessage : "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430."), orderId);
        }
        catch (Exception e) {
            System.err.println("--- \ud83d\udd34 \u041a\u0420\u0418\u0422\u0418\u0427\u0415\u0421\u041a\u0410\u042f \u041e\u0428\u0418\u0411\u041a\u0410 \u0412\u042b\u041f\u041e\u041b\u041d\u0415\u041d\u0418\u042f ---");
            e.printStackTrace();
            return new PaymentInitResponse("\u041a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0430: " + e.getMessage(), orderId);
        }
    }
}
