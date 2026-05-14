#!/usr/bin/env python3
"""
Trendable: scrape configured news sources and print the top 15 headline candidates.

Run:
    python trendable.py
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser


SOURCES = [
    "https://dylrit.lovable.app",
    "https://news-aggregator-nu-tan.vercel.app/",
    "https://osint-aggregator--dylan2045.replit.app/",
    "https://dnu-dylan-new-york-updates--dylan2045aad.replit.app/",
    "https://ai-pulse-news--dylan2045ad.replit.app/",
    "https://attached-assets--dylanad2045.replit.app/",
]

JSON_ENDPOINTS = {
    "https://news-aggregator-nu-tan.vercel.app/": ["data.json"],
    "https://osint-aggregator--dylan2045.replit.app/": ["api/osint/articles"],
    "https://dnu-dylan-new-york-updates--dylan2045aad.replit.app/": ["api/feeds"],
    "https://ai-pulse-news--dylan2045ad.replit.app/": ["headlines"],
    "https://attached-assets--dylanad2045.replit.app/": ["api/articles"],
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 Trendable/1.0"
)

STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "amid",
    "and",
    "are",
    "around",
    "as",
    "at",
    "back",
    "be",
    "been",
    "before",
    "being",
    "but",
    "by",
    "can",
    "could",
    "daily",
    "down",
    "for",
    "from",
    "has",
    "have",
    "headline",
    "headlines",
    "here",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "latest",
    "live",
    "more",
    "new",
    "news",
    "not",
    "of",
    "on",
    "or",
    "over",
    "read",
    "report",
    "says",
    "the",
    "their",
    "this",
    "to",
    "top",
    "update",
    "updates",
    "up",
    "via",
    "was",
    "with",
}


@dataclass(frozen=True)
class Candidate:
    text: str
    source: str
    url: str
    tag: str
    position: int
    score: float


class HeadlineParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.meta_titles: list[str] = []
        self.candidates: list[Candidate] = []
        self._tag_stack: list[tuple[str, str | None]] = []
        self._capture: list[str] = []
        self._href: str | None = None
        self._position = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        tag = tag.lower()
        if tag == "meta":
            key = (attr.get("property") or attr.get("name") or "").lower()
            content = clean_text(attr.get("content") or "")
            if key in {"og:title", "twitter:title"} and content:
                self.meta_titles.append(content)
            return

        if tag == "a":
            self._href = attr.get("href")

        if tag in {"title", "h1", "h2", "h3", "a"}:
            self._tag_stack.append((tag, self._href if tag == "a" else None))
            self._capture = []

    def handle_data(self, data: str) -> None:
        if self._tag_stack:
            self._capture.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self._tag_stack:
            if tag == "a":
                self._href = None
            return

        active_tag, href = self._tag_stack[-1]
        if tag != active_tag:
            if tag == "a":
                self._href = None
            return

        self._tag_stack.pop()
        text = clean_text(" ".join(self._capture))
        self._capture = []

        if tag == "title":
            self.title = text
        elif looks_like_headline(text):
            self._position += 1
            url = urllib.parse.urljoin(self.base_url, href or "")
            self.candidates.append(
                Candidate(
                    text=text,
                    source=self.base_url,
                    url=url,
                    tag=tag,
                    position=self._position,
                    score=base_score(tag, self._position),
                )
            )

        if tag == "a":
            self._href = None


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n-|•")


def looks_like_headline(text: str) -> bool:
    if not text:
        return False
    if len(text) < 18 or len(text) > 180:
        return False
    if len(text.split()) < 4:
        return False
    lower = text.lower()
    noisy = (
        "javascript",
        "subscribe",
        "sign in",
        "privacy policy",
        "terms of service",
        "cookie",
        "read more",
        "view all",
    )
    return not any(term in lower for term in noisy)


def base_score(tag: str, position: int) -> float:
    weights = {"h1": 18.0, "h2": 14.0, "h3": 10.0, "a": 7.0}
    return weights.get(tag, 4.0) + max(0.0, 8.0 - min(position, 16) * 0.35)


def fetch_source(url: str, timeout: float) -> tuple[str, list[Candidate], str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        return url, [], str(exc)

    parser = HeadlineParser(url)
    parser.feed(body)

    candidates = list(parser.candidates)
    for title in parser.meta_titles + ([parser.title] if parser.title else []):
        if looks_like_headline(title):
            candidates.append(
                Candidate(
                    text=title,
                    source=url,
                    url=url,
                    tag="title",
                    position=0,
                    score=16.0,
                )
            )

    for endpoint in JSON_ENDPOINTS.get(url, []):
        endpoint_url = urllib.parse.urljoin(url, endpoint)
        json_candidates, error = fetch_json_candidates(url, endpoint_url, timeout)
        if error:
            return url, candidates, error
        candidates.extend(json_candidates)

    return url, candidates, None


def fetch_json_candidates(source: str, endpoint_url: str, timeout: float) -> tuple[list[Candidate], str | None]:
    request = urllib.request.Request(
        endpoint_url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read().decode(charset, errors="replace")
            data = json.loads(payload)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as exc:
        return [], f"{endpoint_url}: {exc}"

    candidates: list[Candidate] = []
    for position, item in enumerate(iter_news_items(data), 1):
        title = extract_title(item)
        if not looks_like_headline(title):
            continue
        link = extract_link(item) or endpoint_url
        score = 24.0 + max(0.0, 12.0 - min(position, 30) * 0.25)
        if item.get("hot") is True:
            score += 6.0
        if item.get("ai_match") is True:
            score += 4.0
        candidates.append(
            Candidate(
                text=title,
                source=source,
                url=urllib.parse.urljoin(source, link),
                tag="json",
                position=position,
                score=score,
            )
        )

    return candidates, None


def iter_news_items(value: object):
    if isinstance(value, list):
        for item in value:
            yield from iter_news_items(item)
        return

    if not isinstance(value, dict):
        return

    if extract_title(value):
        yield value

    for key, child in value.items():
        if key in {"items", "articles", "sources", "polymarket", "economics", "companies", "tech"}:
            yield from iter_news_items(child)
        elif isinstance(child, (list, dict)) and key not in {"outcomes"}:
            yield from iter_news_items(child)


def extract_title(item: dict) -> str:
    for key in ("title", "headline", "question", "name"):
        value = clean_text(str(item.get(key) or ""))
        if value:
            return value
    return ""


def extract_link(item: dict) -> str:
    for key in ("url", "link", "href"):
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return ""


def norm_key(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]+", "", text.lower())
    words = [word for word in text.split() if word not in STOPWORDS]
    return " ".join(words[:14])


def tokens(text: str) -> list[str]:
    return [
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())
        if word not in STOPWORDS
    ]


def rank(candidates: list[Candidate], limit: int) -> list[Candidate]:
    keyword_counts = Counter()
    source_counts: dict[str, set[str]] = {}
    for candidate in candidates:
        unique = set(tokens(candidate.text))
        keyword_counts.update(unique)
        for word in unique:
            source_counts.setdefault(word, set()).add(candidate.source)

    best_by_key: dict[str, Candidate] = {}
    for candidate in candidates:
        key = norm_key(candidate.text)
        if not key:
            continue

        trend_score = sum(keyword_counts[word] for word in set(tokens(candidate.text)))
        cross_source_score = sum(len(source_counts.get(word, set())) for word in set(tokens(candidate.text)))
        score = candidate.score + trend_score * 0.35 + cross_source_score * 0.55
        scored = Candidate(
            text=candidate.text,
            source=candidate.source,
            url=candidate.url,
            tag=candidate.tag,
            position=candidate.position,
            score=score,
        )

        existing = best_by_key.get(key)
        if existing is None or scored.score > existing.score:
            best_by_key[key] = scored

    return sorted(best_by_key.values(), key=lambda item: item.score, reverse=True)[:limit]


def trendable(limit: int, timeout: float) -> tuple[list[Candidate], list[tuple[str, str]]]:
    errors: list[tuple[str, str]] = []
    all_candidates: list[Candidate] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
        futures = [executor.submit(fetch_source, source, timeout) for source in SOURCES]
        for future in concurrent.futures.as_completed(futures):
            source, candidates, error = future.result()
            if error:
                errors.append((source, error))
            all_candidates.extend(candidates)

    return rank(all_candidates, limit), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Trendable headline scraper.")
    parser.add_argument("--limit", type=int, default=15, help="number of headlines to print")
    parser.add_argument("--timeout", type=float, default=15.0, help="seconds to wait per source")
    args = parser.parse_args()

    started = time.time()
    headlines, errors = trendable(args.limit, args.timeout)

    print(f"Trendable top {len(headlines)} headlines")
    print(f"Sources: {len(SOURCES)} | Completed in {time.time() - started:.1f}s")
    print()

    if not headlines:
        print("No headline candidates were found.")
    for index, item in enumerate(headlines, 1):
        host = urllib.parse.urlparse(item.source).netloc
        print(f"{index:>2}. {item.text}")
        print(f"    Source: {host}")
        if item.url and item.url != item.source:
            print(f"    Link: {item.url}")

    if errors:
        print()
        print("Source warnings:", file=sys.stderr)
        for source, error in errors:
            print(f"- {source}: {error}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
