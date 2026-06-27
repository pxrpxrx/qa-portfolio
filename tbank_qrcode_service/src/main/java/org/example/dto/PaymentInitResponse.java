/*
 * Decompiled with CFR 0.152.
 */
package org.example.dto;

public class PaymentInitResponse {
    private String status;
    private String paymentURL;
    private String orderId;
    private String message;

    public PaymentInitResponse(String paymentURL, String orderId) {
        this.status = "SUCCESS";
        this.paymentURL = paymentURL;
        this.orderId = orderId;
        this.message = "\u041f\u043b\u0430\u0442\u0435\u0436 \u0438\u043d\u0438\u0446\u0438\u0438\u0440\u043e\u0432\u0430\u043d. \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 URL \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b.";
    }

    public PaymentInitResponse(String errorMessage, Integer errorCode) {
        this.status = "ERROR";
        this.message = errorMessage;
        this.orderId = null;
        this.paymentURL = null;
    }

    public PaymentInitResponse(String errorMessage, String knownOrderId, boolean isError) {
        this.status = "ERROR";
        this.message = errorMessage;
        this.orderId = knownOrderId;
        this.paymentURL = null;
    }

    public String getStatus() {
        return this.status;
    }

    public String getPaymentURL() {
        return this.paymentURL;
    }

    public String getOrderId() {
        return this.orderId;
    }

    public String getMessage() {
        return this.message;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setPaymentUrl(String paymentURL) {
        this.paymentURL = paymentURL;
    }

    public void setOrderId(String orderId) {
        this.orderId = orderId;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
