import http from 'k6/http';
import { check, group } from 'k6';
import { Rate } from 'k6/metrics';

const negativeErrors = new Rate('negative_unexpected_errors');

export const options = {
  vus: 5,
  iterations: 50,
  thresholds: {
    negative_unexpected_errors: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  group('negative: invalid amount', function () {
    // Negative amount
    const res1 = http.get(
      `${BASE_URL}/api/card/init?userId=test-user&amount=-500&email=test@test.com`
    );
    check(res1, {
      'negative amount: server responded (not crash)': (r) => r.status > 0,
      'negative amount: 4xx or 200 with error': (r) =>
        r.status === 200 || (r.status >= 400 && r.status < 500),
    }) || negativeErrors.add(1);

    // Zero amount
    const res2 = http.get(
      `${BASE_URL}/api/card/init?userId=test-user&amount=0&email=test@test.com`
    );
    check(res2, {
      'zero amount: server responded': (r) => r.status > 0,
      'zero amount: 4xx or 200 with error': (r) =>
        r.status === 200 || (r.status >= 400 && r.status < 500),
    }) || negativeErrors.add(1);

    // Extremely large amount
    const res3 = http.get(
      `${BASE_URL}/api/card/init?userId=test-user&amount=999999999&email=test@test.com`
    );
    check(res3, {
      'huge amount: server responded': (r) => r.status > 0,
      'huge amount: not 500': (r) => r.status !== 500,
    }) || negativeErrors.add(1);
  });

  group('negative: missing parameters', function () {
    // Missing userId
    const res1 = http.get(
      `${BASE_URL}/api/card/init?amount=1000&email=test@test.com`
    );
    check(res1, {
      'missing userId: server responded': (r) => r.status > 0,
      'missing userId: 4xx (bad request)': (r) => r.status >= 400 && r.status < 500,
    }) || negativeErrors.add(1);

    // Missing amount
    const res2 = http.get(
      `${BASE_URL}/api/card/init?userId=test-user&email=test@test.com`
    );
    check(res2, {
      'missing amount: server responded': (r) => r.status > 0,
      'missing amount: 4xx (bad request)': (r) => r.status >= 400 && r.status < 500,
    }) || negativeErrors.add(1);

    // No parameters at all
    const res3 = http.get(`${BASE_URL}/api/card/init`);
    check(res3, {
      'no params: server responded': (r) => r.status > 0,
      'no params: 4xx (bad request)': (r) => r.status >= 400 && r.status < 500,
    }) || negativeErrors.add(1);
  });

  group('negative: invalid data types', function () {
    // String instead of number for amount
    const res1 = http.get(
      `${BASE_URL}/api/card/init?userId=test-user&amount=abc&email=test@test.com`
    );
    check(res1, {
      'string amount: server responded': (r) => r.status > 0,
      'string amount: 4xx (bad request)': (r) => r.status >= 400 && r.status < 500,
    }) || negativeErrors.add(1);

    // SQL injection attempt
    const res2 = http.get(
      `${BASE_URL}/api/card/init?userId=123' OR '1'='1&amount=1000&email=test@test.com`
    );
    check(res2, {
      'sql injection: server responded': (r) => r.status > 0,
      'sql injection: not 500': (r) => r.status !== 500,
    }) || negativeErrors.add(1);

    // XSS attempt
    const res3 = http.get(
      `${BASE_URL}/api/card/init?userId=<script>alert(1)</script>&amount=1000&email=test@test.com`
    );
    check(res3, {
      'xss attempt: server responded': (r) => r.status > 0,
      'xss attempt: not 500': (r) => r.status !== 500,
    }) || negativeErrors.add(1);
  });

  group('negative: POST to GET endpoint', function () {
    const res = http.post(
      `${BASE_URL}/api/card/init`,
      JSON.stringify({ userId: 'test', amount: 1000, email: 'test@test.com' }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    check(res, {
      'POST to GET: server responded': (r) => r.status > 0,
      'POST to GET: 405 or 4xx': (r) => r.status === 405 || (r.status >= 400 && r.status < 500),
    }) || negativeErrors.add(1);
  });

  group('negative: non-existent endpoint', function () {
    const res = http.get(`${BASE_URL}/api/nonexistent/endpoint`);
    check(res, {
      '404: server responded': (r) => r.status > 0,
      '404: returns 404': (r) => r.status === 404,
    }) || negativeErrors.add(1);
  });
}
