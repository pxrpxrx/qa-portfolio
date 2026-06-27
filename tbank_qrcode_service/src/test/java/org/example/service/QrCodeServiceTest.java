package org.example.service;

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit-тесты QrCodeService.
 * Проверяют генерацию QR-кодов.
 */
@ExtendWith(MockitoExtension.class)
class QrCodeServiceTest {

    private QrCodeService qrCodeService;

    @BeforeEach
    void setUp() {
        qrCodeService = new QrCodeService();
    }

    @Test
    @DisplayName("generateQrCodeImage: валидный контент генерирует PNG")
    void generateQrCodeImage_validContent_generatesPng() throws Exception {
        String content = "https://example.com/payment/123";
        int width = 200;
        int height = 200;

        byte[] imageBytes = qrCodeService.generateQrCodeImage(content, width, height);

        assertNotNull(imageBytes);
        assertTrue(imageBytes.length > 0);
        // PNG signature: 89 50 4E 47
        assertEquals((byte) 0x89, imageBytes[0]);
        assertEquals((byte) 0x50, imageBytes[1]);
        assertEquals((byte) 0x4E, imageBytes[2]);
        assertEquals((byte) 0x47, imageBytes[3]);
    }

    @Test
    @DisplayName("generateQrCodeImage: пустой контент выбрасывает IllegalArgumentException")
    void generateQrCodeImage_emptyContent_throws() {
        assertThrows(IllegalArgumentException.class, () -> {
            qrCodeService.generateQrCodeImage("", 200, 200);
        });
    }

    @Test
    @DisplayName("generateQrCodeImage: null контент выбрасывает IllegalArgumentException")
    void generateQrCodeImage_nullContent_throws() {
        assertThrows(IllegalArgumentException.class, () -> {
            qrCodeService.generateQrCodeImage(null, 200, 200);
        });
    }

    @Test
    @DisplayName("generateQrCodeBase64: возвращает валидный Base64")
    void generateQrCodeBase64_returnsValidBase64() throws Exception {
        String content = "https://example.com/payment/123";
        int width = 200;
        int height = 200;

        String base64 = qrCodeService.generateQrCodeBase64(content, width, height);

        assertNotNull(base64);
        assertFalse(base64.isEmpty());
        // Base64 не должен содержать пробелов
        assertFalse(base64.contains(" "));
    }

    @Test
    @DisplayName("generateQrCodeImage: разные размеры дают разные результаты")
    void generateQrCodeImage_differentSizes_differentResults() throws Exception {
        String content = "https://example.com/payment/123";

        byte[] small = qrCodeService.generateQrCodeImage(content, 100, 100);
        byte[] large = qrCodeService.generateQrCodeImage(content, 300, 300);

        assertNotNull(small);
        assertNotNull(large);
        // Больший размер должен давать больший файл
        assertTrue(large.length > small.length);
    }
}
