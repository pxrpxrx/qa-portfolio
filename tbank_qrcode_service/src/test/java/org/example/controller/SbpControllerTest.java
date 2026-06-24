package org.example.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;
import org.example.service.TinkoffApiService;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.mockito.Mockito.when;

@WebMvcTest(SbpController.class)
class SbpControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TinkoffApiService tinkoffApiService;

    @Test
    void getPaymentStatus_WithValidOrderId_ShouldReturnStatus() throws Exception {
        when(tinkoffApiService.getPaymentStatus("order-123"))
            .thenReturn("CONFIRMED");

        mockMvc.perform(get("/api/sbp/payment/order-123"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.orderId").value("order-123"))
            .andExpect(jsonPath("$.status").value("CONFIRMED"));
    }

    @Test
    void getPaymentStatus_WithInvalidOrderId_ShouldReturn404() throws Exception {
        when(tinkoffApiService.getPaymentStatus("non-existent"))
            .thenThrow(new RuntimeException("Order not found"));

        mockMvc.perform(get("/api/sbp/payment/non-existent"))
            .andExpect(status().isNotFound());
    }
}
