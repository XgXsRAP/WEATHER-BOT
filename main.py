"""CLI entry point for the Polymarket Weather Market Scanner."""

import argparse
import asyncio
import sys
import time

from bot.config import load_config
from bot.cities import load_cities
from bot.scanner import run_scan, save_scan
from bot.display import console, show_scan_summary, show_city_detail, show_scan_header


async def cmd_scan(args):
    """Run a single scan and display results."""
    show_scan_header()
    console.print("[cyan]Scanning all markets...[/cyan]")

    start = time.time()
    results = await run_scan(days_ahead=args.days)
    elapsed = time.time() - start

    console.print(f"[dim]Scan completed in {elapsed:.1f}s — {len(results)} markets found[/dim]")

    show_scan_summary(results)

    # Save results
    config = load_config()
    filepath = save_scan(results, config.get("data_dir", "data"))
    console.print(f"[dim]Results saved to {filepath}[/dim]\n")

    return results


async def cmd_watch(args):
    """Continuous scanning loop."""
    config = load_config()
    interval = config.get("scan_interval", 3600)

    console.print(f"[cyan]Watch mode — scanning every {interval}s (Ctrl+C to stop)[/cyan]\n")

    while True:
        try:
            await cmd_scan(args)
            console.print(f"[dim]Next scan in {interval}s...[/dim]\n")
            await asyncio.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped.[/yellow]")
            break


async def cmd_city(args):
    """Deep dive on a single city."""
    slug = args.slug.lower().strip()
    cities = load_cities()

    if slug not in cities:
        console.print(f"[red]Unknown city: {slug}[/red]")
        console.print(f"Available: {', '.join(sorted(cities.keys()))}")
        return

    show_scan_header()
    console.print(f"[cyan]Scanning {cities[slug]['name']}...[/cyan]")

    results = await run_scan(days_ahead=args.days)

    city_results = [r for r in results if r.get("city") == slug]
    if not city_results:
        console.print(f"[yellow]No active markets found for {slug}[/yellow]")
        return

    for r in city_results:
        show_city_detail(r)


def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Weather Market Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # scan
    p_scan = sub.add_parser("scan", help="Run one scan and display results")
    p_scan.add_argument("--days", type=int, default=4, help="Days ahead to scan (default: 4)")

    # watch
    p_watch = sub.add_parser("watch", help="Continuous scanning loop")
    p_watch.add_argument("--days", type=int, default=4, help="Days ahead to scan (default: 4)")

    # city
    p_city = sub.add_parser("city", help="Deep dive on one city")
    p_city.add_argument("slug", help="City slug (e.g., nyc, london, tokyo)")
    p_city.add_argument("--days", type=int, default=4, help="Days ahead to scan (default: 4)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "scan":
        asyncio.run(cmd_scan(args))
    elif args.command == "watch":
        asyncio.run(cmd_watch(args))
    elif args.command == "city":
        asyncio.run(cmd_city(args))


if __name__ == "__main__":
    main()
