"""Main CLI entry point for Lead Radar.

Usage:
    python -m lead_radar reddit                # scrape & score Reddit
    python -m lead_radar import --csv FILE     # import manual CSV & score
    python -m lead_radar interactive           # interactive manual import
    python -m lead_radar full                  # Reddit + manual (if file exists)
"""

import argparse
import os
import sys

from .config import (
    REDDIT_KEYWORDS,
    REDDIT_SUBS,
    TOP_N,
    OUTPUT_DIR,
)
from .reddit_source import search_reddit, enrich_reddit_leads
from .scorer import score_and_filter_leads
from .storage import export_csv, export_markdown, save_all_leads_json
from .manual_import import parse_manual_csv


def run_reddit(top_n: int = TOP_N, output_dir: str = OUTPUT_DIR,
               limit_per_kw: int = 25, enrich: bool = True,
               proxy: str = None) -> list:
    """Run the full Reddit pipeline."""
    print("\n" + "=" * 60)
    print("  Lead Radar MVP — Reddit Scan")
    print("=" * 60 + "\n")

    print(f"Keywords: {len(REDDIT_KEYWORDS)} across {len(REDDIT_SUBS)} subs")
    print(f"Limit per keyword: {limit_per_kw} posts")
    if proxy:
        print(f"Proxy: {proxy}")
    print()

    leads = search_reddit(
        keywords=REDDIT_KEYWORDS,
        subreddits=REDDIT_SUBS,
        limit_per_keyword=limit_per_kw,
        proxy=proxy,
    )

    if not leads:
        print("\nNo leads found. Check network or try different keywords.")
        return []

    if enrich:
        print(f"\nEnriching top user profiles (fetching bios)...")
        leads = enrich_reddit_leads(leads, max_users=min(50, len(leads)),
                                    proxy=proxy)

    print(f"\nScoring and filtering {len(leads)} leads...")
    top_leads = score_and_filter_leads(leads, top_n=top_n)

    if not top_leads:
        print("\nNo leads passed scoring threshold.")
        return []

    csv_path = export_csv(top_leads, output_dir)
    md_path = export_markdown(top_leads, output_dir)
    json_path = save_all_leads_json(leads, output_dir)

    print("\n" + "=" * 60)
    print(f"  Top {len(top_leads)} Leads")
    print("=" * 60 + "\n")

    for i, lead in enumerate(top_leads, 1):
        print(f"  #{i}  {lead.score:>4}/10  {lead.platform:8s}  u/{lead.username}")
        print(f"       {lead.type_guess}")
        print(f"       {lead.profile_url}")
        print()

    print(f"  CSV output:  {csv_path}")
    print(f"  Markdown:    {md_path}")
    print(f"  Full JSON:   {json_path}")
    print()

    return top_leads


def run_import(csv_file: str, top_n: int = TOP_N,
               output_dir: str = OUTPUT_DIR) -> list:
    """Import leads from CSV and score them."""
    print(f"\nImporting leads from: {csv_file}")
    if not os.path.exists(csv_file):
        print(f"  Error: file not found: {csv_file}")
        return []

    leads = parse_manual_csv(csv_file)
    print(f"  Imported {len(leads)} leads")

    if not leads:
        return []

    print(f"  Scoring...")
    top_leads = score_and_filter_leads(leads, top_n=top_n)

    csv_path = export_csv(top_leads, output_dir)
    md_path = export_markdown(top_leads, output_dir)

    print(f"\n  Top {len(top_leads)} from import:")
    for i, lead in enumerate(top_leads, 1):
        print(f"  #{i}  {lead.score:>4}/10  {lead.platform:8s}  {lead.username}")

    print(f"\n  CSV output:  {csv_path}")
    print(f"  Markdown:    {md_path}\n")

    return top_leads


def main():
    parser = argparse.ArgumentParser(
        description="Whale Wallet Tracker — Lead Radar MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m lead_radar reddit
  python -m lead_radar reddit --top 20
  python -m lead_radar import --csv my_leads.csv
  python -m lead_radar full --manual-csv x_leads.csv
        """,
    )
    parser.add_argument("command", choices=["reddit", "import", "full"],
                        help="What to run")
    parser.add_argument("--top", type=int, default=TOP_N,
                        help=f"Number of top leads to output (default: {TOP_N})")
    parser.add_argument("--output-dir", default=OUTPUT_DIR,
                        help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("--limit-per-kw", type=int, default=25,
                        help="Posts per keyword on Reddit (default: 25)")
    parser.add_argument("--no-enrich", action="store_true",
                        help="Skip fetching user bios on Reddit (faster)")
    parser.add_argument("--csv", dest="csv_file", default="",
                        help="CSV file for import command")
    parser.add_argument("--manual-csv", default="",
                        help="Additional manual CSV for 'full' command")
    parser.add_argument("--proxy", default=None,
                        help="HTTP/SOCKS proxy, e.g. http://127.0.0.1:7890")

    args = parser.parse_args()

    if args.command == "reddit":
        run_reddit(
            top_n=args.top,
            output_dir=args.output_dir,
            limit_per_kw=args.limit_per_kw,
            enrich=not args.no_enrich,
            proxy=args.proxy,
        )
    elif args.command == "import":
        if not args.csv_file:
            print("Error: --csv required for import command")
            sys.exit(1)
        run_import(args.csv_file, top_n=args.top, output_dir=args.output_dir)
    elif args.command == "full":
        all_leads = []
        reddit_leads = run_reddit(
            top_n=args.top,
            output_dir=args.output_dir,
            limit_per_kw=args.limit_per_kw,
            enrich=not args.no_enrich,
            proxy=args.proxy,
        )
        all_leads.extend(reddit_leads)

        if args.manual_csv and os.path.exists(args.manual_csv):
            manual_leads = run_import(
                args.manual_csv, top_n=args.top, output_dir=args.output_dir
            )
            all_leads.extend(manual_leads)

        if all_leads:
            from .scorer import score_and_filter_leads as saf
            combined = saf(all_leads, top_n=args.top)
            md_path = export_markdown(combined, args.output_dir)
            print(f"  Combined Top {args.top} Markdown: {md_path}")


if __name__ == "__main__":
    main()
