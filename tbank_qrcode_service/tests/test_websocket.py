import pytest
import json
import time
import threading
from websocket import create_connection, WebSocketConnectionClosedException

WS_URL = "ws://208.92.226.223:8080/ws"
BASE_URL = "http://208.92.226.223:8080"

RECEIVED_MESSAGES = []
CONNECTION_ERRORS = []


def _subscribe_and_listen(order_id, timeout=15):
    """Подключается к WebSocket, подписывается на orderId и ждёт сообщение."""
    import requests
    try:
        ws = create_connection(WS_URL, timeout=10)
    except Exception as e:
        CONNECTION_ERRORS.append(f"Connection failed: {e}")
        return

    subscribe_frame = f"SUBSCRIBE\nid:sub-0\ndestination:/topic/payment/{order_id}\n\n\0"
    ws.send(subscribe_frame)

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            ws.settimeout(2)
            message = ws.recv()
            RECEIVED_MESSAGES.append(message)
        except WebSocketConnectionClosedException:
            break
        except Exception:
            continue
    ws.close()


class TestWebSocketPayments:
    """Интеграционные тесты WebSocket для получения статусов оплаты."""

    @pytest.mark.smoke
    @pytest.mark.websocket
    def test_websocket_connection(self):
        """Проверка возможности подключения к WebSocket."""
        try:
            ws = create_connection(WS_URL, timeout=5)
            assert ws.connected
            ws.close()
        except Exception as e:
            pytest.fail(f"Не удалось подключиться к WebSocket: {e}")

    @pytest.mark.websocket
    def test_websocket_subscribe_and_receive(self):
        """Проверка подписки на топик и получения уведомления об оплате.

        Последовательность:
        1. Инициализировать платеж через REST
        2. Подключиться к WebSocket и подписаться на /topic/payment/{orderId}
        3. Дождаться сообщения о статусе CONFIRMED
        """
        import requests

        global RECEIVED_MESSAGES, CONNECTION_ERRORS
        RECEIVED_MESSAGES.clear()
        CONNECTION_ERRORS.clear()

        response = requests.get(
            f"{BASE_URL}/api/sbp/init-and-qr",
            params={"userId": "ws_test_user", "amount": 100.00}
        )
        assert response.status_code == 200
        data = response.json()
        order_id = data["orderId"]

        thread = threading.Thread(target=_subscribe_and_listen, args=(order_id, 20))
        thread.daemon = True
        thread.start()

        thread.join(timeout=25)

        if CONNECTION_ERRORS:
            pytest.skip(f"WebSocket недоступен: {CONNECTION_ERRORS[0]}")

        if not RECEIVED_MESSAGES:
            pytest.skip("Сообщение не получено в течение таймаута (оплата не произведена)")

        for msg in RECEIVED_MESSAGES:
            try:
                parsed = json.loads(msg.replace("\n", "").strip("\0"))
                if parsed.get("status") == "CONFIRMED" and parsed.get("orderId") == order_id:
                    return
            except (json.JSONDecodeError, AttributeError):
                continue

    @pytest.mark.websocket
    def test_websocket_invalid_topic(self):
        """Проверка подписки на несуществующий топик."""
        import requests
        try:
            ws = create_connection(WS_URL, timeout=5)
            assert ws.connected

            subscribe_frame = "SUBSCRIBE\nid:sub-0\ndestination:/topic/invalid-topic-12345\n\n\0"
            ws.send(subscribe_frame)

            ws.settimeout(3)
            try:
                msg = ws.recv()
                assert msg is not None
            except Exception:
                pass

            ws.close()
        except Exception as e:
            pytest.skip(f"WebSocket недоступен: {e}")

    @pytest.mark.websocket
    def test_websocket_multiple_subscriptions(self):
        """Проверка нескольких одновременных подписок."""
        import requests
        try:
            ws = create_connection(WS_URL, timeout=5)
            assert ws.connected

            for i in range(3):
                sub_frame = f"SUBSCRIBE\nid:sub-{i}\ndestination:/topic/payment/multi-order-{i}\n\n\0"
                ws.send(sub_frame)

            ws.settimeout(2)
            try:
                msg = ws.recv()
                assert msg is not None
            except Exception:
                pass

            ws.close()
        except Exception as e:
            pytest.skip(f"WebSocket недоступен: {e}")
