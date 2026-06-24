package org.example.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TinkoffApiServiceTest {

    @InjectMocks
    private TinkoffApiService tinkoffApiService;

    @Mock
    private CloseableHttpClient httpClient;

    @Mock
    private ObjectMapper objectMapper;

    private final ObjectMapper realMapper = new ObjectMapper();

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(tinkoffApiService, "apiUrl",
            "https://securepay.tinkoff.ru/v2/");
        ReflectionTestUtils.setField(tinkoffApiService, "terminalKey",
            "1765518875198DEMO");
        ReflectionTestUtils.setField(tinkoffApiService, "secretKey",
            "test-secret-key");
    }

    @Test
    void initPayment_ShouldReturnOrderId_OnSuccess() throws Exception {
        String jsonResponse = "{"
            + "\"Success\": true,"
            + "\"OrderId\": \"order-abc-123\","
            + "\"PaymentId\": \"1234567890\","
            + "\"Status\": \"NEW\""
            + "}";

        CloseableHttpResponse response = mock(CloseableHttpResponse.class);
        when(response.getCode()).thenReturn(200);
        when(response.getEntity()).thenReturn(
            new StringEntity(jsonResponse, ContentType.APPLICATION_JSON));

        when(httpClient.execute(any(HttpPost.class))).thenReturn(response);

        String orderId = tinkoffApiService.initPayment("test_user", 100.50);

        assertEquals("order-abc-123", orderId);
    }

    @Test
    void initPayment_ShouldThrow_WhenApiReturnsFailure() throws Exception {
        String jsonResponse = "{"
            + "\"Success\": false,"
            + "\"ErrorCode\": \"105\","
            + "\"Message\": \"Invalid amount\","
            + "\"Details\": \"Amount must be positive\""
            + "}";

        CloseableHttpResponse response = mock(CloseableHttpResponse.class);
        when(response.getCode()).thenReturn(200);
        when(response.getEntity()).thenReturn(
            new StringEntity(jsonResponse, ContentType.APPLICATION_JSON));

        when(httpClient.execute(any(HttpPost.class))).thenReturn(response);

        RuntimeException exception = assertThrows(RuntimeException.class, () ->
            tinkoffApiService.initPayment("test_user", -50.0));
        assertTrue(exception.getMessage().contains("Invalid amount")
            || exception.getMessage().contains("105"));
    }

    @Test
    void initPayment_ShouldThrow_WhenHttpStatusNot200() throws Exception {
        CloseableHttpResponse response = mock(CloseableHttpResponse.class);
        when(response.getCode()).thenReturn(500);
        when(response.getEntity()).thenReturn(null);

        when(httpClient.execute(any(HttpPost.class))).thenReturn(response);

        assertThrows(RuntimeException.class, () ->
            tinkoffApiService.initPayment("test_user", 100.0));
    }

    @Test
    void initPayment_ShouldThrow_OnIOException() throws Exception {
        when(httpClient.execute(any(HttpPost.class)))
            .thenThrow(new java.io.IOException("Connection refused"));

        assertThrows(RuntimeException.class, () ->
            tinkoffApiService.initPayment("test_user", 100.0));
    }

    @Test
    void initPayment_ShouldIncludeTerminalKeyInRequest() throws Exception {
        String jsonResponse = "{"
            + "\"Success\": true,"
            + "\"OrderId\": \"order-xyz\""
            + "}";

        CloseableHttpResponse response = mock(CloseableHttpResponse.class);
        when(response.getCode()).thenReturn(200);
        when(response.getEntity()).thenReturn(
            new StringEntity(jsonResponse, ContentType.APPLICATION_JSON));

        when(httpClient.execute(any(HttpPost.class))).thenReturn(response);

        tinkoffApiService.initPayment("test_user_42", 250.00);

        ArgumentCaptor<HttpPost> postCaptor = ArgumentCaptor.forClass(HttpPost.class);
        verify(httpClient).execute(postCaptor.capture());

        HttpPost capturedPost = postCaptor.getValue();
        String body = new String(capturedPost.getEntity().getContent().readAllBytes(),
            StandardCharsets.UTF_8);

        assertTrue(body.contains("1765518875198DEMO"));
        assertTrue(body.contains("test_user_42"));
        assertTrue(body.contains("250.0") || body.contains("250"));
    }
}
