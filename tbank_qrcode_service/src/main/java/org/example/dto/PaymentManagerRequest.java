/*
 * Decompiled with CFR 0.152.
 */
package org.example.dto;

public class PaymentManagerRequest {
    private String userId;
    private double amount;
    private String email;

    public String getUserId() {
        return this.userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public double getAmount() {
        return this.amount;
    }

    public String getEmail() {
        return this.email;
    }

    public void setAmount(double amount) {
        this.amount = amount;
    }
}
