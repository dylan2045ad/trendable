# Trendable

Trendable is a lightweight headline intelligence tool for ranking what is worth paying attention to across Dylan's news and signal sources.

It runs as both a local CLI and a Vercel-ready dashboard/API. The scraper collects headline candidates from configured source dashboards, JSON endpoints, and page metadata, then scores them for recency, source placement, keyword overlap, cross-source momentum, and available article context.

## Highlights

- Pulls from multiple configured dashboards and news endpoints.
- Extracts headlines from HTML, metadata, and JSON payloads.
- Deduplicates near-matching stories before ranking.
- Enriches strong candidates with summaries and images when available.
- Ships as a zero-dependency Python script plus a Vercel serverless endpoint.
- Includes a static front end for quickly scanning the ranked list.

## Stack

| Layer | Technology |
| --- | --- |
| Scraper | Python standard library |
| Ranking | Keyword frequency, cross-source overlap, source-position weighting |
| API | Vercel Python serverless function |
| UI | Static HTML, CSS, JavaScript |
| Deploy | Vercel |

## How It Works

```text
Configured sources
    -> HTML + JSON extraction
    -> headline cleanup
    -> scoring + deduplication
    -> metadata enrichment
    -> CLI output or `/api/trendable`
```

The ranking model intentionally stays transparent. Every result carries source, score inputs, summary, image URL when found, and a direct link when available.

## Local CLI

```powershell
python trendable.py
```

Optional arguments:

```powershell
python trendable.py --limit 20 --timeout 12
```

## API

```http
GET /api/trendable?limit=15&timeout=10
```

Parameters:

| Name | Default | Range | Purpose |
| --- | ---: | ---: | --- |
| `limit` | `15` | `1-50` | Number of ranked headlines to return |
| `timeout` | `10` | `2-20` | Seconds to wait per source |

Example response shape:

```json
{
  "triggerword": "Trendable",
  "count": 15,
  "sourceCount": 6,
  "durationSeconds": 3.42,
  "headlines": [
    {
      "text": "Example headline",
      "source": "https://example.com/",
      "url": "https://example.com/story",
      "tag": "json",
      "position": 1,
      "score": 42.5,
      "summary": "Short story summary",
      "image_url": "https://example.com/image.jpg"
    }
  ],
  "errors": []
}
```

## Vercel Deploy

Deploy the repository to Vercel. The project exposes:

- `/` - static dashboard
- `/api/trendable` - Python serverless API endpoint

No Python package installation is required; the scraper uses the standard library.

## Repository Map

| Path | Purpose |
| --- | --- |
| `trendable.py` | Scraper, ranking logic, CLI |
| `api/trendable.py` | Vercel serverless API wrapper |
| `public/index.html` | Production dashboard |
| `index.html` | Local/static dashboard copy |
| `TRENDABLE.md` | Codex triggerword runbook |
| `vercel.json` | Vercel routing |

## Roadmap

- Add source health snapshots and latency telemetry.
- Add persisted trend history for "rising" vs. "already saturated" stories.
- Add screenshot examples to the README after a stable deployment pass.
- Add unit tests for JSON extraction, deduplication, and score weighting.

## Design Principle

Trendable favors explainable ranking over opaque virality claims. It is built to help a human operator scan faster, spot overlap earlier, and turn raw headline flow into better editorial judgment.
