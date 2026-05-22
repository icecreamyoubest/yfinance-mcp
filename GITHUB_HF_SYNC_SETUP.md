# GitHub → Hugging Face Spaces Sync Setup

This repository contains a Gradio-style MCP server for Hugging Face Spaces.

## 1. Create a Hugging Face Space

Create a new Hugging Face Space with:

- SDK: Gradio
- Visibility: Public, if you want OpenAI / Dify / LangChain to access it remotely
- Example Space repo id: `your-hf-username/yfinance-mcp-service`

The MCP endpoint will be:

```txt
https://<your-hf-username>-<your-space-name>.hf.space/gradio_api/mcp/
```

SSE endpoint:

```txt
https://<your-hf-username>-<your-space-name>.hf.space/gradio_api/mcp/sse
```

## 2. Add GitHub Secret

In GitHub repository:

```txt
Settings → Secrets and variables → Actions → Secrets → New repository secret
```

Add:

```txt
HF_TOKEN=<your Hugging Face write token>
```

The token must have write permission to the target Hugging Face Space.

## 3. Add GitHub Variable

In GitHub repository:

```txt
Settings → Secrets and variables → Actions → Variables → New repository variable
```

Add:

```txt
HF_SPACE_REPO=your-hf-username/yfinance-mcp-service
```

## 4. Trigger Sync

Push to `main`, or manually trigger:

```txt
Actions → Sync to Hugging Face Space → Run workflow
```

## 5. Verify MCP Endpoint

```bash
python test_gradio_mcp_client.py https://<your-hf-username>-<your-space-name>.hf.space/gradio_api/mcp/
```

If your client requires SSE:

```bash
python test_gradio_mcp_client.py https://<your-hf-username>-<your-space-name>.hf.space/gradio_api/mcp/sse
```
