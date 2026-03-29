# Academy Museum Calendar Feeds

RSS and ICS feeds for upcoming film screenings and conversations at the [Academy Museum of Motion Pictures](https://www.academymuseum.org/calendar) in Los Angeles.

## Subscribe

- **RSS** — `feed.xml` for feed readers
- **ICS** — `calendar.ics` for calendar apps (Google Calendar, Apple Calendar, Outlook)

Feeds cover a rolling 3-month window and are updated daily.

## What's Included

- **Screenings** — film presentations, retrospectives, and special screenings
- **Conversations** — talks, panels, gallery spotlights, and community events

Each entry includes title, date, location, description, runtime (for screenings), and a link to the event page on academymuseum.org.

## How It Works

1. Fetches the Academy Museum calendar page for the current month (remaining days) plus the next two full months
2. Extracts event data from the embedded JSON (Contentful CMS)
3. Filters to Screenings and Conversations categories
4. Parses film runtimes from metadata, with [TMDb](https://www.themoviedb.org/) fallback (via [cinelength.com](https://cinelength.netlify.app))
5. Generates `feed.xml` (RSS 2.0) and `calendar.ics` (iCalendar) in the `docs/` directory

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Output is written to `docs/feed.xml` and `docs/calendar.ics`.

## Automated Updates

A GitHub Actions workflow (`.github/workflows/update-feeds.yml`) runs daily and commits updated feeds to the `docs/` directory. Feeds are served via GitHub Pages.

## Note

Event start times are only available for some events (primarily Conversations). Most screenings appear as all-day calendar entries because the museum's data does not include structured screening times.
