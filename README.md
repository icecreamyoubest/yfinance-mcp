---
title: Yahoo Finance MCP Server
emoji: 📈
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 5.38.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Yahoo Finance MCP server exposed with Hugging Face Gradio MCP style.
tags:
  - mcp-server
  - gradio
  - finance
---

# Yahoo Finance MCP Server

This Space exposes Yahoo Finance tools as a Hugging Face / Gradio MCP Server.

## MCP Endpoints

After deployment, use one of these endpoints:

```txt
https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/
```

or SSE-compatible endpoint:

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

## Cursor / Windsurf / Cline MCP Config

```json
{
  "mcpServers": {
    "hf-yfinance": {
      "url": "https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/"
    }
  }
}
```

If your client expects SSE:

```json
{
  "mcpServers": {
    "hf-yfinance": {
      "url": "https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/sse"
    }
  }
}
```

If your client only supports stdio, use `mcp-remote`:

```json
{
  "mcpServers": {
    "hf-yfinance": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/sse",
        "--transport",
        "sse-only"
      ]
    }
  }
}
```

## OpenAI Responses API Example

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.1",
    tools=[
        {
            "type": "mcp",
            "server_label": "hf-yfinance",
            "server_url": "https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/",
            "server_description": "Yahoo Finance MCP server for stock quotes, historical data, company profiles, comparison, and financial risk snapshots.",
            "require_approval": "never"
        }
    ],
    input="Use the MCP server to compare AAPL, MSFT, and NVDA by current price, PE ratio, market cap, and risk."
)

print(response.output_text)
```

## Local Test

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```txt
http://localhost:7860
```

MCP endpoints:

```txt
http://localhost:7860/gradio_api/mcp/
http://localhost:7860/gradio_api/mcp/sse
```

## Disclaimer

This project is for research and demo purposes only. It is not financial advice.
