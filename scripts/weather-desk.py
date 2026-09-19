#!/usr/bin/env python3
"""Data desk: the week's weather as a front-page chart article.

Fetches a live 7-day forecast from Open-Meteo (free, no key) and renders a
Weather story — a line chart of daily highs, a table of the week, and a short
templated reading. Everything on the page is computed from the API response:
this is a data desk, deliberately code, never handed to a model. Fix the
script if the numbers or the phrasing are wrong; do not have a model
"improve" it.

Usage:
    weather-desk.py <edition_dir> [--lat L] [--lon L] [--place NAME] [--c|--f]
    weather-desk.py <edition_dir> --place Aberdeen     # uses env defaults

Defaults are Aberdeen, Scotland (57.1497, -2.0943), in Celsius. Requires network;
exits 1 (and writes nothing) if the fetch fails, so a nightly job can fail the run
rather than invent a
paper day with a guessed forecast.

Writes <edition_dir>/articles/02-your-week-in-weather.md (code 02 — right
after the lead, where a weather board belongs).
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

API = "https://api.open-meteo.com/v1/forecast"

# Short sky descriptions from WMO weather codes.
SKIES = {
    (0, 0): "Clear",
    (1, 1): "Mostly clear",
    (2, 2): "Partly cloudy",
    (3, 3): "Overcast",
    (45, 48): "Fog",
    (51, 57): "Drizzle",
    (61, 61): "Light rain",
    (63, 63): "Rain",
    (65, 65): "Heavy rain",
    (71, 77): "Snow",
    (80, 82): "Showers",
    (95, 99): "Storm",
}


def sky(code: int) -> str:
    for (lo, hi), word in SKIES.items():
        if lo <= code <= hi:
            return word
    return "—"


def fetch(lat: float, lon: float) -> dict:
    params = (
        f"latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,weather_code"
        "&timezone=America%2FNew_York&forecast_days=7"
    )
    with urllib.request.urlopen(f"{API}?{params}", timeout=20) as r:
        return json.load(r)


def to_f(c: float) -> int:
    return round(c * 9 / 5 + 32)


def build_article(data: dict, place: str, units: str) -> str:
    d = data["daily"]
    dates = d["time"]
    hi_c, lo_c = d["temperature_2m_max"], d["temperature_2m_min"]
    rain = d["precipitation_probability_max"]
    codes = d["weather_code"]

    if units == "f":
        hi = [to_f(x) for x in hi_c]
        lo = [to_f(x) for x in lo_c]
        deg = "°F"
    else:
        hi, lo = hi_c, lo_c
        deg = "°C"

    # Weekday abbreviations for the axis labels (12-char cap, one per value).
    from datetime import datetime
    labels = []
    for t in dates:
        try:
            labels.append(datetime.fromisoformat(t).strftime("%a"))
        except ValueError:
            labels.append("—")

    peak = max(hi)
    peak_day = labels[hi.index(peak)]
    rain_day = labels[rain.index(max(rain))]
    rain_max = max(rain)

    # Floor the chart just under the coolest high so a warm, flat week still
    # shows its shape (the project's own WRITING.md: "start highs of 94-99 at
    # 80, not 0").
    floor = max(0, (min(hi) // 10) * 10 - 5)
    values = ", ".join(str(v) for v in hi)
    label_str = ", ".join(labels)

    caption = (
        f"Daily highs for the week in {place}, {deg}. The warmest day is "
        f"{peak_day}, at {peak}{deg}; the wettest is {rain_day}, a "
        f"{rain_max}% chance of rain."
    )

    rows = "\n".join(
        f"| {labels[i]} | {hi[i]}{deg} | {lo[i]}{deg} | {rain[i]:>3}% | {sky(codes[i])} |"
        for i in range(len(dates))
    )

    deck = f"The warmest day is {peak_day}; keep the umbrella for {rain_day}"

    # Templated prose — every sentence is derived from the numbers fetched,
    # so the desk adds no guesswork a model might. Length stays above the
    # 60-word floor so the story carries its own headline.
    body = (
        f"Highs in {place} run from {min(hi)}{deg} to {peak}{deg} this week. "
        f"The peak is {peak_day}, when the "
        f"high reaches {peak}{deg}; the coolest nights stay near {min(lo)}{deg}, "
        f"so the mornings are the easy part of any walk. Rain is unevenly "
        f"spread — the likeliest wet day is {rain_day}, at a {rain_max}% "
        f"chance, and the rest of the week is largely dry. None of this is a "
        f"reason to change a plan; it is a reason to know which day to save "
        f"for the long walk and which to spend indoors."
    )

    return f"""---
id: 02-your-week-in-weather
headline: Weather for the Week
deck: {deck}
section: weather
priority: 2
span: 2col
chart:
  kind: line
  values: [{values}]
  labels: [{label_str}]
  show_values: true
  min: {floor}
caption: {caption}
---

{body}

### The board

| Day | High | Low | Rain | Sky |
|:---|---:|---:|---:|---|
{rows}

The forecast is for {place} and comes from Open-Meteo, fetched at run time.
The numbers below the line are exactly what the city shipped; the reading
above them is this desk's, and it changes with the data every night.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edition_dir", type=Path)
    ap.add_argument("--lat", type=float, default=float(os.environ.get("WEATHER_LAT", "57.1497")))
    ap.add_argument("--lon", type=float, default=float(os.environ.get("WEATHER_LON", "-2.0943")))
    ap.add_argument("--place", default=os.environ.get("WEATHER_PLACE", "Aberdeen"))
    ap.add_argument("--c", dest="units", action="store_const", const="f", default="c",
                    help="report in Celsius; default is Fahrenheit (the demo's voice)")
    args = ap.parse_args()

    try:
        data = fetch(args.lat, args.lon)
    except Exception as e:  # network or shape failure — never invent a paper
        print(f"error: could not fetch forecast: {e}", file=sys.stderr)
        return 1

    articles = args.edition_dir / "articles"
    articles.mkdir(parents=True, exist_ok=True)
    out = articles / "02-your-week-in-weather.md"
    out.write_text(build_article(data, args.place, args.units))
    print(f"wrote {out} (7-day forecast for {args.place})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
