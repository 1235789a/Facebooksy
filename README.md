# Whale Wallet Tracker — KR2 Community Index Tool

Quickly find potential customer communities/posts for manual outreach. No auto-DMs, no private data scraping.

## What it does

- Searches public web results via DuckDuckGo HTML (no API key needed)
- Targets: Facebook Groups, Reddit, X (Twitter), Telegram
- Scores relevance 1–10 based on keyword matching
- Outputs a CSV with platform, URL, score, suggested entry method, risk level
- Deduplicates URLs, caps at 50 results by default

## Install

```bash
pip install -r requirements.txt
```

If `requests` or `beautifulsoup4` are unavailable, the script falls back to **URL-only mode** — it generates DuckDuckGo search links you can click manually.

## Run

```bash
python community_index.py --limit 50 --output community_index.csv
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--limit` | 50 | Max results to output |
| `--output` | community_index.csv | Output CSV file path |
| `--fallback` | off | Force URL-only mode (no web requests) |

## CSV columns

| Column | Description |
|---|---|
| platform | Facebook Groups / Reddit / X / Telegram / Other |
| title | Result title or search query label |
| url | Direct link to the community/post |
| query_used | The search query that found this result |
| matched_keywords | Keywords that triggered the relevance score |
| estimated_relevance_score | 1–10 (higher = better target) |
| suggested_entry_method | public comment / public post / admin outreach / skip |
| risk_level | low / medium / high (scam/airdrop indicators) |
| reason | Short explanation of the score |

## How to use the CSV

1. **Open in Excel/Google Sheets/Numbers** — double-click `community_index.csv`
2. **Sort by `estimated_relevance_score` descending** — start with 8–10 scores
3. **Filter by platform** — focus on where your audience is
4. **Filter out `risk_level: high`** — skip obvious scam/airdrop groups
5. **Click URLs to verify** — open each community, check recent activity & rules
6. **Use `suggested_entry_method` as a guide**:
   - **public comment**: Reply to existing threads with value first, mention your tool naturally
   - **public post**: Write a useful post about wallet tracking / smart money, link in bio
   - **admin outreach**: DM group admin first, ask permission before posting
   - **skip**: Low relevance or high risk, don't waste time

## Scoring rules

- **8–10 (High)**: Title/snippet contains wallet tracking, smart money, whale alerts, copy trading, alpha, meme coin trading, Solana/ETH trading
- **5–7 (Medium)**: General crypto trading, altcoin, degen, signals communities
- **1–4 (Low)**: Pure news, exchange announcements, airdrop spam, obvious ad groups

## Privacy & compliance

- No login to any platform
- No member list scraping
- No private content access
- No auto-commenting or auto-DMing
- No bypassing platform rate limits
- Only collects public search result links
