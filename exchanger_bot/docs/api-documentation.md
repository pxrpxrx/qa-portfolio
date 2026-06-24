# API-документация: BestChange

**Сервис:** BestChange (агрегатор обменников)  
**Версия API:** v2  
**URL:** `https://bestchange.app/v2`

---

## Аутентификация

API-ключ передаётся в URL:
https://bestchange.app/v2/{API_KEY}/rates/{from_id}-{to_id}


---

## Получение курса

### Запрос

GET /{API_KEY}/rates/{from_id}-{to_id}


### Параметры

| Параметр | Тип | Описание |
|:---|:---|:---|
| `API_KEY` | string | Ключ доступа |
| `from_id` | integer | ID валюты продажи |
| `to_id` | integer | ID валюты покупки |

### ID валют

| Валюта | ID |
|:---|:---|
| BTC | 93 |
| USDT (TRC20) | 10 |
| RUB | 105 |

### Пример запроса
```bash
curl -X GET "https://bestchange.app/v2/YOUR_API_KEY/rates/93-105"\

{
  "rates": {
    "93-105": [
      {
        "changer": 1029,
        "rate": 0.000016,
        "reserve": 1000000,
        "inmin": 500,
        "inmax": 5000000
      }
    ]
  }
}

def get_bestchange_rate(from_id, to_id, exchanger_id=None):
    url = f"https://bestchange.app/v2/{API_KEY}/rates/{from_id}-{to_id}"
    resp = requests.get(url)
    data = resp.json()
    
    rates = data.get('rates', {}).get(f"{from_id}-{to_id}", [])
    
    if exchanger_id:
        for rate in rates:
            if rate.get('changer') == exchanger_id:
                return rate
        return rates[0] if rates else None
    return rates[0] if rates else None

    ### Пример ответа (успешный)
```json
{
  "rates": {
    "93-105": [
      {
        "changer": 1029,
        "rate": 0.000016,
        "reserve": 1000000,
        "inmin": 500,
        "inmax": 5000000
      }
    ]
  }
}