"""
Simple remote MCP smoke test for a Hugging Face Gradio MCP Space.

Usage:
  python test_gradio_mcp_client.py https://<user>-<space>.hf.space/gradio_api/mcp/

If your client requires SSE:
  python test_gradio_mcp_client.py https://<user>-<space>.hf.space/gradio_api/mcp/sse
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from fastmcp import Client


def _print_result(name: str, result: Any) -> None:
    print(f"\n=== {name} ===")
    print(result)


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_gradio_mcp_client.py https://<user>-<space>.hf.space/gradio_api/mcp/")
        sys.exit(1)

    server_url = sys.argv[1]
    print(f"Connecting to MCP server: {server_url}")

    async with Client(server_url) as client:
        tools = await client.list_tools()
        print("\nTools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        _print_result("health_check", await client.call_tool("health_check", {}))
        _print_result("get_stock_quote", await client.call_tool("get_stock_quote", {"ticker": "NVDA"}))
        _print_result("compare_stocks", await client.call_tool("compare_stocks", {"tickers": "AAPL,MSFT,NVDA"}))


if __name__ == "__main__":
    asyncio.run(main())
