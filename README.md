---
title: Yahoo Finance MCP Server
emoji: 📈
colorFrom: blue
colorTo: gray
sdk: gradio
app_file: app.py
short_description: Yahoo Finance MCP stock tools
tags:
  - mcp-server
  - gradio
  - finance
  - stocks
license: apache-2.0
---

# Yahoo Finance MCP Server

A Hugging Face Spaces Gradio MCP server for Yahoo Finance stock tools.

## MCP Endpoint

```txt
https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/
```

SSE endpoint:

```txt
https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/sse
```

## Tools

- `health_check`
- `get_stock_quote`
- `get_company_profile`
- `get_stock_history`
- `compare_stocks`
- `get_financial_risk_snapshot`

## Example Prompts

```txt
Query NVDA current price, PE ratio, market cap, and business summary.
```

```txt
Compare AAPL, MSFT, and NVDA by valuation and market cap.
```

```txt
Get a financial risk snapshot for TSLA.
```

## Disclaimer

This project is for research and demo purposes only. It is not financial advice.
