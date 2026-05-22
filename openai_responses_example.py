from openai import OpenAI

client = OpenAI()

MCP_URL = "https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/"

response = client.responses.create(
    model="gpt-5.1",
    tools=[
        {
            "type": "mcp",
            "server_label": "hf-yfinance",
            "server_url": MCP_URL,
            "server_description": (
                "Yahoo Finance MCP server for stock quotes, historical data, "
                "company profiles, comparison, and financial risk snapshots."
            ),
            "require_approval": "never",
        }
    ],
    input=(
        "Use the Yahoo Finance MCP server to compare AAPL, MSFT, and NVDA. "
        "Summarize current price, PE ratio, market cap, sector, and risk."
    ),
)

print(response.output_text)
