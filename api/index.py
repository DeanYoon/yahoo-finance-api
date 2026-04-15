import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from api.nikkei_crawler import get_session, scrape_fund_data
import json

app = FastAPI(title="Yahoo Finance API", description="Stable yfinance-based API", version="1.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

nikkei_router = APIRouter()
@nikkei_router.get("/{fcode}")
def get_nikkei_fund(fcode: str):
    return scrape_fund_data(get_session(), fcode)
app.include_router(nikkei_router, prefix="/nikkei")

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
            results[sym] = ticker.fast_info
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
        except Exception as e:
            results[sym] = {"error": str(e)}
    return results

@app.get("/history")
def get_history(symbols: str, period: str = "1mo", interval: str = "1d"):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            df = yf.Ticker(sym).history(period=period, interval=interval)
            results[sym] = df.to_dict(orient="index")
        except Exception as e:
            results[sym] = {"error": str(e)}
    return results

@app.get("/dividends")
def get_dividends(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            results[sym] = yf.Ticker(sym).dividends.to_dict()
        except Exception as e:
            results[sym] = {"error": str(e)}
    return results

@app.get("/search")
def search(q: str):
    import requests
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    resp = requests.get(url, params={"q": q}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    return resp.json().get("quotes", [])
