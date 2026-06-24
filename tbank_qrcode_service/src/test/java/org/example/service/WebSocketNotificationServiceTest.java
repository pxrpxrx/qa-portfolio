package org.example.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class WebSocketNotificationServiceTest {

    @InjectMocks
    private WebSocketNotificationService notificationService;

    @Mock
    private SimpMessagingTemplate messagingTemplate;

    @Captor
    private ArgumentCaptor<String> destinationCaptor;

    @Captor
    private ArgumentCaptor<Object> payloadCaptor;

    @Test
    void notifyPaymentConfirmed_ShouldSendToCorrectTopic() {
        String orderId = "order-test-001";

        notificationService.notifyPaymentConfirmed(orderId);

        verify(messagingTemplate, times(1))
            .convertAndSend(eq("/topic/payment/" + orderId), any());
    }

    @Test
    void notifyPaymentConfirmed_ShouldSendCorrectPayload() {
        String orderId = "order-test-002";

        notificationService.notifyPaymentConfirmed(orderId);

        verify(messagingTemplate).convertAndSend(
            destinationCaptor.capture(),
            payloadCaptor.capture());

        assertEquals("/topic/payment/order-test-002", destinationCaptor.getValue());

        assertNotNull(payloadCaptor.getValue());
        assertInstanceOf(java.util.Map.class, payloadCaptor.getValue());

        @SuppressWarnings("unchecked")
        java.util.Map<String, String> payload =
            (java.util.Map<String, String>) payloadCaptor.getValue();
        assertEquals(orderId, payload.get("orderId"));
        assertEquals("CONFIRMED", payload.get("status"));
    }

    @Test
    void notifyPaymentConfirmed_WithEmptyOrderId_ShouldStillSend() {
        notificationService.notifyPaymentConfirmed("");

        verify(messagingTemplate).convertAndSend(
            destinationCaptor.capture(),
            payloadCaptor.capture());

        assertEquals("/topic/payment/", destinationCaptor.getValue());
    }

    @Test
    void notifyPaymentConfirmed_ShouldHandleMessagingException() {
        doThrow(new RuntimeException("Template error"))
            .when(messagingTemplate).convertAndSend(anyString(), any());

        assertDoesNotThrow(() ->
            notificationService.notifyPaymentConfirmed("order-test-003"));
    }

    @Test
    void notifyPaymentConfirmed_WithSpecialCharsInOrderId() {
        String orderId = "order-<script>alert(1)</script>-123";

        notificationService.notifyPaymentConfirmed(orderId);

        verify(messagingTemplate).convertAndSend(
            destinationCaptor.capture(),
            any());

        assertTrue(destinationCaptor.getValue().contains(orderId));
    }

    @Test
    void notifyPaymentConfirmed_ShouldSendStatusConfirmed() {
        notificationService.notifyPaymentConfirmed("order-test-004");

        verify(messagingTemplate).convertAndSend(
            anyString(),
            payloadCaptor.capture());

        @SuppressWarnings("unchecked")
        java.util.Map<String, String> payload =
            (java.util.Map<String, String>) payloadCaptor.getValue();
        assertEquals("CONFIRMED", payload.get("status"));
    }
}
