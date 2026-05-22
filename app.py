import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import gradio as gr
import yfinance as yf


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("yfinance-mcp-gradio")


def _json(data: Dict[str, Any] | List[Any]) -> str:
    """Return pretty JSON string."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _normalize_ticker(ticker: str) -> str:
    if not ticker:
        return ""
    return ticker.strip().upper()


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        value = float(value)
        if value != value:
            return None
        return value
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _get_info(ticker: str) -> Dict[str, Any]:
    stock = yf.Ticker(ticker)
    return stock.info or {}


def health_check() -> str:
    """
    Check whether the Yahoo Finance MCP server is running.

    Returns:
        A JSON string containing service status, timestamp, transport style, and Hugging Face MCP endpoint hints.
    """
    return _json(
        {
            "ok": True,
            "service": "Yahoo Finance MCP Server on Hugging Face Spaces",
            "runtime": "gradio",
            "mcp_style": "huggingface-gradio-mcp",
            "mcp_endpoints": [
                "/gradio_api/mcp/",
                "/gradio_api/mcp/sse",
            ],
            "timestamp": int(time.time()),
        }
    )


def get_stock_quote(ticker: str) -> str:
    """
    Get the latest available stock quote and basic company financial metrics.

    Args:
        ticker: Stock ticker symbol, for example AAPL, NVDA, MSFT, TSLA, or 0700.HK.

    Returns:
        A JSON string containing latest available price, daily range, market cap, PE ratio, sector, industry, and business summary.
    """
    ticker = _normalize_ticker(ticker)

    if not ticker:
        return _json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        info = _get_info(ticker)

        if not info:
            return _json(
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

        result = {
            "ok": True,
            "ticker": ticker,
            "company_name": info.get("longName") or info.get("shortName") or "unknown",
            "exchange": info.get("exchange") or "unknown",
            "quote_type": info.get("quoteType") or "unknown",
            "currency": currency,
            "current_price": _safe_float(current_price),
            "previous_close": _safe_float(info.get("previousClose")),
            "open": _safe_float(info.get("open")),
            "day_high": _safe_float(info.get("dayHigh")),
            "day_low": _safe_float(info.get("dayLow")),
            "fifty_two_week_high": _safe_float(info.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": _safe_float(info.get("fiftyTwoWeekLow")),
            "market_cap": _safe_int(info.get("marketCap")),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_book": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "sector": info.get("sector") or "unknown",
            "industry": info.get("industry") or "unknown",
            "website": info.get("website") or "unknown",
            "business_summary": (info.get("longBusinessSummary") or "")[:900],
            "data_source": "Yahoo Finance via yfinance",
            "disclaimer": "Market data may be delayed or incomplete. This is not financial advice.",
        }

        return _json(result)

    except Exception as exc:
        logger.exception("get_stock_quote failed for ticker=%s", ticker)
        return _json(
            {
                "ok": False,
                "ticker": ticker,
                "error": str(exc),
                "hint": "Check ticker format, for example AAPL, NVDA, MSFT, or 0700.HK.",
            }
        )


def get_company_profile(ticker: str) -> str:
    """
    Get company profile, business summary, sector, industry, country, website, and employee count.

    Args:
        ticker: Stock ticker symbol, for example AAPL, NVDA, MSFT, TSLA, or 0700.HK.

    Returns:
        A JSON string containing company profile and business description.
    """
    ticker = _normalize_ticker(ticker)

    if not ticker:
        return _json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        info = _get_info(ticker)

        result = {
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

        return _json(result)

    except Exception as exc:
        logger.exception("get_company_profile failed for ticker=%s", ticker)
        return _json({"ok": False, "ticker": ticker, "error": str(exc)})


def get_stock_history(ticker: str, period: str = "5d", interval: str = "1d", limit: int = 20) -> str:
    """
    Get recent historical OHLCV market data.

    Args:
        ticker: Stock ticker symbol, for example AAPL, NVDA, MSFT, TSLA, or 0700.HK.
        period: Data period, for example 1d, 5d, 1mo, 3mo, 6mo, 1y, or 5y.
        interval: Data interval, for example 1m, 5m, 15m, 1h, 1d, or 1wk.
        limit: Maximum number of rows to return. The value is capped at 100.

    Returns:
        A JSON string containing historical OHLCV rows.
    """
    ticker = _normalize_ticker(ticker)
    if not ticker:
        return _json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        limit = max(1, min(int(limit), 100))
    except Exception:
        limit = 20

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return _json(
                {
                    "ok": False,
                    "ticker": ticker,
                    "period": period,
                    "interval": interval,
                    "error": "No historical data returned.",
                }
            )

        rows = []
        for idx, row in hist.tail(limit).iterrows():
            rows.append(
                {
                    "datetime": str(idx),
                    "open": _safe_float(row.get("Open")),
                    "high": _safe_float(row.get("High")),
                    "low": _safe_float(row.get("Low")),
                    "close": _safe_float(row.get("Close")),
                    "volume": _safe_int(row.get("Volume")),
                }
            )

        return _json(
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
        return _json(
            {
                "ok": False,
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "error": str(exc),
            }
        )


def compare_stocks(tickers_csv: str) -> str:
    """
    Compare multiple stocks by price, market cap, PE ratio, sector, industry, and beta.

    Args:
        tickers_csv: Comma-separated stock tickers, for example AAPL,MSFT,NVDA.

    Returns:
        A JSON string containing a comparison table for the requested tickers.
    """
    if not tickers_csv:
        return _json({"ok": False, "error": "tickers_csv is required", "example": "AAPL,MSFT,NVDA"})

    tickers = [_normalize_ticker(t) for t in tickers_csv.split(",") if _normalize_ticker(t)]
    tickers = tickers[:10]

    if not tickers:
        return _json({"ok": False, "error": "No valid tickers provided."})

    results = []

    for ticker in tickers:
        try:
            info = _get_info(ticker)
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
                    "currency": info.get("currency") or "USD",
                    "current_price": _safe_float(current_price),
                    "market_cap": _safe_int(info.get("marketCap")),
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "price_to_book": info.get("priceToBook"),
                    "beta": info.get("beta"),
                    "sector": info.get("sector") or "unknown",
                    "industry": info.get("industry") or "unknown",
                }
            )
        except Exception as exc:
            logger.exception("compare_stocks failed for ticker=%s", ticker)
            results.append({"ok": False, "ticker": ticker, "error": str(exc)})

    return _json(
        {
            "ok": True,
            "tickers": tickers,
            "results": results,
            "data_source": "Yahoo Finance via yfinance",
            "disclaimer": "Market data may be delayed or incomplete. This is not financial advice.",
        }
    )


def get_financial_risk_snapshot(ticker: str) -> str:
    """
    Generate a basic financial risk snapshot using valuation, leverage, liquidity, profitability, growth, and volatility indicators.

    Args:
        ticker: Stock ticker symbol, for example AAPL, NVDA, MSFT, TSLA, or 0700.HK.

    Returns:
        A JSON string containing risk indicators and simple rule-based risk flags.
    """
    ticker = _normalize_ticker(ticker)
    if not ticker:
        return _json({"ok": False, "error": "ticker is required", "example": "AAPL"})

    try:
        info = _get_info(ticker)

        beta = _safe_float(info.get("beta"))
        trailing_pe = _safe_float(info.get("trailingPE"))
        forward_pe = _safe_float(info.get("forwardPE"))
        debt_to_equity = _safe_float(info.get("debtToEquity"))
        profit_margins = _safe_float(info.get("profitMargins"))
        operating_margins = _safe_float(info.get("operatingMargins"))
        current_ratio = _safe_float(info.get("currentRatio"))
        quick_ratio = _safe_float(info.get("quickRatio"))
        revenue_growth = _safe_float(info.get("revenueGrowth"))
        earnings_growth = _safe_float(info.get("earningsGrowth"))

        risk_flags = []

        if beta is not None and beta > 1.5:
            risk_flags.append("High beta: the stock may be more volatile than the broader market.")
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
            risk_flags.append("No major risk flags detected from the available Yahoo Finance indicators.")

        return _json(
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
                "disclaimer": "This is not financial advice. It is a simple data-driven risk snapshot.",
            }
        )

    except Exception as exc:
        logger.exception("get_financial_risk_snapshot failed for ticker=%s", ticker)
        return _json({"ok": False, "ticker": ticker, "error": str(exc)})


with gr.Blocks(
    title="Yahoo Finance MCP Server",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(
        """
