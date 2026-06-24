import pytest
import requests
import json

BASE_URL = "http://208.92.226.223:8080"
WS_URL = "ws://208.92.226.223:8080/ws"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def ws_url():
    return WS_URL


@pytest.fixture
def sample_payment(base_url):
    response = requests.get(
        f"{base_url}/api/sbp/init-and-qr",
        params={"userId": "test_user", "amount": 100.50}
    )
    if response.status_code == 200:
        return response.json()
    return None
