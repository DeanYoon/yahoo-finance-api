import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api.nikkei_crawler import get_session, scrape_fund_data
import pandas as pd

# 캐시 경로 설정
yf.set_tz_cache_location('/tmp')

app = FastAPI(title="Yahoo Finance API", description="Reliable yfinance API", version="1.6.4")
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
                for d, v in divs.items():
                    # 안전한 float 변환
                    if isinstance(v, (pd.Series, pd.DataFrame)):
                        val = float(v.iloc[0])
                    else:
                        val = float(v)
                    div_list.append({"date": str(d)[:10], "amount": val})
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
