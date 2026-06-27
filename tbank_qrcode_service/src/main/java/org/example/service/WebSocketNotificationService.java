/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.messaging.simp.SimpMessagingTemplate
 *  org.springframework.stereotype.Service
 */
package org.example.service;

import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
public class WebSocketNotificationService {
    private final SimpMessagingTemplate messagingTemplate;

    @Autowired
    public WebSocketNotificationService(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    public void notifyClientStatusUpdate(String orderId, String status) {
        Map<String, String> payload = Map.of("orderId", orderId, "status", status);
        String destination = "/topic/payment/" + orderId;
        this.messagingTemplate.convertAndSend(destination, payload);
        System.out.println("-> [WS] Уведомление отправлено в канал " + destination + " со статусом: " + status);
    }
}
