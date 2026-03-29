"""Scrape Academy Museum calendar for Screenings and Conversations events."""

import json
import re
from datetime import date, datetime, timedelta

import pytz
import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

CALENDAR_URL = "https://www.academymuseum.org/calendar"
EVENT_BASE_URL = "https://www.academymuseum.org/en/calendar/"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = "ecc49deb9e28d9a978b54a4321e5c4f1"  # via cinelength.com
PACIFIC = pytz.timezone("America/Los_Angeles")
INCLUDED_TYPES = {"Screenings", "Conversations"}


def get_date_ranges(today=None):
    """Calculate date ranges: rest of current month + next 2 full months."""
    if today is None:
        today = date.today()

    ranges = []

    # Rest of current month (tomorrow through end of month)
    tomorrow = today + timedelta(days=1)
    end_of_month = (today + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
    if tomorrow <= end_of_month:
        ranges.append((tomorrow, end_of_month))

    # Next 2 full months
    for i in range(1, 3):
        first = (today + relativedelta(months=i)).replace(day=1)
        last = (today + relativedelta(months=i + 1)).replace(day=1) - timedelta(days=1)
        ranges.append((first, last))

    return ranges


def fetch_calendar_page(start_date, end_date):
    """Fetch a calendar page for the given date range."""
    params = {"start": start_date.isoformat(), "end": end_date.isoformat()}
    resp = requests.get(CALENDAR_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_events_json(html):
    """Extract the events dictionary from the embedded __NEXT_DATA__ JSON."""
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        data = json.loads(script.string)
        return data.get("props", {}).get("pageProps", {}).get("cfProgramsKeyedByTkId", {})

    # Fallback: look for cfProgramsKeyedByTkId in any script tag
    for script in soup.find_all("script"):
        if script.string and "cfProgramsKeyedByTkId" in (script.string or ""):
            match = re.search(r'"cfProgramsKeyedByTkId"\s*:\s*(\{.+?\})\s*,\s*"', script.string, re.DOTALL)
            if match:
                return json.loads(match.group(1))

    return {}


def extract_text_from_rich_text(rich_text):
    """Extract plain text from a Contentful rich text JSON structure."""
    if not rich_text or not isinstance(rich_text, dict):
        return ""
    json_data = rich_text.get("json", rich_text)
    if not isinstance(json_data, dict):
        return ""
    return _walk_content(json_data.get("content", []), top_level=True).strip()


def _walk_content(content_list, top_level=False):
    """Recursively walk Contentful rich text content nodes to extract text."""
    parts = []
    for node in content_list:
        if node.get("nodeType") == "text":
            parts.append(node.get("value", ""))
        elif node.get("nodeType") in ("paragraph", "heading-1", "heading-2", "heading-3"):
            text = _walk_content(node.get("content", []))
            if text.strip():
                parts.append(text + "\n")
        elif "content" in node:
            parts.append(_walk_content(node["content"]))
    return "".join(parts)


def parse_metadata(metadata_text):
    """Parse filmMetadata1 text to extract location, time, date, and cost."""
    info = {}
    for line in metadata_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for field in ["Location", "Time", "Times", "Date", "Dates", "Cost"]:
            pattern = rf"^{field}:\s*(.+)$"
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                key = "time" if field in ("Time", "Times") else field.lower().rstrip("s")
                info[key] = match.group(1).strip()
                break
    return info


def parse_time_string(time_str, event_date):
    """Parse a time string like '2pm', '7:30pm', 'Noon' into a datetime."""
    time_str = time_str.strip().split(",")[0].split(" and ")[0].strip()
    time_str = time_str.split("–")[0].split("-")[0].strip()

    if time_str.lower() == "noon":
        hour, minute = 12, 0
    elif time_str.lower() == "midnight":
        hour, minute = 0, 0
    else:
        time_str = time_str.lower().replace(".", "")
        match = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", time_str)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        if match.group(3) == "pm" and hour != 12:
            hour += 12
        elif match.group(3) == "am" and hour == 12:
            hour = 0

    naive = datetime(event_date.year, event_date.month, event_date.day, hour, minute)
    return PACIFIC.localize(naive)


def parse_runtime_from_metadata(metadata_text):
    """Extract runtime in minutes from film metadata like '170 min.' or '95 min'."""
    match = re.search(r"(\d+)\s*min", metadata_text)
    if match:
        return int(match.group(1))
    return None


def lookup_runtime_tmdb(title):
    """Look up a film's runtime via TMDb API (powers cinelength.com)."""
    try:
        # Strip suffixes like "in 35mm", "in 4K" for better search results
        clean_title = re.sub(r"\s+in\s+(35mm|4K|DCP|70mm)\s*$", "", title, flags=re.IGNORECASE).strip()
        resp = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "language": "en-US", "query": clean_title, "page": 1},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        movie_id = results[0]["id"]
        detail = requests.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=10,
        )
        detail.raise_for_status()
        runtime = detail.json().get("runtime")
        if runtime and runtime > 0:
            return runtime
    except requests.RequestException:
        pass
    return None


