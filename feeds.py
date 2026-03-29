"""Generate RSS and ICS feeds from parsed Academy Museum events."""

from datetime import date, datetime

import pytz
from feedgen.feed import FeedGenerator
from icalendar import Calendar, Event, vText

PACIFIC = pytz.timezone("America/Los_Angeles")
SITE_URL = "https://www.academymuseum.org/calendar"
FEED_TITLE = "Academy Museum of Motion Pictures — Screenings & Conversations"
FEED_DESCRIPTION = (
    "Upcoming film screenings and conversations at the "
    "Academy Museum of Motion Pictures in Los Angeles."
)


def _build_description(event):
    """Build a description string from event fields."""
    parts = []
    if event["tagline"]:
        parts.append(event["tagline"])
    if event["event_date"]:
        date_str = event["event_date"].strftime("%A, %B %-d, %Y")
        if event["time_str"]:
            date_str += f" at {event['time_str']}"
        parts.append(date_str)
    if event["location"]:
        parts.append(f"Location: {event['location']}")
    if event.get("runtime_min"):
        hours, mins = divmod(event["runtime_min"], 60)
        if hours and mins:
            parts.append(f"Runtime: {hours}h {mins}m")
        elif hours:
            parts.append(f"Runtime: {hours}h")
        else:
            parts.append(f"Runtime: {mins}m")
    if event["cost"]:
        parts.append(f"Cost: {event['cost']}")
    if event["film_info"]:
        parts.append(event["film_info"])
    if event["categories"]:
        parts.append(f"Type: {', '.join(event['categories'])}")
    if event["description"]:
        parts.append(event["description"])
    return "\n\n".join(parts)


def generate_rss(events, output_path):
    """Generate an RSS 2.0 feed XML file."""
    fg = FeedGenerator()
    fg.title(FEED_TITLE)
    fg.link(href=SITE_URL, rel="alternate")
    fg.description(FEED_DESCRIPTION)
    fg.language("en")
    fg.lastBuildDate(datetime.now(pytz.UTC))

    for event in events:
        fe = fg.add_entry()
        fe.id(event["url"] or event["id"])
        fe.title(event["title"])
        if event["url"]:
            fe.link(href=event["url"])

        fe.description(_build_description(event))

        # For RSS pubDate, use dt_start if it's a datetime, otherwise localize the date
        if event["all_day"]:
            pub = PACIFIC.localize(datetime(
                event["event_date"].year, event["event_date"].month, event["event_date"].day
            ))
        else:
            pub = event["dt_start"]
        fe.published(pub)

        if event["categories"]:
            for cat in event["categories"]:
                fe.category(term=cat)

        if event["image_url"]:
            fe.enclosure(event["image_url"], 0, "image/jpeg")

    fg.rss_file(output_path, pretty=True)


def generate_ics(events, output_path):
    """Generate an ICS calendar file."""
    cal = Calendar()
    cal.add("prodid", "-//Academy Museum Calendar//academymuseum.org//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", FEED_TITLE)
    cal.add("x-wr-timezone", "America/Los_Angeles")

    for event_data in events:
        vevent = Event()
        vevent.add("uid", f"{event_data['id']}@academymuseum.org")
        vevent.add("summary", event_data["title"])

        # All-day events use date objects; timed events use datetime
        vevent.add("dtstart", event_data["dt_start"])
        vevent.add("dtend", event_data["dt_end"])

        # Description
        desc = _build_description(event_data)
        if desc:
            vevent.add("description", desc)

        if event_data["location"]:
            vevent.add("location", vText(event_data["location"]))

        if event_data["url"]:
            vevent.add("url", event_data["url"])

        vevent.add("dtstamp", datetime.now(pytz.UTC))

        if event_data["categories"]:
            vevent.add("categories", event_data["categories"])

        cal.add_component(vevent)

    with open(output_path, "wb") as f:
        f.write(cal.to_ical())
