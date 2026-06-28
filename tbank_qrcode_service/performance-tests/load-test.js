import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

// Custom metrics for detailed reporting
const paymentInitDuration = new Trend('payment_init_duration', true);
const paymentInitErrors = new Rate('payment_init_errors');
const qrGenerationDuration = new Trend('qr_generation_duration', true);
const cardInitDuration = new Trend('card_init_duration', true);
const totalPayments = new Counter('total_payments');

export const options = {
  scenarios: {
    ramp_up_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },  // warm-up
        { duration: '1m', target: 50 },   // peak load
        { duration: '30s', target: 20 },  // cool-down
        { duration: '30s', target: 0 },   // ramp-down
      ],
      gracefulRampDown: '10s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<3000', 'p(99)<5000'],
    http_req_failed: ['rate<0.05'],
    payment_init_duration: ['p(95)<3000'],
    qr_generation_duration: ['p(95)<4000'],
    card_init_duration: ['p(95)<3000'],
    payment_init_errors: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

function randomEmail() {
  return `loaduser${Math.floor(Math.random() * 10000)}@test.com`;
}

function randomAmount() {
  return (Math.random() * 9900 + 100).toFixed(2);
}

export default function () {
  const userId = `load-test-user-${__VU}-${__ITER}`;
  const amount = randomAmount();
  const email = randomEmail();

  group('01_payment_init', function () {
    const res = http.get(
      `${BASE_URL}/api/card/init?userId=${userId}&amount=${amount}&email=${email}`,
      { tags: { name: 'POST /api/card/init' } }
    );

    cardInitDuration.add(res.timings.duration);
    totalPayments.add(1);

    check(res, {
      'card/init: status 200': (r) => r.status === 200,
      'card/init: has orderId or error': (r) => {
        const body = r.json();
        return body && (body.orderId || body.error);
      },
    });

    if (res.status !== 200) {
      paymentInitErrors.add(1);
    }
  });

  group('02_sbp_payment', function () {
    const res = http.get(
      `${BASE_URL}/api/sbp/init-and-qr?userId=${userId}&amount=${amount}&email=${email}`,
      { tags: { name: 'GET /api/sbp/init-and-qr' } }
    );

    paymentInitDuration.add(res.timings.duration);

    check(res, {
      'sbp/init-and-qr: status 200': (r) => r.status === 200,
      'sbp/init-and-qr: has status field': (r) => {
        const body = r.json();
        return body && body.status;
      },
    });

    if (res.status !== 200) {
      paymentInitErrors.add(1);
    }
  });

  group('03_qr_generation', function () {
    const res = http.get(
      `${BASE_URL}/api/qr/generate?amount=${amount}&email=${email}`,
      { tags: { name: 'GET /api/qr/generate' } }
    );

    qrGenerationDuration.add(res.timings.duration);

    check(res, {
      'qr/generate: status 200 or 503': (r) => r.status === 200 || r.status === 503,
      'qr/generate: response not empty': (r) => r.body.length > 0,
    });
  });

  sleep(Math.random() * 2 + 0.5);
}

export function handleSummary(data) {
  const reportDir = __ENV.REPORT_DIR || '.';
  return {
    [`${reportDir}/load-test-report.html`]: htmlReport(data),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
