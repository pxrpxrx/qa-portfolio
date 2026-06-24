package org.example.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;
import org.example.service.QrCodeService;
import org.example.dto.PaymentInitResponse;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.anyDouble;
import static org.mockito.Mockito.when;

@WebMvcTest(QrCodeController.class)
class QrCodeControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private QrCodeService qrCodeService;

    @Test
    void initAndGenerateQr_ShouldReturnQrAndOrderId() throws Exception {
        PaymentInitResponse mockResponse = new PaymentInitResponse(
            "order-12345",
            "<svg xmlns=\"http://www.w3.org/2000/svg\">...</svg>"
        );

        when(qrCodeService.initAndGenerateQr(anyString(), anyDouble()))
            .thenReturn(mockResponse);

        mockMvc.perform(get("/api/sbp/init-and-qr")
                .param("userId", "test_user")
                .param("amount", "100.50"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.orderId").value("order-12345"))
            .andExpect(jsonPath("$.qrSvg").exists());
    }

    @Test
    void initAndGenerateQr_WithoutUserId_ShouldReturn400() throws Exception {
        mockMvc.perform(get("/api/sbp/init-and-qr")
                .param("amount", "100.50"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void initAndGenerateQr_WithoutAmount_ShouldReturn400() throws Exception {
        mockMvc.perform(get("/api/sbp/init-and-qr")
                .param("userId", "test_user"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void initAndGenerateQr_NegativeAmount_ShouldReturn400() throws Exception {
        mockMvc.perform(get("/api/sbp/init-and-qr")
                .param("userId", "test_user")
                .param("amount", "-50"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void initAndGenerateQr_ZeroAmount_ShouldReturn400() throws Exception {
        mockMvc.perform(get("/api/sbp/init-and-qr")
                .param("userId", "test_user")
                .param("amount", "0"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void initAndGenerateQr_InvalidAmountType_ShouldReturn400() throws Exception {
        mockMvc.perform(get("/api/sbp/init-and-qr")
                .param("userId", "test_user")
                .param("amount", "not_a_number"))
            .andExpect(status().isBadRequest());
    }
}
