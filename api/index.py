import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api.nikkei_crawler import get_session, scrape_fund_data
import pandas as pd
import numpy as np

# 캐시 경로 설정
yf.set_tz_cache_location('/tmp')

app = FastAPI(title="Yahoo Finance API", description="Reliable yfinance API", version="1.6.6")
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
            ticker = yf.Ticker(sym)
            info = ticker.info
            results[sym] = {
                "price": info.get('regularMarketPrice'),
                "change": info.get('regularMarketChange'),
                "changePercent": info.get('regularMarketChangePercent'),
                "previousClose": info.get('regularMarketPreviousClose'),
                "currency": info.get('currency'),
                "marketCap": info.get('marketCap'),
                "dayHigh": info.get('dayHigh'),
                "dayLow": info.get('dayLow'),
                "volume": info.get('volume')
            }
        except Exception as e:
            results[sym] = {"error": str(e)}
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
            results[sym] = [
                {
                    "date": str(date)[:10],
                    "open": float(row.get("Open")),
                    "high": float(row.get("High")),
                    "low": float(row.get("Low")),
                    "close": float(row.get("Close")),
                    "volume": float(row.get("Volume"))
                }
                for date, row in df.iterrows()
            ]
        except Exception as e:
            results[sym] = {"error": str(e)}
    return results

@app.get("/dividends")
def get_dividends(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            divs = yf.Ticker(sym).dividends
            div_list = []
            if divs is not None and not divs.empty:
                # 인덱스(날짜)를 기준으로 Series 순회
                for date_idx, val in divs.items():
                    # val이 np.float64이거나 다른 타입일 수 있으므로 float로 변환
                    try:
                        amount = float(val)
                    except:
                        # 배열로 들어오는 예외 케이스 처리
                        amount = float(val) if isinstance(val, (int, float)) else float(val.iloc[0])
                    div_list.append({"date": str(date_idx)[:10], "amount": amount})
            results[sym] = {"dividends": div_list}
        except Exception as e:
            results[sym] = {"error": str(e)}
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
