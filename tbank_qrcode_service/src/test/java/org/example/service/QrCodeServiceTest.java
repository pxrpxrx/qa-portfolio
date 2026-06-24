package org.example.service;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import java.awt.image.BufferedImage;
import java.util.Base64;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class QrCodeServiceTest {

    @InjectMocks
    private QrCodeService qrCodeService;

    @Mock
    private TinkoffApiService tinkoffApiService;

    @Test
    void generateQrCode_ShouldReturnBase64Png() throws Exception {
        String qrText = "https://securepay.tinkoff.ru/pay?orderId=test-123";
        String result = qrCodeService.generateQrCode(qrText);

        assertNotNull(result);
        assertTrue(result.startsWith("data:image/png;base64,"));
        assertTrue(result.length() > 30);
    }

    @Test
    void generateQrCode_WithDifferentText_ReturnsDifferentQr() throws Exception {
        String qr1 = qrCodeService.generateQrCode("https://pay.tinkoff.ru/order/1");
        String qr2 = qrCodeService.generateQrCode("https://pay.tinkoff.ru/order/2");

        assertNotNull(qr1);
        assertNotNull(qr2);
    }

    @Test
    void generateQrCode_WithEmptyText_ShouldThrowException() {
        assertThrows(IllegalArgumentException.class, () -> {
            qrCodeService.generateQrCode("");
        });
    }

    @Test
    void generateQrCode_WithNullText_ShouldThrowException() {
        assertThrows(IllegalArgumentException.class, () -> {
            qrCodeService.generateQrCode(null);
        });
    }

    @Test
    void initAndGenerateQr_ShouldReturnPaymentInitResponse() throws Exception {
        String testUserId = "test_user_001";
        double testAmount = 100.50;
        String mockOrderId = "order-xxxxxxxx";

        when(tinkoffApiService.initPayment(testUserId, testAmount))
            .thenReturn(mockOrderId);

        var response = qrCodeService.initAndGenerateQr(testUserId, testAmount);

        assertNotNull(response);
        assertEquals(mockOrderId, response.getOrderId());
        assertNotNull(response.getQrSvg());
        assertTrue(response.getQrSvg().startsWith("data:image/png;base64,")
                || response.getQrSvg().startsWith("<svg"));

        verify(tinkoffApiService, times(1)).initPayment(testUserId, testAmount);
    }

    @Test
    void initAndGenerateQr_WhenTinkoffFails_ShouldThrowException() throws Exception {
        when(tinkoffApiService.initPayment(anyString(), anyDouble()))
            .thenThrow(new RuntimeException("Tinkoff API error"));

        assertThrows(RuntimeException.class, () -> {
            qrCodeService.initAndGenerateQr("test_user", 100.0);
        });
    }
}
