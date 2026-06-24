
### 📄 test_spread_logic.js

```javascript
/**
 * Тесты для проверки логики расчета спреда
 * Запуск: node test_spread_logic.js
 */

// Мок-данные, которые приходят с API бирж
const mockData = [
  {
    coin: 'BTCUSDT',
    mexcBuy: 65000.00,
    mexcSell: 64990.00,
    bybitBuy: 65050.00,
    bybitSell: 65000.00
  },
  {
    coin: 'ETHUSDT',
    mexcBuy: 3500.00,
    mexcSell: 3498.00,
    bybitBuy: 3510.00,
    bybitSell: 3505.00
  }
];

/**
 * Функция расчета спреда (воспроизводит логику из Code-ноды n8n)
 */
function calculateSpread(exchanges) {
  const validExchanges = exchanges.filter(ex =>
    ex.buyPrice && ex.sellPrice && ex.buyPrice > 0 && ex.sellPrice > 0
  );

  if (validExchanges.length < 2) {
    return { spread: 0, bestBuyPrice: 0, bestSellPrice: 0 };
  }

  let bestBuy = { price: Infinity, exchange: '' };
  let bestSell = { price: 0, exchange: '' };

  for (const ex of validExchanges) {
    if (ex.buyPrice < bestBuy.price) {
      bestBuy.price = ex.buyPrice;
      bestBuy.exchange = ex.name;
    }
    if (ex.sellPrice > bestSell.price) {
      bestSell.price = ex.sellPrice;
      bestSell.exchange = ex.name;
    }
  }

  const spread = ((bestSell.price - bestBuy.price) / bestBuy.price) * 100;

  // Фильтрация: отсекаем спреды > 50% и отрицательные
  if (spread > 50 || spread < 0) {
    return { spread: 0, bestBuyPrice: 0, bestSellPrice: 0 };
  }

  return {
    spread: spread,
    bestBuyPrice: bestBuy.price,
    bestSellPrice: bestSell.price,
    bestBuyExchange: bestBuy.exchange,
    bestSellExchange: bestSell.exchange
  };
}

/**
 * Тест 1: Корректный расчет спреда для BTCUSDT
 */
function testBTCSpread() {
  console.log('🔍 Тест 1: Расчет спреда для BTCUSDT...');

  const exchanges = [
    { name: 'MEXC', buyPrice: mockData[0].mexcBuy, sellPrice: mockData[0].mexcSell },
    { name: 'Bybit', buyPrice: mockData[0].bybitBuy, sellPrice: mockData[0].bybitSell }
  ];

  const result = calculateSpread(exchanges);
  const expectedSpread = ((65050 - 64990) / 64990) * 100; // ~0.092%

  if (Math.abs(result.spread - expectedSpread) < 0.01) {
    console.log('✅ PASS: Спред для BTCUSDT рассчитан корректно:', result.spread.toFixed(2) + '%');
    return true;
  } else {
    console.log('❌ FAIL: Ожидалось:', expectedSpread.toFixed(2) + '%, получено:', result.spread.toFixed(2) + '%');
    return false;
  }
}

/**
 * Тест 2: Фильтрация спреда > 50%
 */
function testSpreadFilter() {
  console.log('🔍 Тест 2: Фильтрация спреда > 50%...');

  const exchanges = [
    { name: 'MEXC', buyPrice: 100, sellPrice: 90 },
    { name: 'Bybit', buyPrice: 200, sellPrice: 190 }
  ];

  const result = calculateSpread(exchanges);
  // Спред = ((190 - 100) / 100) * 100 = 90% → должен быть отсечен

  if (result.spread === 0) {
    console.log('✅ PASS: Спред > 50% корректно отсечен');
    return true;
  } else {
    console.log('❌ FAIL: Ожидался 0, получено:', result.spread);
    return false;
  }
}

/**
 * Тест 3: Фильтрация отрицательного спреда
 */
function testNegativeSpread() {
  console.log('🔍 Тест 3: Фильтрация отрицательного спреда...');

  const exchanges = [
    { name: 'MEXC', buyPrice: 100, sellPrice: 90 },
    { name: 'Bybit', buyPrice: 80, sellPrice: 70 }
  ];

  const result = calculateSpread(exchanges);
  // Спред = ((90 - 100) / 100) * 100 = -10% → должен быть отсечен

  if (result.spread === 0) {
    console.log('✅ PASS: Отрицательный спред корректно отсечен');
    return true;
  } else {
    console.log('❌ FAIL: Ожидался 0, получено:', result.spread);
    return false;
  }
}

/**
 * Тест 4: Недостаточно данных
 */
function testInsufficientData() {
  console.log('🔍 Тест 4: Обработка недостаточных данных...');

  const exchanges = [
    { name: 'MEXC', buyPrice: 100, sellPrice: 90 }
  ];

  const result = calculateSpread(exchanges);

  if (result.spread === 0) {
    console.log('✅ PASS: Недостаточность данных корректно обработана');
    return true;
  } else {
    console.log('❌ FAIL: Ожидался 0, получено:', result.spread);
    return false;
  }
}

/**
 * Тест 5: Корректный расчет спреда для ETHUSDT
 */
function testETHSpread() {
  console.log('🔍 Тест 5: Расчет спреда для ETHUSDT...');

  const exchanges = [
    { name: 'MEXC', buyPrice: mockData[1].mexcBuy, sellPrice: mockData[1].mexcSell },
    { name: 'Bybit', buyPrice: mockData[1].bybitBuy, sellPrice: mockData[1].bybitSell }
  ];

  const result = calculateSpread(exchanges);
  const expectedSpread = ((3510 - 3498) / 3498) * 100; // ~0.343%

  if (Math.abs(result.spread - expectedSpread) < 0.01) {
    console.log('✅ PASS: Спред для ETHUSDT рассчитан корректно:', result.spread.toFixed(2) + '%');
    return true;
  } else {
    console.log('❌ FAIL: Ожидалось:', expectedSpread.toFixed(2) + '%, получено:', result.spread.toFixed(2) + '%');
    return false;
  }
}

/**
 * Запуск всех тестов
 */
function runAllTests() {
  console.log('\n🧪 Запуск автотестов для расчета спреда\n');

  const tests = [
    testBTCSpread,
    testSpreadFilter,
    testNegativeSpread,
    testInsufficientData,
    testETHSpread
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    if (test()) {
      passed++;
    } else {
      failed++;
    }
    console.log('---');
  }

  console.log('\n📊 РЕЗУЛЬТАТЫ:');
  console.log(`✅ Пройдено: ${passed}`);
  console.log(`❌ Провалено: ${failed}`);
  console.log(`📈 Итого: ${passed + failed} тестов`);

  if (failed === 0) {
    console.log('\n🎉 Все тесты пройдены!');
  } else {
    console.log('\n⚠️ Есть проваленные тесты.');
  }
}

// Запуск
runAllTests();