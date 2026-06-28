import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate } from 'k6/metrics';

const stressErrors = new Rate('stress_errors');

export const options = {
  scenarios: {
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000', 'p(99)<10000'],
    http_req_failed: ['rate<0.1'],
    stress_errors: ['rate<0.15'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const userId = `soak-user-${__VU}-${__ITER}`;
  const amount = (Math.random() * 9900 + 100).toFixed(2);
  const email = `soak${Math.floor(Math.random() * 10000)}@test.com`;

  group('payment_flow', function () {
    // Step 1: Init payment
    const initRes = http.get(
      `${BASE_URL}/api/card/init?userId=${userId}&amount=${amount}&email=${email}`,
      { tags: { name: 'soak: card/init' } }
    );

    check(initRes, {
      'init: responded': (r) => r.status > 0,
      'init: not crashed': (r) => r.status !== 0,
    }) || stressErrors.add(1);

    sleep(1);

    // Step 2: SBP init
    const sbpRes = http.get(
      `${BASE_URL}/api/sbp/init-and-qr?userId=${userId}&amount=${amount}&email=${email}`,
      { tags: { name: 'soak: sbp/init-and-qr' } }
    );

    check(sbpRes, {
      'sbp: responded': (r) => r.status > 0,
      'sbp: not crashed': (r) => r.status !== 0,
    }) || stressErrors.add(1);

    sleep(1);

    // Step 3: QR generation
    const qrRes = http.get(
      `${BASE_URL}/api/qr/generate?amount=${amount}&email=${email}`,
      { tags: { name: 'soak: qr/generate' } }
    );

    check(qrRes, {
      'qr: responded': (r) => r.status > 0,
      'qr: not crashed': (r) => r.status !== 0,
    }) || stressErrors.add(1);
  });

  sleep(2);
}