# Yahoo Finance MCP Server

This Hugging Face Space exposes Yahoo Finance tools as a **Gradio MCP Server**.

MCP endpoints after deployment:

```text
https://<user>-<space>.hf.space/gradio_api/mcp/
https://<user>-<space>.hf.space/gradio_api/mcp/sse
```

Use the tabs below for manual UI testing. MCP clients can discover and call the same tools.
"""
    )

    with gr.Tab("Health Check"):
        health_output = gr.Code(label="Result", language="json")
        health_btn = gr.Button("Run health_check")
        health_btn.click(
            fn=health_check,
            inputs=[],
            outputs=health_output,
            api_name="health_check",
        )

    with gr.Tab("Stock Quote"):
        quote_ticker = gr.Textbox(label="Ticker", value="NVDA", placeholder="AAPL, NVDA, MSFT, 0700.HK")
        quote_output = gr.Code(label="Result", language="json")
        quote_btn = gr.Button("Run get_stock_quote")
        quote_btn.click(
            fn=get_stock_quote,
            inputs=quote_ticker,
            outputs=quote_output,
            api_name="get_stock_quote",
        )

    with gr.Tab("Company Profile"):
        profile_ticker = gr.Textbox(label="Ticker", value="AAPL")
        profile_output = gr.Code(label="Result", language="json")
        profile_btn = gr.Button("Run get_company_profile")
        profile_btn.click(
            fn=get_company_profile,
            inputs=profile_ticker,
            outputs=profile_output,
            api_name="get_company_profile",
        )

    with gr.Tab("Stock History"):
        history_ticker = gr.Textbox(label="Ticker", value="AAPL")
        history_period = gr.Textbox(label="Period", value="5d")
        history_interval = gr.Textbox(label="Interval", value="1d")
        history_limit = gr.Number(label="Limit", value=20, precision=0)
        history_output = gr.Code(label="Result", language="json")
        history_btn = gr.Button("Run get_stock_history")
        history_btn.click(
            fn=get_stock_history,
            inputs=[history_ticker, history_period, history_interval, history_limit],
            outputs=history_output,
            api_name="get_stock_history",
        )

    with gr.Tab("Compare Stocks"):
        compare_input = gr.Textbox(label="Tickers CSV", value="AAPL,MSFT,NVDA")
        compare_output = gr.Code(label="Result", language="json")
        compare_btn = gr.Button("Run compare_stocks")
        compare_btn.click(
            fn=compare_stocks,
            inputs=compare_input,
            outputs=compare_output,
            api_name="compare_stocks",
        )

    with gr.Tab("Risk Snapshot"):
        risk_ticker = gr.Textbox(label="Ticker", value="TSLA")
        risk_output = gr.Code(label="Result", language="json")
        risk_btn = gr.Button("Run get_financial_risk_snapshot")
        risk_btn.click(
            fn=get_financial_risk_snapshot,
            inputs=risk_ticker,
            outputs=risk_output,
            api_name="get_financial_risk_snapshot",
        )


if __name__ == "__main__":
    # HF Gradio Spaces normally manages server name and port automatically.
    # These env vars make the same app runnable locally or in Docker as well.
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))

    demo.queue().launch(
        server_name=server_name,
        server_port=server_port,
        mcp_server=True,
        show_api=True,
    )
