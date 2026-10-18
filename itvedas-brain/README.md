# ITVedas Brain

Autonomous content generation and intelligence engine for ITVedas.com.

Powered by the **Claude API** (`claude-opus-5-5`) via the official `anthropic` Python SDK (pinned in `requirements.txt`).

## Architecture & Components

- `core/llm.py` - Claude API helper: one `claude()` call used by every script, with refusal fallback and JSON-schema replies for reviews
- `content-writer.py` - Long-form technical curriculum and guide generator
- `news-agent.py` - RSS ingestion and tech/security news intelligence generator
- `state/` - Pipeline memory, publishing history, and deduplication state

## Configuration

Set `ANTHROPIC_API_KEY` in your environment or repository secrets:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export CLAUDE_MODEL="claude-opus-5-5"   # optional
```
