const https = require('https');

/**
 * Функция для выполнения HTTP-запроса
 */
function httpGet(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve({ status: res.statusCode, data: json });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    }).on('error', (err) => reject(err));
  });
}

/**
 * Тест 1: Доступность API MEXC
 */
async function testMEXCAPI() {
  console.log('🔍 Тест 1: Доступность API MEXC...');
  try {
    const response = await httpGet('https://api.mexc.com/api/v3/ticker/24hr');
    if (response.status === 200 && Array.isArray(response.data)) {
      console.log('✅ PASS: API MEXC доступен, получено', response.data.length, 'тикеров');
      return true;
    } else {
      console.log('❌ FAIL: Неверный статус или структура ответа');
      return false;
    }
  } catch (error) {
    console.log('❌ FAIL: Ошибка подключения:', error.message);
    return false;
  }
}

/**
 * Тест 2: Доступность API Bybit
 */
async function testBybitAPI() {
  console.log('🔍 Тест 2: Доступность API Bybit...');
  try {
    const response = await httpGet('https://api.bybit.com/v5/market/tickers?category=spot');
    if (response.status === 200 && response.data.result && response.data.result.list) {
      console.log('✅ PASS: API Bybit доступен, получено', response.data.result.list.length, 'тикеров');
      return true;
    } else {
      console.log('❌ FAIL: Неверный статус или структура ответа');
      return false;
    }
  } catch (error) {
    console.log('❌ FAIL: Ошибка подключения:', error.message);
    return false;
  }
}

/**
 * Тест 3: Доступность API HTX
 */
async function testHTXAPI() {
  console.log('🔍 Тест 3: Доступность API HTX...');
  try {
    const response = await httpGet('https://api.huobi.pro/market/tickers');
    if (response.status === 200 && response.data.data) {
      console.log('✅ PASS: API HTX доступен, получено', response.data.data.length, 'тикеров');
      return true;
    } else {
      console.log('❌ FAIL: Неверный статус или структура ответа');
      return false;
    }
  } catch (error) {
    console.log('❌ FAIL: Ошибка подключения:', error.message);
    return false;
  }
}

/**
 * Запуск всех тестов
 */
async function runAllTests() {
  console.log('\n🧪 Запуск автотестов для API бирж\n');

  const tests = [
    testMEXCAPI,
    testBybitAPI,
    testHTXAPI
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      if (await test()) {
        passed++;
      } else {
        failed++;
      }
    } catch (error) {
      console.log('❌ FAIL: Ошибка выполнения теста:', error.message);
      failed++;
    }
    console.log('---');
  }

  console.log('\n📊 РЕЗУЛЬТАТЫ:');
  console.log(`✅ Пройдено: ${passed}`);
  console.log(`❌ Провалено: ${failed}`);
  console.log(`📈 Итого: ${passed + failed} тестов`);

  if (failed === 0) {
    console.log('\n🎉 Все API-тесты пройдены!');
  } else {
    console.log('\n⚠️ Есть проваленные тесты.');
  }
}

// Запуск
runAllTests();