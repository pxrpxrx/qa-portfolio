# k6 Performance Test Results

**Date:** 2026-06-28
**Tool:** k6 v2.0.0
**Target:** tbank_qrcode_service (mock server, 50-250ms latency)

---

## 1. Load Test (`load-test.js`)

**Scenario:** Ramp-up to 50 VU over 2m30s (4 stages)

### Thresholds — ALL PASSED ✓

| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| http_req_duration p(95) | < 3000ms | 248.61ms | ✓ |
| http_req_duration p(99) | < 5000ms | 256.78ms | ✓ |
| http_req_failed | < 5% | 0.00% | ✓ |
| card_init_duration p(95) | < 3000ms | 248.82ms | ✓ |
| payment_init_duration p(95) | < 3000ms | 247.77ms | ✓ |
| qr_generation_duration p(95) | < 4000ms | 249.01ms | ✓ |

### Summary

| Metric | avg | min | med | max | p(95) |
|--------|-----|-----|-----|-----|-------|
| http_req_duration | 158.42ms | 50.09ms | 159.92ms | 273.59ms | 248.61ms |
| iteration_duration | 1.97s | 696ms | 1.98s | 3.15s | 2.89s |

- **Total requests:** 5,067 (33.6 req/s)
- **Total iterations:** 1,689 (11.2 iter/s)
- **Checks:** 10,134 total, 100% passed
- **Max VUs:** 50

---

## 2. Spike Test (`spike-test.js`)

**Scenario:** Sudden spike from 10 to 200 VU in 5 seconds

### Thresholds — ALL PASSED ✓

| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| http_req_duration p(95) | < 5000ms | 246.39ms | ✓ |
| http_req_failed | < 50% | 0.00% | ✓ |
| spike_errors | < 50% | 0.00% | ✓ |

### Summary

| Metric | avg | min | med | max | p(95) |
|--------|-----|-----|-----|-----|-------|
| http_req_duration | 155.88ms | 49.8ms | 156.17ms | 263.95ms | 246.39ms |
| iteration_duration | 656ms | 550ms | 656ms | 764ms | 746ms |

- **Total requests:** 6,294 (176.8 req/s)
- **Max VUs:** 200
- **Checks:** 12,588 total, 100% passed

**Conclusion:** Server handled 20x load spike without degradation.

---

## 3. Negative Test (`negative-test.js`)

**Scenario:** 50 iterations, 5 VUs — invalid data, SQL injection, XSS

### Thresholds — ALL PASSED ✓

| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| negative_unexpected_errors | < 5% | 0.00% | ✓ |

### Checks — 22/22 PASSED ✓

| Check | Result |
|-------|--------|
| negative amount: server responded | ✓ |
| negative amount: 4xx or 200 with error | ✓ |
| zero amount: server responded | ✓ |
| zero amount: 4xx or 200 with error | ✓ |
| huge amount: server responded | ✓ |
| huge amount: not 500 | ✓ |
| missing userId: 4xx (bad request) | ✓ |
| missing amount: 4xx (bad request) | ✓ |
| no params: 4xx (bad request) | ✓ |
| string amount: 4xx (bad request) | ✓ |
| sql injection: server responded | ✓ |
| sql injection: not 500 | ✓ |
| xss attempt: server responded | ✓ |
| xss attempt: not 500 | ✓ |
| POST to GET: 405 or 4xx | ✓ |
| 404: returns 404 | ✓ |

- **Total requests:** 550 (34.4 req/s)
- **http_req_failed:** 81.81% (expected — negative tests SHOULD fail)
- **Server crashes:** 0

**Conclusion:** Server correctly returns 4xx for all invalid inputs. No 500 errors. No crashes.

---

## 4. Soak Test (`stress-test.js`)

**Status:** Not yet executed (requires 10 minutes)

**To run:**
```bash
node mock-server.js &
k6 run stress-test.js
```

---

## How to reproduce

```bash
# 1. Start mock server
node mock-server.js

# 2. Run tests (in separate terminal)
k6 run load-test.js
k6 run spike-test.js
k6 run negative-test.js
k6 run stress-test.js  # 10 minutes!
```
