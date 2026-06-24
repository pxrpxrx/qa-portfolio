import pytest
import requests
import json

BASE_URL = "http://208.92.226.223:8080"


class TestPaymentAPI:
    """Интеграционные тесты REST API платёжного сервиса."""

    @pytest.mark.smoke
    def test_init_payment_success(self):
        """Проверка успешной инициализации платежа с корректными параметрами."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_001", "amount": 100.50}
        )
        assert response.status_code == 200
        data = response.json()
        assert "qrSvg" in data
        assert "orderId" in data
        assert data["orderId"] is not None
        assert data["qrSvg"].startswith("<svg") or data["qrSvg"].startswith("data:image")

    @pytest.mark.smoke
    def test_init_payment_minimal_amount(self):
        """Проверка инициализации с минимально допустимой суммой."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_002", "amount": 1.00}
        )
        assert response.status_code == 200
        data = response.json()
        assert "orderId" in data

    def test_init_payment_large_amount(self):
        """Проверка инициализации с большой суммой."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_003", "amount": 999999.99}
        )
        assert response.status_code == 200
        data = response.json()
        assert "orderId" in data

    def test_init_payment_missing_user_id(self):
        """Проверка ошибки при отсутствии обязательного параметра userId."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"amount": 100.50}
        )
        assert response.status_code == 400

    def test_init_payment_missing_amount(self):
        """Проверка ошибки при отсутствии обязательного параметра amount."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_004"}
        )
        assert response.status_code == 400

    def test_init_payment_empty_user_id(self):
        """Проверка ошибки при пустом userId."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "", "amount": 100.50}
        )
        assert response.status_code == 400

    def test_init_payment_negative_amount(self):
        """Проверка ошибки при отрицательной сумме."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_005", "amount": -50}
        )
        assert response.status_code == 400

    def test_init_payment_zero_amount(self):
        """Проверка ошибки при нулевой сумме."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_006", "amount": 0}
        )
        assert response.status_code == 400

    def test_init_payment_string_amount(self):
        """Проверка обработки невалидного типа amount (строка вместо числа)."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_007", "amount": "not_a_number"}
        )
        assert response.status_code == 400

    def test_init_payment_special_chars_user_id(self):
        """Проверка userId со спецсимволами."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "<script>alert(1)</script>", "amount": 100.50}
        )
        assert response.status_code in (200, 400)

    def test_init_payment_very_long_user_id(self):
        """Проверка userId с длиной более 1000 символов."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "x" * 2000, "amount": 100.50}
        )
        assert response.status_code in (200, 400)

    @pytest.mark.smoke
    def test_health_check(self):
        """Проверка health endpoint."""
        response = requests.get(f"{BASE_URL}/actuator/health")
        assert response.status_code in (200, 404)

    def test_unknown_endpoint(self):
        """Проверка ответа на несуществующий endpoint."""
        response = requests.get(f"{BASE_URL}/api/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Проверка ответа при неверном HTTP-методе."""
        response = requests.post(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "test_user_008", "amount": 100.50}
        )
        assert response.status_code in (405, 400)

    def test_concurrent_init_same_user(self):
        """Проверка множественных запросов для одного userId."""
        responses = [
            requests.get(
                f"{BASE_URL}/api/sbp/init-and-qr",
                params={"userId": "concurrent_user", "amount": 50 + i}
            )
            for i in range(5)
        ]
        for resp in responses:
            assert resp.status_code == 200
            data = resp.json()
            assert "orderId" in data

    def test_response_format(self):
        """Проверка структуры JSON-ответа."""
        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "format_check_user", "amount": 250.00}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("orderId"), str)
        assert isinstance(data.get("qrSvg"), str)
        assert len(data["orderId"]) > 0
        assert len(data["qrSvg"]) > 0
