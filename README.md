# Whale Wallet Tracker — Lead Radar MVP

A minimum viable lead radar for finding crypto-native small-B prospects (alpha group admins, KOLs, newsletter operators, community managers) who could benefit from smart-money whale alert tools.

**No auto-DM, no auto-comment, no spam.** Just research, scoring, and a daily Top 10 shortlist for manual outreach.

---

## What it does

1. **Searches public Reddit posts** for relevant keywords (whale tracker, smart money, on-chain alpha, etc.)
2. **Supports manual import** of X/Twitter leads via CSV (paste profiles you found manually)
3. **Scores each lead 0-10** across 5 dimensions:
   - Community identity (Telegram/Discord/group/newsletter)
   - Crypto content focus
   - Manual workflow pain (screenshots, Dexscreener, Arkham, etc.)
   - Monetization potential (VIP, premium, paid group)
   - Interaction likelihood (replies, comments, discussions)
4. **Outputs a daily Top 10** in CSV + Markdown format
5. **Suggests outreach angles** for each lead (non-spammy, value-first)

## Project structure

```
lead_radar/
  __init__.py
  __main__.py          # CLI entry point
  config.py            # keywords, scoring config
  models.py            # Lead data class
  reddit_source.py     # Reddit public search scraper
  scorer.py            # scoring engine + type guess + angle suggestion
  storage.py           # CSV / Markdown / JSON output
  manual_import.py     # manual CSV / JSON / interactive import
sample_x_leads.csv     # sample manual import file
output/                # generated reports go here (created on first run)
```

## Quick start

### 1. Run a Reddit scan

```bash
python -m lead_radar reddit
```

This will:
- Search 10 crypto subreddits for 10 keywords
- Collect unique post authors
- Enrich top profiles with bios (optional, `--no-enrich` to skip)
- Score all leads
- Output Top 10 to `output/lead_radar_YYYY-MM-DD.csv` and `.md`

### 2. Import manual X/Twitter leads

Create a CSV file (use `sample_x_leads.csv` as template) with columns:

```
name, username, platform, profile_url, source_post_url, bio, recent_post_text
```

Then run:

```bash
python -m lead_radar import --csv my_x_leads.csv
```

### 3. Run everything combined

```bash
python -m lead_radar full --manual-csv my_x_leads.csv
```

## CLI options

```
positional arguments:
  {reddit,import,full}   What to run

optional arguments:
  --top N                Number of top leads (default: 10)
  --output-dir DIR       Output directory (default: output)
  --limit-per-kw N       Posts per keyword on Reddit (default: 25)
  --no-enrich            Skip Reddit user bio fetching (faster)
  --csv FILE             CSV file for 'import' command
  --manual-csv FILE      Manual CSV for 'full' command
```

## Scoring rules (0-10)

| Dimension | Points | How to score |
|-----------|--------|--------------|
| Community identity | 0-2 | Telegram/Discord/group/community/newsletter mentions |
| Crypto content | 0-2 | Token/Solana/whale/on-chain/alpha mentions |
| Manual workflow | 0-2 | Screenshots, Dexscreener, Arkham, "need to check", etc. |
| Monetization | 0-2 | VIP, premium, paid group, collab, sponsor, newsletter |
| Interaction | 0-2 | Comments, replies, questions, discussions |

## Output files

- `output/lead_radar_YYYY-MM-DD.md` — readable report with full analysis
- `output/lead_radar_YYYY-MM-DD.csv` — spreadsheet-friendly format
- `output/all_leads_YYYY-MM-DD.json` — raw data for re-processing

## Important: what this tool does NOT do

- ❌ No auto-DM or auto-comment
- ❌ No auto-follow or auto-join
- ❌ No scraping of private data
- ❌ No bypassing platform rate limits or anti-bot measures
- ❌ No spam or mass outreach

This is a **research and scoring tool**. All outreach is manual and human-initiated.

## Customizing keywords

Edit `lead_radar/config.py` to:
- Add/remove `REDDIT_KEYWORDS`
- Add/remove `REDDIT_SUBS`
- Adjust scoring keyword lists
- Change `TOP_N` default

## Next things you might want to add

- [ ] X/Twitter API integration (with official API key)
- [ ] Telegram public channel search
- [ ] Lead deduplication across days
- [ ] Status tracking (new → reviewed → contacted → replied)
- [ ] Google Sheets export
- [ ] Daily scheduled runs
- [ ] Web dashboard
