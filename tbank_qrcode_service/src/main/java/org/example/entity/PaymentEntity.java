/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  jakarta.persistence.Column
 *  jakarta.persistence.Entity
 *  jakarta.persistence.GeneratedValue
 *  jakarta.persistence.GenerationType
 *  jakarta.persistence.Id
 *  jakarta.persistence.Table
 */
package org.example.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name="payments")
public class PaymentEntity {
    @Id
    @GeneratedValue(strategy=GenerationType.IDENTITY)
    private Long id;
    @Column(name="client_id")
    private String clientId;
    @Column(name="order_id", nullable=false)
    private String orderId;
    @Column(name="payment_id")
    private String paymentId;
    private String email;
    private BigDecimal amount;
    @Column(name="payment_type")
    private String paymentType;
    @Column(name="payment_date")
    private LocalDateTime paymentDate;

    public void setPaymentId(String paymentId) {
        this.paymentId = paymentId;
    }

    public void setPaymentDate(LocalDateTime paymentDate) {
        this.paymentDate = paymentDate;
    }

    public void setOrderId(String orderId) {
        this.orderId = orderId;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public void setClientId(String clientId) {
        this.clientId = clientId;
    }

    public Long getId() {
        return this.id;
    }

    public String getOrderId() {
        return this.orderId;
    }
}
