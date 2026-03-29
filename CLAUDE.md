# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scrapes the Academy Museum of Motion Pictures calendar (academymuseum.org/calendar) and generates RSS and ICS feeds for **Screenings** and **Conversations** events, covering a rolling 3-month lookahead window.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate feeds (outputs to docs/)
python main.py
```

## Architecture

- **`scraper.py`** — Fetches calendar pages using `?start=&end=` query params, extracts embedded JSON from `__NEXT_DATA__` script tag (Contentful CMS), filters to Screenings/Conversations via `programTypesCollection`, parses `filmMetadata1` rich text for time/location.
- **`feeds.py`** — Generates `feed.xml` (RSS 2.0 via feedgen) and `calendar.ics` (via icalendar lib). Events with parsed times get proper DTSTART/DTEND; others become all-day events.
- **`main.py`** — Entry point: scrape → generate → write to `docs/`.
- **`docs/`** — Served by GitHub Pages. Contains `feed.xml`, `calendar.ics`, and `index.html`.
- **`.github/workflows/update-feeds.yml`** — Daily cron job that regenerates and commits feeds.

## Key Details

- Event times are only available as human-readable text in `filmMetadata1` (e.g., "Time: 2pm"). Most screenings lack structured time data and are treated as all-day events.
- The museum is always closed on Tuesdays.
- All event times are Pacific Time (`America/Los_Angeles`).
- The scraper fetches 3 separate date ranges: remainder of current month + next 2 full months.
