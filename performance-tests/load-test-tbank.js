import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    userId: `load-test-user-${__VU}`,
    amount: Math.random() * 10000 + 100,
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post(`${BASE_URL}/api/sbp/init`, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has orderId': (r) => r.json('orderId') !== undefined,
  });

  sleep(1);
}
