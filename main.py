#!/usr/bin/env python3
"""Generate RSS and ICS feeds for Academy Museum screenings and conversations."""

import os
import sys

from scraper import scrape_all_events
from feeds import generate_rss, generate_ics


def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)

    rss_path = os.path.join(output_dir, "feed.xml")
    ics_path = os.path.join(output_dir, "calendar.ics")

    print("Scraping Academy Museum calendar...")
    events = scrape_all_events()
    print(f"Found {len(events)} events (Screenings & Conversations)")

    if not events:
        print("Warning: No events found. Feed files will not be updated.", file=sys.stderr)
        return

    print(f"Generating RSS feed: {rss_path}")
    generate_rss(events, rss_path)

    print(f"Generating ICS feed: {ics_path}")
    generate_ics(events, ics_path)

    print("Done.")


if __name__ == "__main__":
    main()
