import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const spikeErrors = new Rate('spike_errors');

export const options = {
  scenarios: {
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 10 },   // baseline
        { duration: '5s', target: 200 },   // sudden spike
        { duration: '15s', target: 200 },  // sustain spike
        { duration: '5s', target: 0 },     // recovery
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    http_req_failed: ['rate<0.5'],
    spike_errors: ['rate<0.5'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const userId = `spike-user-${__VU}`;
  const amount = (Math.random() * 5000 + 100).toFixed(2);
  const email = `spike${Math.floor(Math.random() * 10000)}@test.com`;

  const res = http.get(
    `${BASE_URL}/api/card/init?userId=${userId}&amount=${amount}&email=${email}`
  );

  const passed = check(res, {
    'spike: responded': (r) => r.status > 0,
    'spike: not 5xx (or acceptable 503)': (r) => r.status < 500 || r.status === 503,
  });

  if (!passed) {
    spikeErrors.add(1);
  }

  sleep(0.5);
}
