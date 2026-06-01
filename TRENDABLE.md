# Trendable Codex Runbook

When Dylan enters `Trendable` in this Codex thread, run:

```powershell
python trendable.py
```

Return the top 15 headlines with:

- rank
- headline
- source name
- summary when available
- link
- source warnings, if any

## Current Sources

- `https://reddit-aggregator--dylanguu11.replit.app/`
- `https://news-aggregator-nu-tan.vercel.app/`
- `https://osint-aggregator--dylan2045.replit.app/`
- `https://dnu-dylan-new-york-updates--dylan2045aad.replit.app/`
- `https://ai-pulse-news--dylan2045ad.replit.app/`
- `https://attached-assets--dylanad2045.replit.app/`

## Operator Notes

- Treat partial source failures as warnings, not a full failure, when headlines still return.
- Prefer the CLI for quick local checks.
- Prefer `/api/trendable?limit=15&timeout=10` when validating the deployed API.
