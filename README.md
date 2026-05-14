# Trendable

Trendable scrapes Dylan's configured sources and returns the top 15 ranked headlines.

## Local CLI

```powershell
python trendable.py
```

## Vercel

Deploy this folder to Vercel. The project has:

- `/` - a static headline dashboard
- `/api/trendable` - a Python serverless API endpoint

The API supports optional query parameters:

```text
/api/trendable?limit=15&timeout=10
```

No Python dependencies are required.
