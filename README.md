# Academy Museum Calendar Feeds

UNOFFICIAL RSS and ICS feeds for upcoming film screenings and conversations at the [Academy Museum of Motion Pictures](https://www.academymuseum.org/calendar) in Los Angeles.

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
3. Filters for Screenings, Conversations and Book Signings categories
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

## Notes

- For RSS, use this link: https://raw.githubusercontent.com/samkrishna/academymuseum-calendar/main/docs/feed.xml
- For iCalendar and other .ics-compatibile calendar applications, use this link: https://raw.githubusercontent.com/samkrishna/academymuseum-calendar/main/docs/calendar.ics

NOTE: For the RSS readers, I have tested this on NetNewsWire 7.x (my personal RSS reader) and Feedly. I have tried to get the RSS script to sort the entries based on screening time in ascending order and it looks like Feedly reads this sequence correctly in a way that NetNewsWire 7.x does not. (I use "Sort from Oldest to Newest" to get the correct sequence.)

NOTE: For the .ics/iCal apps, past screening will revert to "all-day events" because they are no longer purchasable through Ticketure.

NOTE: These are unofficial feeds I whipped up using Anthropic's Claude Code. My only affiliation with the Academy Museum is that I'm a *Museum** member (as distinct from an Academy Member). Insert all the standard legal and technical disclaimers here including that IF the Museum chooses to change their website in a way that breaks these feeds, they'll stop working.

I assume ZERO legal responsibility or liability for the production of these feeds. It's an MIT license, after all.