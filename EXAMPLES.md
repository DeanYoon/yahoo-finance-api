# Yahoo Finance API

**Base URL:** `https://yahoo-finance-api-seven.vercel.app`

---

## 1. Root

```bash
curl "https://yahoo-finance-api-seven.vercel.app/"
```

---

## 2. 시세 정보 (Quote)

```bash
# 단일 종목
curl "https://yahoo-finance-api-seven.vercel.app/quote?symbols=AAPL"

# 여러 종목
curl "https://yahoo-finance-api-seven.vercel.app/quote?symbols=AAPL,MSFT,GOOGL,TSLA"
```

**Response:**
```json
{
  "AAPL": {
    "price": 255.92,
    "change": 0.29,
    "changePercent": 0.0011,
    "marketCap": 3761492983808,
    "currency": "USD",
    "exchange": "NasdaqGS",
    "previousClose": 255.63,
    "dayHigh": 256.13,
    "dayLow": 250.65,
    "volume": 31289369,
    "marketState": "CLOSED"
  }
}
```

---

## 3. 요약 정보 (Summary)

```bash
# PER, 배당수익률, 52주 고저, 베타, 거래량
curl "https://yahoo-finance-api-seven.vercel.app/summary?symbols=AAPL"
```

**Response:**
```json
{
  "AAPL": {
    "trailingPE": 32.35,
    "forwardPE": 27.47,
    "dividendYield": 0.0041,
    "fiftyTwoWeekHigh": 288.62,
    "fiftyTwoWeekLow": 169.21,
    "beta": 1.109,
    "volume": 31289369,
    "averageVolume": 47741423,
    "marketCap": 3761492983808
  }
}
```

---

## 4. 과거 주가 (History)

```bash
# 기간: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
# 간격: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

curl "https://yahoo-finance-api-seven.vercel.app/history?symbols=AAPL&period=5d"
curl "https://yahoo-finance-api-seven.vercel.app/history?symbols=AAPL&period=6mo&interval=1wk"
curl "https://yahoo-finance-api-seven.vercel.app/history?symbols=AAPL,MSFT&period=1y"
```

**Response:**
```json
{
  "AAPL": {
    "2026-03-27": {
      "open": 253.90,
      "high": 255.49,
      "low": 248.07,
      "close": 248.80,
      "volume": 47900000,
      "adjclose": 248.80
    }
  }
}
```

---

## 5. 배당 내역 (Dividends)

```bash
# 기본 5년치
curl "https://yahoo-finance-api-seven.vercel.app/dividends?symbols=AAPL"

# 기간 지정 (년)
curl "https://yahoo-finance-api-seven.vercel.app/dividends?symbols=AAPL&years=10"

# 여러 종목
curl "https://yahoo-finance-api-seven.vercel.app/dividends?symbols=AAPL,JNJ,KO"
```

**Response:**
```json
{
  "AAPL": [
    {
      "date": "2024-05-10",
      "amount": 0.25
    },
    {
      "date": "2024-08-12",
      "amount": 0.25
    },
    {
      "date": "2025-02-10",
      "amount": 0.25
    }
  ]
}
```

---

## 6. 종목 검색 (Search)

```bash
curl "https://yahoo-finance-api-seven.vercel.app/search?q=Apple"
curl "https://yahoo-finance-api-seven.vercel.app/search?q=Tesla&count=5"
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NMS",
    "type": "EQUITY"
  }
]
```

---

## Python 예제

```python
import requests

BASE = "https://yahoo-finance-api-seven.vercel.app"

# AAPL 시세 + 배당 + 1년 치 주가
def get_stock_data(symbol):
    quote = requests.get(f"{BASE}/quote?symbols={symbol}").json()
    summary = requests.get(f"{BASE}/summary?symbols={symbol}").json()
    divs = requests.get(f"{BASE}/dividends?symbols={symbol}&years=5").json()
    hist = requests.get(f"{BASE}/history?symbols={symbol}&period=1y").json()

    return {
        "quote": quote,
        "summary": summary,
        "dividends": divs,
        "history": hist,
    }

data = get_stock_data("AAPL")
print(f"AAPL 현재가: {data['quote']['AAPL']['price']}")
print(f"AAPL PER: {data['summary']['AAPL']['trailingPE']}")
print(f"AAPL 배당 건수: {len(data['dividends']['AAPL'])}")
print(f"AAPL 히스토리 항목수: {len(data['history']['AAPL'])}")
```
