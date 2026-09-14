# ITVedas Brain

Autonomous content generation and intelligence engine for ITVedas.com.

Powered by **Google Gemini** (`gemini-2.5-flash`) via standard library `urllib.request` (zero external dependencies).

## Architecture & Components

- `core/llm.py` - Core Google Gemini API client with retry and code fence stripping
- `gemini_client.py` - Lightweight Gemini helper utility
- `content-writer.py` - Long-form technical curriculum and guide generator
- `news-agent.py` - RSS ingestion and tech/security news intelligence generator
- `state/` - Pipeline memory, publishing history, and deduplication state

## Configuration

Set `GEMINI_API_KEY` in your environment or repository secrets:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GEMINI_MODEL="gemini-2.5-flash"
```
