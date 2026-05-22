# GitHub to Hugging Face Spaces Sync Setup

This repository includes a GitHub Actions workflow that syncs the minimal Hugging Face Space runtime files to your Space:

- `app.py`
- `requirements.txt`
- `README.md`

## Required GitHub Actions settings

Go to:

```txt
GitHub Repository → Settings → Secrets and variables → Actions
```

### Secret

```txt
HF_TOKEN=<your Hugging Face write token>
```

### Variable or Secret

```txt
HF_SPACE_REPO=<hf-username>/<space-name>
```

Example:

```txt
HF_SPACE_REPO=corinna/yfinance-mcp-service
```

Do not use the full URL. Use only `username/space-name`.

## Hugging Face Space settings

Create the Space as:

```txt
SDK: Gradio
Visibility: Public, if OpenAI or other public clients need to call it
```

The Space README metadata already uses:

```yaml
sdk: gradio
app_file: app.py
short_description: Yahoo Finance MCP stock tools
```

The `short_description` is intentionally less than 60 characters to satisfy Hugging Face metadata validation.

## MCP endpoint

After successful deployment:

```txt
https://<user>-<space>.hf.space/gradio_api/mcp/
```

SSE endpoint:

```txt
https://<user>-<space>.hf.space/gradio_api/mcp/sse
```
