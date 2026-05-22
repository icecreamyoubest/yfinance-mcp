# Runbook

## Local run

```bash
pip install -r requirements.txt
python app.py
```

Open:

```txt
http://localhost:7860
```

MCP endpoint:

```txt
http://localhost:7860/gradio_api/mcp/
```

## Remote test

```bash
pip install fastmcp
python test_gradio_mcp_client.py https://<user>-<space>.hf.space/gradio_api/mcp/
```

## Common errors

### `unexpected keyword argument 'mcp_server'`

Your Gradio version is too old or MCP extra is missing. Ensure:

```txt
gradio[mcp]>=5.49.0
```

### Hugging Face push rejected: `short_description` too long

Keep `README.md` frontmatter `short_description` at 60 characters or less.

### MCP discovery timeout

Try both endpoints:

```txt
/gradio_api/mcp/
/gradio_api/mcp/sse
```

Some clients require the SSE path.
