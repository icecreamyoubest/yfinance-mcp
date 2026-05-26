"""
Yahoo Finance MCP Server for Hugging Face Spaces - Gradio MCP Style

Runtime style:
- Hugging Face Space SDK: Gradio
- MCP endpoint: /gradio_api/mcp/ and /gradio_api/mcp/sse
- Launch: demo.launch(mcp_server=True)

This app intentionally avoids FastMCP's standalone /mcp transport because
Hugging Face Spaces commonly exposes Gradio MCP servers through /gradio_api/mcp/.
"""

from __future__ import annotations

import json
import concurrent.futures
import logging
from functools import lru_cache
import os
import time
from typing import Any, Dict, List, Optional

import gradio as gr
import yfinance as yf

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("yfinance-gradio-mcp")

# Configuration for network resilience
YFINANCE_TIMEOUT_SECONDS = 10
YFINANCE_MAX_RETRIES = 3
YFINANCE_RETRY_DELAY_SECONDS = 2

# Increased workers to prevent bottlenecks and handle concurrent requests better
executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------


def to_json(data: Any) -> str:
    """Serialize data to stable pretty JSON."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def normalize_ticker(ticker: str) -> str:
    """Normalize user ticker input for Yahoo Finance."""
    return (ticker or "").strip().upper()


def parse_ticker_list(tickers: str) -> List[str]:
    """Parse comma/newline/space separated tickers into a clean list."""
    if not tickers:
        return []

    raw = tickers.replace("\n", ",").replace(";", ",").split(",")
    parsed: List[str] = []

    for item in raw:
        item = item.strip()
        if not item:
            continue
        # Also support accidental space-separated input such as "AAPL MSFT NVDA".
        for sub in item.split():
            normalized = normalize_ticker(sub)
            if normalized and normalized not in parsed:
                parsed.append(normalized)

    return parsed[:10]


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        number = float(value)
        if number != number:  # NaN check
            return None
        return number
    except Exception:
        return None


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def safe_money(value: Any, currency: str = "USD") -> str:
    number = safe_float(value)
    if number is None:
        return "unknown"
    return f"{currency} {number:,.2f}"


def safe_market_cap(value: Any, currency: str = "USD") -> str:
    number = safe_int(value)
    if number is None:
        return "unknown"
    return f"{currency} {number:,}"


def safe_percent(value: Any) -> Optional[str]:
    number = safe_float(value)
    if number is None:
        return None
    return f"{number * 100:.2f}%"


@lru_cache(maxsize=128)
def yahoo_info(ticker: str) -> Dict[str, Any]:
    """Fetch info directly to avoid nested executor deadlocks."""
    for attempt in range(YFINANCE_MAX_RETRIES):
        try:
            stock = yf.Ticker(ticker)
            # Accessing .info triggers the actual network request
            info = stock.info
            if info:
                return info
        except Exception as exc:
            logger.error("Attempt %d: yfinance request failed for %s: %s", attempt + 1, ticker, exc)
        
        if attempt < YFINANCE_MAX_RETRIES - 1:
            time.sleep(YFINANCE_RETRY_DELAY_SECONDS * (2 ** attempt))
    return {}


# -----------------------------------------------------------------------------
# MCP-exposed functions
# -----------------------------------------------------------------------------


def health_check() -> str:
    """
    Check whether the Yahoo Finance MCP server is running.

    Returns:
        JSON string with service status, runtime style, and expected MCP paths.
    """
    return to_json(
        {
            "ok": True,
            "service": "Yahoo Finance Gradio MCP Server",
            "runtime": "huggingface-spaces-gradio",
            "mcp_endpoints": ["/gradio_api/mcp/", "/gradio_api/mcp/sse"],
            "timestamp": int(time.time()),
        }
    )


def get_stock_quote(ticker: str) -> str:
    """
    Get latest available quote and core financial metrics for a stock.

    Args:
        ticker: Yahoo Finance ticker, for example AAPL, NVDA, MSFT, TSLA, or 0700.HK.

    Returns:
        JSON string containing quote, market cap, PE ratios, sector, industry, and business summary.
    """
    ticker = normalize_ticker(ticker)
    if not ticker:
        return to_json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        info = yahoo_info(ticker)
        if not info:
            return to_json(
                {
                    "ok": False,
                    "ticker": ticker,
                    "error": "No data returned from Yahoo Finance.",
                }
            )

        currency = info.get("currency") or "USD"
        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )

        return to_json(
            {
                "ok": True,
                "ticker": ticker,
                "company_name": info.get("longName") or info.get("shortName") or "unknown",
                "exchange": info.get("exchange") or "unknown",
                "quote_type": info.get("quoteType") or "unknown",
                "currency": currency,
                "current_price": safe_money(current_price, currency),
                "previous_close": safe_money(info.get("previousClose"), currency),
                "open": safe_money(info.get("open"), currency),
                "day_high": safe_money(info.get("dayHigh"), currency),
                "day_low": safe_money(info.get("dayLow"), currency),
                "fifty_two_week_high": safe_money(info.get("fiftyTwoWeekHigh"), currency),
                "fifty_two_week_low": safe_money(info.get("fiftyTwoWeekLow"), currency),
                "market_cap": safe_market_cap(info.get("marketCap"), currency),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": safe_percent(info.get("dividendYield")),
                "beta": info.get("beta"),
                "sector": info.get("sector") or "unknown",
                "industry": info.get("industry") or "unknown",
                "website": info.get("website") or "unknown",
                "business_summary": (info.get("longBusinessSummary") or "")[:900],
                "data_source": "Yahoo Finance via yfinance",
                "disclaimer": "Market data may be delayed or incomplete. Not financial advice.",
            }
        )

    except Exception as exc:
        logger.exception("get_stock_quote failed for ticker=%s", ticker)
        return to_json(
            {
                "ok": False,
                "ticker": ticker,
                "error": str(exc),
                "hint": "Use Yahoo Finance ticker format, e.g. AAPL, NVDA, MSFT, 0700.HK.",
            }
        )


def get_company_profile(ticker: str) -> str:
    """
    Get company profile information for a stock.

    Args:
        ticker: Yahoo Finance ticker, for example AAPL, NVDA, MSFT, or 0700.HK.

    Returns:
        JSON string containing country, city, website, sector, industry, employees, and business summary.
    """
    ticker = normalize_ticker(ticker)
    if not ticker:
        return to_json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        info = yahoo_info(ticker)
        return to_json(
            {
                "ok": True,
                "ticker": ticker,
                "company_name": info.get("longName") or info.get("shortName") or "unknown",
                "country": info.get("country") or "unknown",
                "city": info.get("city") or "unknown",
                "address": info.get("address1") or "unknown",
                "website": info.get("website") or "unknown",
                "sector": info.get("sector") or "unknown",
                "industry": info.get("industry") or "unknown",
                "full_time_employees": info.get("fullTimeEmployees"),
                "phone": info.get("phone") or "unknown",
                "business_summary": info.get("longBusinessSummary") or "unknown",
                "data_source": "Yahoo Finance via yfinance",
            }
        )
    except Exception as exc:
        logger.exception("get_company_profile failed for ticker=%s", ticker)
        return to_json({"ok": False, "ticker": ticker, "error": str(exc)})


def get_stock_history(ticker: str, period: str = "5d", interval: str = "1d", limit: int = 20) -> str:
    """
    Get recent historical OHLCV data for a stock.

    Args:
        ticker: Yahoo Finance ticker, for example AAPL, NVDA, MSFT, or 0700.HK.
        period: Data period, for example 1d, 5d, 1mo, 3mo, 6mo, 1y, or 5y.
        interval: Data interval, for example 1m, 5m, 15m, 1h, 1d, or 1wk.
        limit: Maximum rows to return. Range is clamped to 1-100.

    Returns:
        JSON string containing historical OHLCV rows.
    """
    ticker = normalize_ticker(ticker)
    if not ticker:
        return to_json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        limit_int = max(1, min(int(limit), 100))
    except Exception:
        limit_int = 20

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return to_json(
                {
                    "ok": False,
                    "ticker": ticker,
                    "period": period,
                    "interval": interval,
                    "error": "No historical data returned.",
                }
            )

        rows = []
        for idx, row in hist.tail(limit_int).iterrows():
            rows.append(
                {
                    "datetime": str(idx),
                    "open": safe_float(row.get("Open")),
                    "high": safe_float(row.get("High")),
                    "low": safe_float(row.get("Low")),
                    "close": safe_float(row.get("Close")),
                    "volume": safe_int(row.get("Volume")),
                }
            )

        return to_json(
            {
                "ok": True,
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "rows_returned": len(rows),
                "rows": rows,
                "data_source": "Yahoo Finance via yfinance",
            }
        )
    except Exception as exc:
        logger.exception("get_stock_history failed for ticker=%s", ticker)
        return to_json(
            {
                "ok": False,
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "error": str(exc),
            }
        )


def compare_stocks(tickers: str) -> str:
    """
    Compare multiple stocks by valuation, market cap, beta, sector, and industry.

    Args:
        tickers: Comma-separated Yahoo Finance tickers, for example AAPL,MSFT,NVDA.

    Returns:
        JSON string containing a comparison table for up to 10 tickers.
    """
    ticker_list = parse_ticker_list(tickers)
    if not ticker_list:
        return to_json(
            {
                "ok": False,
                "error": "tickers are required",
                "example": "AAPL,MSFT,NVDA",
            }
        )

    results: List[Dict[str, Any]] = []
    # Use the shared executor to fetch info for multiple tickers concurrently
    futures = {executor.submit(yahoo_info, ticker): ticker for ticker in ticker_list}

    for future in concurrent.futures.as_completed(futures):
        ticker = futures[future]
        try:
            info = future.result()
            if not info:
                results.append(
                    {
                        "ok": False,
                        "ticker": ticker,
                        "error": "No data returned from Yahoo Finance.",
                    }
                )
                continue

            currency = info.get("currency") or "USD"
            current_price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("previousClose")
            )
            results.append(
                {
                    "ok": True,
                    "ticker": ticker,
                    "company_name": info.get("longName") or info.get("shortName") or "unknown",
                    "currency": currency,
                    "current_price": safe_float(current_price),
                    "market_cap": safe_int(info.get("marketCap")),
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "price_to_book": info.get("priceToBook"),
                    "beta": info.get("beta"),
                    "sector": info.get("sector") or "unknown",
                    "industry": info.get("industry") or "unknown",
                }
            )
        except Exception as exc:
            logger.exception("compare_stocks failed for ticker=%s: %s", ticker, exc)
            results.append({"ok": False, "ticker": ticker, "error": str(exc)})

    return to_json(
        {
            "ok": True,
            "tickers": ticker_list,
            "results": results,
            "data_source": "Yahoo Finance via yfinance",
            "disclaimer": "Market data may be delayed or incomplete. Not financial advice.",
        }
    )


def get_financial_risk_snapshot(ticker: str) -> str:
    """
    Generate a basic financial risk snapshot using Yahoo Finance indicators.

    Args:
        ticker: Yahoo Finance ticker, for example AAPL, NVDA, MSFT, TSLA, or 0700.HK.

    Returns:
        JSON string containing valuation, volatility, leverage, liquidity, profitability, growth, and rule-based risk flags.
    """
    ticker = normalize_ticker(ticker)
    if not ticker:
        return to_json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        info = yahoo_info(ticker)

        beta = safe_float(info.get("beta"))
        trailing_pe = safe_float(info.get("trailingPE"))
        forward_pe = safe_float(info.get("forwardPE"))
        debt_to_equity = safe_float(info.get("debtToEquity"))
        profit_margins = safe_float(info.get("profitMargins"))
        operating_margins = safe_float(info.get("operatingMargins"))
        current_ratio = safe_float(info.get("currentRatio"))
        quick_ratio = safe_float(info.get("quickRatio"))
        revenue_growth = safe_float(info.get("revenueGrowth"))
        earnings_growth = safe_float(info.get("earningsGrowth"))

        risk_flags: List[str] = []
        if beta is not None and beta > 1.5:
            risk_flags.append("High beta: stock may be more volatile than the broader market.")
        if trailing_pe is not None and trailing_pe > 50:
            risk_flags.append("High trailing PE: valuation may be expensive relative to earnings.")
        if debt_to_equity is not None and debt_to_equity > 150:
            risk_flags.append("High debt-to-equity: leverage risk may be elevated.")
        if profit_margins is not None and profit_margins < 0:
            risk_flags.append("Negative profit margin: company is currently unprofitable.")
        if current_ratio is not None and current_ratio < 1:
            risk_flags.append("Current ratio below 1: short-term liquidity may be weak.")
        if revenue_growth is not None and revenue_growth < 0:
            risk_flags.append("Negative revenue growth: sales are contracting.")
        if earnings_growth is not None and earnings_growth < 0:
            risk_flags.append("Negative earnings growth: profitability trend may be weakening.")
        if not risk_flags:
            risk_flags.append("No major risk flags detected from available Yahoo Finance indicators.")

        return to_json(
            {
                "ok": True,
                "ticker": ticker,
                "company_name": info.get("longName") or info.get("shortName") or "unknown",
                "valuation": {
                    "trailing_pe": trailing_pe,
                    "forward_pe": forward_pe,
                    "price_to_book": info.get("priceToBook"),
                    "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                    "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                },
                "volatility": {
                    "beta": beta,
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                },
                "leverage_liquidity": {
                    "debt_to_equity": debt_to_equity,
                    "current_ratio": current_ratio,
                    "quick_ratio": quick_ratio,
                    "total_debt": info.get("totalDebt"),
                    "total_cash": info.get("totalCash"),
                },
                "profitability_growth": {
                    "profit_margins": profit_margins,
                    "operating_margins": operating_margins,
                    "return_on_assets": info.get("returnOnAssets"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "revenue_growth": revenue_growth,
                    "earnings_growth": earnings_growth,
                },
                "risk_flags": risk_flags,
                "data_source": "Yahoo Finance via yfinance",
                "disclaimer": "This is not financial advice. It is a simple data-driven risk snapshot and may be incomplete or delayed.",
            }
        )
    except Exception as exc:
        logger.exception("get_financial_risk_snapshot failed for ticker=%s", ticker)
        return to_json({"ok": False, "ticker": ticker, "error": str(exc)})


# -----------------------------------------------------------------------------
# Gradio UI + API endpoints. Each button click with api_name becomes an API route.
# With launch(mcp_server=True), Gradio exposes these routes as MCP tools.
# -----------------------------------------------------------------------------

with gr.Blocks(title="Yahoo Finance MCP Server") as demo:
    gr.Markdown(
        """
