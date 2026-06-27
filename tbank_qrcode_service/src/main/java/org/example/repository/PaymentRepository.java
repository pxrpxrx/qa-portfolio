/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.data.jpa.repository.JpaRepository
 *  org.springframework.stereotype.Repository
 */
package org.example.repository;

import java.util.Optional;
import org.example.entity.PaymentEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PaymentRepository
extends JpaRepository<PaymentEntity, Long> {
    public Optional<PaymentEntity> findByOrderId(String var1);
}
