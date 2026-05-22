"""
OpenAI Responses API example for remote MCP.

Before running:
  export OPENAI_API_KEY=...

Then edit SERVER_URL to your deployed Hugging Face Space MCP endpoint.
"""

from openai import OpenAI

SERVER_URL = "https://yourusername-yfinance-mcp-service.hf.space/gradio_api/mcp/"

client = OpenAI()

response = client.responses.create(
    model="gpt-5.1",
    tools=[
        {
            "type": "mcp",
            "server_label": "hf-yahoo-finance",
            "server_url": SERVER_URL,
            "server_description": "Yahoo Finance MCP server for stock data.",
            "require_approval": "never",
        }
    ],
    input=(
        "Use the Yahoo Finance MCP server to compare AAPL, MSFT, and NVDA. "
        "Summarize current price, market cap, PE, beta, and risk factors."
    ),
)

print(response.output_text)