# Yahoo Finance MCP Server

This Hugging Face Space exposes stock tools as a **Gradio MCP server**.

Expected MCP endpoints after deployment:

```text
/gradio_api/mcp/
/gradio_api/mcp/sse
```

Use this Space from MCP-compatible clients such as OpenAI remote MCP, Cursor, Claude Desktop bridge, or MCP Inspector.
        """
    )

    with gr.Tab("Health"):
        health_btn = gr.Button("Run health_check")
        health_output = gr.Code(label="health_check output", language="json")
        health_btn.click(
            fn=health_check,
            inputs=[],
            outputs=health_output,
            api_name="health_check",
        )

    with gr.Tab("Stock Quote"):
        quote_ticker = gr.Textbox(label="Ticker", value="NVDA", placeholder="AAPL, NVDA, MSFT, 0700.HK")
        quote_btn = gr.Button("Get stock quote")
        quote_output = gr.Code(label="get_stock_quote output", language="json")
        quote_btn.click(
            fn=get_stock_quote,
            inputs=[quote_ticker],
            outputs=quote_output,
            api_name="get_stock_quote",
        )

    with gr.Tab("Company Profile"):
        profile_ticker = gr.Textbox(label="Ticker", value="AAPL", placeholder="AAPL, NVDA, MSFT, 0700.HK")
        profile_btn = gr.Button("Get company profile")
        profile_output = gr.Code(label="get_company_profile output", language="json")
        profile_btn.click(
            fn=get_company_profile,
            inputs=[profile_ticker],
            outputs=profile_output,
            api_name="get_company_profile",
        )

    with gr.Tab("History"):
        hist_ticker = gr.Textbox(label="Ticker", value="AAPL")
        hist_period = gr.Dropdown(
            label="Period",
            choices=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
            value="5d",
        )
        hist_interval = gr.Dropdown(
            label="Interval",
            choices=["1m", "5m", "15m", "30m", "1h", "1d", "1wk"],
            value="1d",
        )
        hist_limit = gr.Number(label="Limit", value=20, precision=0)
        hist_btn = gr.Button("Get stock history")
        hist_output = gr.Code(label="get_stock_history output", language="json")
        hist_btn.click(
            fn=get_stock_history,
            inputs=[hist_ticker, hist_period, hist_interval, hist_limit],
            outputs=hist_output,
            api_name="get_stock_history",
        )

    with gr.Tab("Compare"):
        compare_tickers = gr.Textbox(label="Tickers", value="AAPL,MSFT,NVDA", placeholder="AAPL,MSFT,NVDA")
        compare_btn = gr.Button("Compare stocks")
        compare_output = gr.Code(label="compare_stocks output", language="json")
        compare_btn.click(
            fn=compare_stocks,
            inputs=[compare_tickers],
            outputs=compare_output,
            api_name="compare_stocks",
        )

    with gr.Tab("Risk Snapshot"):
        risk_ticker = gr.Textbox(label="Ticker", value="TSLA", placeholder="AAPL, NVDA, TSLA")
        risk_btn = gr.Button("Get financial risk snapshot")
        risk_output = gr.Code(label="get_financial_risk_snapshot output", language="json")
        risk_btn.click(
            fn=get_financial_risk_snapshot,
            inputs=[risk_ticker],
            outputs=risk_output,
            api_name="get_financial_risk_snapshot",
        )


if __name__ == "__main__":
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("PORT", os.getenv("SPACE_PORT", "7860")))

    logger.info("Starting Gradio MCP server on %s:%s", server_name, server_port)
    logger.info("Expected MCP endpoints: /gradio_api/mcp/ and /gradio_api/mcp/sse")

    # Do not use demo.queue().launch(...) here. Some Gradio/HF combinations have
    # stricter launch signatures or queue interaction issues with mcp_server=True.
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        mcp_server=True,
        show_api=True,
    )
