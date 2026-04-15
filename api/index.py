import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api.nikkei_crawler import get_session, scrape_fund_data
import os

# Serverless (Vercel) 환경의 쓰기 가능한 경로로 캐시 위치 설정
yf.set_tz_cache_location('/tmp')

app = FastAPI(title="Yahoo Finance API", description="Robust yfinance API", version="1.2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/quote", "/summary", "/history", "/dividends", "/search"]}

@app.get("/quote")
def get_quote(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            # fast_info는 데이터가 없는 심볼 조회 시 에러가 잦으므로 info를 사용하거나 예외 처리
            ticker = yf.Ticker(sym)
            info = ticker.fast_info
            results[sym] = {
                "price": info.get('last_price'),
                "currency": info.get('currency'),
                "marketCap": info.get('market_cap'),
                "dayHigh": info.get('day_high'),
                "dayLow": info.get('day_low'),
                "volume": info.get('last_volume')
            }
        except Exception:
            results[sym] = {"error": "Symbol not found or data unavailable"}
    return results

@app.get("/summary")
def get_summary(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            ticker = yf.Ticker(sym)
            results[sym] = ticker.info
        except Exception:
            results[sym] = {"error": "Symbol not found"}
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
            results[sym] = {"error": "History data unavailable"}
    return results

@app.get("/dividends")
def get_dividends(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            divs = yf.Ticker(sym).dividends
            results[sym] = divs.to_dict() if not divs.empty else {}
        except Exception:
            results[sym] = {"error": "Dividend data unavailable"}
    return results

@app.get("/search")
def search(q: str):
    import requests
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        resp = requests.get(url, params={"q": q}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return resp.json().get("quotes", [])
    except:
        return []
