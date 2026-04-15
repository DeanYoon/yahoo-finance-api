from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from yahooquery import Ticker
from typing import Optional
from datetime import datetime, timedelta
# Nikkei router (inline — nikkei_router.py was removed)
from fastapi import APIRouter
from api.nikkei_crawler import get_session, scrape_fund_data

nikkei_router = APIRouter()

@nikkei_router.get("/{fcode}")
def get_nikkei_fund(fcode: str):
    session = get_session()
    return scrape_fund_data(session, fcode)

import pandas as pd
import json

app = FastAPI(
    title="Yahoo Finance API",
    description="Yahoo Finance data via yahooquery + Nikkei scraping",
    version="1.0.0"
)

# Nikkei Fund Scraper 라우터 등록
app.include_router(nikkei_router, prefix="/nikkei")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "endpoints": [
            "GET /quote?symbols=AAPL,MSFT — 시세 정보",
            "GET /summary?symbols=AAPL — 요약 정보",
            "GET /history?symbols=AAPL&period=6mo — 과거 데이터",
            "GET /dividends?symbols=AAPL — 배당 내역",
            "GET /search?q=Apple — 종목 검색",
            "GET /nikkei/4731925B — 니케이 일본 펀드",
        ],
    }


@app.get("/quote")
def get_quote(symbols: str = Query(..., description="콤마 구분 종목 심볼")):
    """실시간 시세 정보 (가격, 변동률, 시가총액 등)"""
    try:
        syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not syms:
            raise HTTPException(status_code=400, detail="심볼을 입력하세요")

        url = "https://query1.finance.yahoo.com/v10/finance/quote"
        params = {"symbols": ",".join(syms)}
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        results = body.get("quoteResponse", {}).get("result", [])
        quote_map = {r["symbol"]: r for r in results if "symbol" in r}

        result = {}
        for sym in syms:
            d = quote_map.get(sym, {})
            if d:
                result[sym] = {
                    "price": d.get("regularMarketPrice"),
                    "change": d.get("regularMarketChange"),
                    "changePercent": d.get("regularMarketChangePercent"),
                    "marketCap": d.get("marketCap"),
                    "currency": d.get("currency"),
                    "exchange": d.get("exchangeName"),
                    "previousClose": d.get("regularMarketPreviousClose"),
                    "dayHigh": d.get("regularMarketDayHigh"),
                    "dayLow": d.get("regularMarketDayLow"),
                    "volume": d.get("regularMarketVolume"),
                    "marketState": d.get("marketState"),
                }
            else:
                result[sym] = {"price": None, "error": "데이터 없음"}

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary")
def get_summary(symbols: str = Query(..., description="콤마 구분 종목 심볼")):
    """종목 요약 정보 (PER, EPS, 52주 고저, 배당수익률 등)"""
    try:
        syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not syms:
            raise HTTPException(status_code=400, detail="심볼을 입력하세요")

        t = Ticker(syms)
        data = t.summary_detail

        result = {}
        for sym in syms:
            d = data.get(sym, {})
            result[sym] = {
                "trailingPE": d.get("trailingPE"),
                "forwardPE": d.get("forwardPE"),
                "dividendYield": d.get("dividendYield"),
                "fiftyTwoWeekHigh": d.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": d.get("fiftyTwoWeekLow"),
                "beta": d.get("beta"),
                "volume": d.get("volume"),
                "averageVolume": d.get("averageVolume"),
                "marketCap": d.get("marketCap"),
            }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
def get_history(
    symbols: str = Query(..., description="콤마 구분 종목 심볼"),
    period: str = Query("1mo", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query("1d", description="1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo"),
):
    """과거 주가 데이터 (OHLCV)"""
    print(f"[DEBUG] /history request: symbols={symbols}, period={period}, interval={interval}")
    try:
        syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not syms:
            raise HTTPException(status_code=400, detail="심볼을 입력하세요")

        t = Ticker(syms)
        hist = t.history(period=period, interval=interval)

        if isinstance(hist, dict):
            return hist

        # DataFrame -> JSON 직렬화
        # MultiIndex인 경우 처리
        if hasattr(hist.index, "names") and "symbol" in hist.index.names:
            result = {}
            for sym in syms:
                try:
                    sym_data = hist.xs(sym, level="symbol")
                    result[sym] = sym_data.to_dict(orient="index")
                except (KeyError, TypeError):
                    result[sym] = []
            return result
        else:
            return {"data": hist.to_dict(orient="index")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dividends")
def get_dividends(
    symbols: str = Query(..., description="콤마 구분 종목 심볼"),
    years: int = Query(5, description="조회 기간 (년)"),
):
    """배당 내역 + 해당 날짜의 종가(close) 포함"""
    try:
        syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not syms:
            raise HTTPException(status_code=400, detail="심볼을 입력하세요")

        start = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")

        # Get dividends using single Ticker
        t = Ticker(syms)
        data = t.dividend_history(start=start)

        # Get historical prices for the same period to find close prices
        hist = t.history(start=start)

        result = {}
        for sym in syms:
            try:
                # Extract dividend entries
                if isinstance(data, pd.DataFrame):
                    try:
                        sym_data_df = data.xs(sym, level="symbol")
                        sym_data = sym_data_df.to_dict(orient="index")
                    except KeyError:
                        sym_data = {}
                elif isinstance(data, dict):
                    sym_data = data.get(sym, [])
                else:
                    sym_data = []

                # Extract price history for this symbol
                price_map = {}
                if isinstance(hist, pd.DataFrame):
                    try:
                        hist_sym = hist.xs(sym, level="symbol")
                    except KeyError:
                        hist_sym = pd.DataFrame()
                else:
                    hist_sym = hist.get(sym) if isinstance(hist, dict) else pd.DataFrame()

                if isinstance(hist_sym, pd.DataFrame) and not hist_sym.empty:
                    # Build a mapping of date string to close price
                    if "close" in hist_sym.columns:
                        price_map = {
                            str(idx)[:10]: row.get("close", row.get("Close"))
                            for idx, row in hist_sym.iterrows()
                            if row.get("close", row.get("Close")) is not None
                        }
                    elif "Close" in hist_sym.columns:
                        price_map = {
                            str(idx)[:10]: row.get("Close")
                            for idx, row in hist_sym.iterrows()
                            if row.get("Close") is not None
                        }

                # Build result
                # Ensure dividend entries are properly mapped
                if isinstance(sym_data, dict):
                    entries = []
                    # sym_data could have keys as timestamps or strings
                    for date, val in sorted(sym_data.items()):
                        # date might be a Timestamp
                        date_str = str(date)[:10]
                        
                        # Fix: Handle multiple structures for 'val'
                        # Structure 1: {'2025-02-10': {'dividends': 0.25}}
                        # Structure 2: {'2025-02-10': 0.25} (if from simple list)
                        if isinstance(val, dict):
                            amount = val.get("dividends") if "dividends" in val else val.get("amount")
                        else:
                            amount = val
                            
                        close = price_map.get(date_str)
                        entries.append({
                            "date": date_str,
                            "amount": amount,
                            "close": close,
                        })
                    result[sym] = entries
            except Exception:
                result[sym] = []

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search_ticker(q: str = Query(..., description="검색어"), count: int = Query(8, description="결과 수")):
    """종목 검색"""
    try:
        import requests

        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": q, "quotesCount": count}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        quotes = data.get("quotes", [])
        return [
            {
                "symbol": item.get("symbol"),
                "name": item.get("shortname") or item.get("longname"),
                "exchange": item.get("exchange"),
                "type": item.get("quoteType"),
            }
            for item in quotes[:count]
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
