/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.google.zxing.BarcodeFormat
 *  com.google.zxing.WriterException
 *  com.google.zxing.client.j2se.MatrixToImageWriter
 *  com.google.zxing.common.BitMatrix
 *  com.google.zxing.qrcode.QRCodeWriter
 *  org.springframework.stereotype.Service
 */
package org.example.service;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Base64;
import org.springframework.stereotype.Service;

@Service
public class QrCodeService {
    public byte[] generateQrCodeImage(String content, int width, int height) throws WriterException, IOException {
        if (content == null || content.trim().isEmpty()) {
            throw new IllegalArgumentException("\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u043c\u043e\u0435 \u0434\u043b\u044f QR-\u043a\u043e\u0434\u0430 \u043d\u0435 \u043c\u043e\u0436\u0435\u0442 \u0431\u044b\u0442\u044c \u043f\u0443\u0441\u0442\u044b\u043c.");
        }
        QRCodeWriter qrCodeWriter = new QRCodeWriter();
        BitMatrix bitMatrix = qrCodeWriter.encode(content, BarcodeFormat.QR_CODE, width, height);
        ByteArrayOutputStream pngOutputStream = new ByteArrayOutputStream();
        MatrixToImageWriter.writeToStream((BitMatrix)bitMatrix, (String)"PNG", (OutputStream)pngOutputStream);
        return pngOutputStream.toByteArray();
    }

    public String generateQrCodeBase64(String content, int width, int height) throws WriterException, IOException {
        byte[] imageBytes = this.generateQrCodeImage(content, width, height);
        return Base64.getEncoder().encodeToString(imageBytes);
    }
}
