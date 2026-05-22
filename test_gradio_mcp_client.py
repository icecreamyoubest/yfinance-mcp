import asyncio
import sys
from fastmcp import Client


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_gradio_mcp_client.py https://<user>-<space>.hf.space/gradio_api/mcp/")
        print("  python test_gradio_mcp_client.py https://<user>-<space>.hf.space/gradio_api/mcp/sse")
        sys.exit(1)

    server_url = sys.argv[1]
    print(f"Connecting to MCP server: {server_url}")

    async with Client(server_url) as client:
        print("\nListing tools...")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        print("\nCalling health_check...")
        print(await client.call_tool("health_check", {}))

        print("\nCalling get_stock_quote...")
        print(await client.call_tool("get_stock_quote", {"ticker": "NVDA"}))

        print("\nCalling compare_stocks...")
        # Gradio MCP exposes compare_stocks with a CSV string input.
        print(await client.call_tool("compare_stocks", {"tickers_csv": "AAPL,MSFT,NVDA"}))


if __name__ == "__main__":
    asyncio.run(main())