def filter_and_parse_events(events_dict):
    """Filter to Screenings/Conversations and parse into structured dicts."""
    parsed = []

    for event_id, event in events_dict.items():
        # Check programTypesCollection for included types
        program_types = set()
        ptc = event.get("programTypesCollection", {})
        if ptc and ptc.get("items"):
            for item in ptc["items"]:
                name = item.get("name", "")
                if name:
                    program_types.add(name)

        matching_types = program_types & INCLUDED_TYPES
        if not matching_types:
            continue

        # Extract basic fields
        title = extract_text_from_rich_text(event.get("programTitle") or event.get("title", {}))
        if not title:
            title = event.get("slug", event_id).replace("-", " ").title()

        # Get the HTML title if available for richer display
        title_html = ""
        title_field = event.get("title", {})
        if isinstance(title_field, dict):
            title_html = title_field.get("html", "")

        slug = event.get("slug", "")
        url = f"{EVENT_BASE_URL}{slug}" if slug else ""

        description = extract_text_from_rich_text(event.get("filmDescription1"))
        tagline = extract_text_from_rich_text(event.get("programTagline"))

        # Parse dates
        start_str = event.get("activeStartDate", "")
        end_str = event.get("activeEndDate", "")
        if not start_str:
            continue

        event_date = datetime.fromisoformat(start_str.replace("Z", "+00:00")).date()

        # Parse metadata for time and location
        metadata_text = extract_text_from_rich_text(event.get("filmMetadata1"))
        metadata = parse_metadata(metadata_text)

        location = metadata.get("location", "Academy Museum of Motion Pictures")
        time_str = metadata.get("time", "")
        cost = metadata.get("cost", "")

        # Get runtime: parse from metadata, fall back to TMDb
        runtime_min = parse_runtime_from_metadata(metadata_text)
        if runtime_min is None and "Screenings" in matching_types:
            runtime_min = lookup_runtime_tmdb(title)
            if runtime_min:
                print(f"  TMDb lookup: {title} → {runtime_min} min")

        # Build datetime with parsed time, or mark as all-day
        all_day = False
        if time_str:
            dt_start = parse_time_string(time_str, event_date)
            if dt_start:
                if runtime_min:
                    duration = timedelta(minutes=runtime_min)
                elif "Screenings" in matching_types:
                    duration = timedelta(hours=2)
                else:
                    duration = timedelta(hours=1, minutes=30)
                dt_end = dt_start + duration
            else:
                all_day = True
                dt_start = event_date
                dt_end = event_date + timedelta(days=1)
        else:
            all_day = True
            dt_start = event_date
            dt_end = event_date + timedelta(days=1)

        # Image
        image_url = ""
        img = event.get("image")
        if img and isinstance(img, dict):
            image_url = img.get("url", "")

        # Extract film technical metadata for screenings
        film_info = ""
        if "Screenings" in matching_types and not metadata.get("location"):
            film_info = metadata_text

        parsed.append({
            "id": event_id,
            "title": title,
            "title_html": title_html,
            "url": url,
            "description": description,
            "tagline": tagline,
            "location": location,
            "dt_start": dt_start,
            "dt_end": dt_end,
            "all_day": all_day,
            "event_date": event_date,
            "time_str": time_str,
            "cost": cost,
            "film_info": film_info,
            "runtime_min": runtime_min,
            "categories": sorted(matching_types),
            "image_url": image_url,
            "members_only": event.get("membersOnly", False),
        })

    # Sort by start date/time
    parsed.sort(key=lambda e: e["event_date"])
    return parsed


def scrape_all_events(today=None):
    """Scrape all events across the 3-month lookahead window."""
    ranges = get_date_ranges(today)
    all_events = {}

    for start, end in ranges:
        html = fetch_calendar_page(start, end)
        events = extract_events_json(html)
        # Merge, deduplicating by event ID
        for eid, event in events.items():
            if eid not in all_events:
                all_events[eid] = event

    return filter_and_parse_events(all_events)
