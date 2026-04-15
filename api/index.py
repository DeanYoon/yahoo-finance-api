import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api.nikkei_crawler import get_session, scrape_fund_data

# 캐시 경로 설정
yf.set_tz_cache_location('/tmp')

app = FastAPI(title="Yahoo Finance API", description="Reliable yfinance API", version="1.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/quote")
def get_quote(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            ticker = yf.Ticker(sym)
            # info가 가장 확실하지만 느림. 1d history를 통해 실시간 근사치 확보 시도
            hist = ticker.history(period="1d")
            data = ticker.info
            results[sym] = {
                "price": hist['Close'].iloc[-1] if not hist.empty else data.get('regularMarketPrice'),
                "currency": data.get('currency'),
                "marketCap": data.get('marketCap'),
                "dayHigh": data.get('dayHigh'),
                "dayLow": data.get('dayLow'),
                "volume": data.get('volume')
            }
        except Exception:
            results[sym] = {"error": "Failed to fetch"}
    return results

@app.get("/summary")
def get_summary(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            results[sym] = yf.Ticker(sym).info
        except Exception:
            results[sym] = {"error": "Failed to fetch"}
    return results

@app.get("/history")
def get_history(symbols: str, period: str = "1mo", interval: str = "1d"):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            df = yf.Ticker(sym).history(period=period, interval=interval)
            results[sym] = df.to_dict(orient="index") if not df.empty else []
        except Exception:
            results[sym] = {"error": "Failed to fetch"}
    return results

@app.get("/dividends")
def get_dividends(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            ticker = yf.Ticker(sym)
            divs = ticker.dividends
            # 프론트엔드가 기대하는 [{date, amount}, ...] 형식으로 변환
            results[sym] = {
                "dividends": [{"date": str(d.date())[:10], "amount": float(v)} for d, v in divs.items()]
            }
        except Exception:
            results[sym] = {"error": "Failed to fetch"}
    return results

@app.get("/search")
def search(q: str):
    import requests
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        resp = requests.get(url, params={"q": q}, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        return resp.json().get("quotes", [])
    except:
        return []
