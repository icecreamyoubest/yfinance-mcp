# Runbook: Hugging Face Gradio MCP Style Deployment

## 1. Create Space

- SDK: Gradio
- Visibility: Public, if OpenAI or external MCP clients need to call it
- Upload:
  - app.py
  - requirements.txt
  - README.md
  - test_gradio_mcp_client.py
  - openai_responses_example.py
  - mcp_config_streamable_http.example.json
  - mcp_config_stdio_bridge.example.json

## 2. Expected Endpoint

```txt
https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/
https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/sse
```

## 3. Important Difference vs Pure FastMCP Docker

Pure FastMCP Docker endpoint:

```txt
/mcp
```

Hugging Face / Gradio MCP endpoint:

```txt
/gradio_api/mcp/
/gradio_api/mcp/sse
```

## 4. Local Test

```bash
pip install -r requirements.txt
python app.py
```

Then:

```bash
python test_gradio_mcp_client.py http://localhost:7860/gradio_api/mcp/
```

or:

```bash
python test_gradio_mcp_client.py http://localhost:7860/gradio_api/mcp/sse
```

## 5. Client Config

For clients supporting URL MCP server:

```json
{
  "mcpServers": {
    "hf-yfinance": {
      "url": "https://<your-username>-<your-space-name>.hf.space/gradio_api/mcp/"
    }
  }
}
```

For clients that only support stdio:

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
