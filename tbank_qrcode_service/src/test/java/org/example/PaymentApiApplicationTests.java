package org.example;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.example.service.TinkoffApiService;

@SpringBootTest
class PaymentApiApplicationTests {

    @MockBean
    private TinkoffApiService tinkoffApiService;

    @Test
    void contextLoads() {
    }
}
