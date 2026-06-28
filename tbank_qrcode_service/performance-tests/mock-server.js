const http = require('http');

const PORT = 8080;

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const path = url.pathname;
  const latency = Math.random() * 200 + 50; // 50-250ms simulated latency

  setTimeout(() => {
    if (path === '/api/card/init') {
      const userId = url.searchParams.get('userId');
      const amount = parseFloat(url.searchParams.get('amount'));
      const email = url.searchParams.get('email');

      if (!userId || !amount || !email) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Missing required parameters' }));
        return;
      }
      if (isNaN(amount) || amount <= 0) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid amount' }));
        return;
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        paymentUrl: `https://pay.tinkoff.ru/order/${Date.now()}`,
        orderId: `ORD-${Date.now()}`,
        status: 'NEW'
      }));

    } else if (path === '/api/sbp/init-and-qr') {
      const userId = url.searchParams.get('userId');
      const amount = parseFloat(url.searchParams.get('amount'));

      if (!userId || !amount) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ERROR', message: 'Missing params' }));
        return;
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'SUCCESS',
        orderId: `SBP-${Date.now()}`,
        qrSvg: '<svg>mock-qr-code</svg>'
      }));

    } else if (path === '/api/qr/generate') {
      res.writeHead(200, { 'Content-Type': 'image/png' });
      res.end(Buffer.from('mock-png-data'));

    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
    }
  }, latency);
});

server.listen(PORT, () => {
  console.log(`Mock server running on http://localhost:${PORT}`);
  console.log('Endpoints: /api/card/init, /api/sbp/init-and-qr, /api/qr/generate');
});
