import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime
from fastapi import APIRouter
from api.nikkei_crawler import get_session, scrape_fund_data
import json

nikkei_router = APIRouter()

@nikkei_router.get("/{fcode}")
def get_nikkei_fund(fcode: str):
    session = get_session()
    return scrape_fund_data(session, fcode)

app = FastAPI(
    title="Yahoo Finance API",
    description="Yahoo Finance data via requests + Nikkei scraping",
    version="1.0.0"
)

app.include_router(nikkei_router, prefix="/nikkei")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {"User-Agent": "Mozilla/5.0"}


@app.get("/")
def root():
    return {
        "status": "ok",
        "endpoints": [
            "GET /quote?symbols=AAPL,MSFT",
            "GET /summary?symbols=AAPL",
            "GET /history?symbols=AAPL&period=6mo&interval=1d",
            "GET /dividends?symbols=AAPL",
            "GET /search?q=Apple",
            "GET /nikkei/4731925B",
        ],
    }

@app.get("/quote")
def get_quote(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules=price"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            data = resp.json()
            res = data.get("quoteSummary", {}).get("result", [{}])[0].get("price", {})
            results[sym] = res
        except:
            results[sym] = {"error": "Failed to fetch"}
    return results

@app.get("/summary")
def get_summary(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules=summaryDetail"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json().get("quoteSummary", {}).get("result", [{}])[0].get("summaryDetail", {})
        results[sym] = data
    return results

@app.get("/history")
def get_history(symbols: str, period: str = "1mo", interval: str = "1d"):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={period}&interval={interval}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        results[sym] = resp.json().get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0]
    return results

@app.get("/dividends")
def get_dividends(symbols: str):
    results = {}
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5y&interval=1d"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        events = resp.json().get("chart", {}).get("result", [{}])[0].get("events", {}).get("dividends", {})
        results[sym] = events
    return results

@app.get("/search")
def search_ticker(q: str):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    resp = requests.get(url, params={"q": q}, headers=HEADERS, timeout=10)
    return resp.json().get("quotes", [])
