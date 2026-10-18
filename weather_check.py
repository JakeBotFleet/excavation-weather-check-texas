"""
weather_check.py
Pre-dig weather check for excavation and dirt work.

Default location: Lone Camp, TX (940.452.0598 service area).
NOAA weather API is the data source. No API key required.

Usage:
    python weather_check.py                      # default location, next 3 days
    python weather_check.py --lat 32.78 --lon -98.32
    python weather_check.py --json               # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

DEFAULT_LAT = 32.78
DEFAULT_LON = -98.32
DEFAULT_LOCATION = "Lone Camp, TX"
NOAA_BASE = "https://api.weather.gov"
USER_AGENT = "(outwestseptic-weather-check, contact@outwestseptic.com)"


@dataclass
class HourlyForecast:
    time: str
    temp_f: float | None
    wind_mph: float | None
    precip_prob: int | None
    short_forecast: str
    detailed: str | None = None


@dataclass
class CheckResult:
    location: str
    lat: float
    lon: float
    checked_at: str
    next_3_days: list[HourlyForecast]
    recommendation: str
    reasoning: list[str]


def http_get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_gridpoint(lat: float, lon: float) -> tuple[str, int, int, str]:
    data = http_get(f"{NOAA_BASE}/points/{lat},{lon}")
    props = data["properties"]
    office = props["cwa"]
    x, y = props["gridX"], props["gridY"]
    location_name = ", ".join(props.get("relativeLocation", {}).get("properties", {}).get("city", "").split())
    state = props.get("relativeLocation", {}).get("properties", {}).get("state", "")
    full_name = f"{location_name}, {state}".strip(", ")
    if not full_name:
        full_name = f"({lat}, {lon})"
    return office, x, y, full_name


def get_hourly(office: str, x: int, y: int, hours: int = 72) -> list[HourlyForecast]:
    data = http_get(f"{NOAA_BASE}/gridpoints/{office}/{x},{y}/forecast/hourly")
    periods = data["properties"]["periods"][:hours]
    out = []
    for p in periods:
        out.append(
            HourlyForecast(
                time=p.get("startTime", ""),
                temp_f=p.get("temperature"),
                wind_mph=p.get("windSpeed", "").split()[0] if p.get("windSpeed") else None,
                precip_prob=p.get("probabilityOfPrecipitation", {}).get("value"),
                short_forecast=p.get("shortForecast", ""),
                detailed=p.get("detailedForecast"),
            )
        )
    return out


def decide(forecasts: list[HourlyForecast]) -> tuple[str, list[str]]:
    """Return (recommendation, reasoning). recommendation in {DIG, HOLD}."""
    reasons: list[str] = []
    bad_rain_terms = ("Heavy Rain", "Showers And Thunderstorms", "Thunderstorms")
    freeze_terms = ("Freezing", "Frost", "Snow", "Wintry Mix", "Sleet", "Ice")

    for f in forecasts[:48]:
        if any(term in f.short_forecast for term in bad_rain_terms):
            reasons.append(
                f"Heavy precipitation in forecast at {f.time}: {f.short_forecast}"
            )
        if any(term in f.short_forecast for term in freeze_terms):
            reasons.append(
                f"Freezing or frozen precip at {f.time}: {f.short_forecast}"
            )
        if f.temp_f is not None and f.temp_f <= 32:
            reasons.append(
                f"Sub-freezing at {f.time}: {f.temp_f}°F"
            )

    if reasons:
        return "HOLD", reasons
    return "DIG", ["No heavy rain, no freeze, no thunderstorms in next 48 hours."]


def run(lat: float, lon: float, location: str, hours: int = 72) -> CheckResult:
    office, x, y, official = get_gridpoint(lat, lon)
    forecasts = get_hourly(office, x, y, hours=hours)
    rec, reasons = decide(forecasts)
    return CheckResult(
        location=official or location,
        lat=lat,
        lon=lon,
        checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        next_3_days=forecasts,
        recommendation=rec,
        reasoning=reasons,
    )


def render_text(result: CheckResult) -> str:
    lines = []
    lines.append(f"Weather check for {result.location}")
    lines.append(f"Checked at {result.checked_at}")
    lines.append("")
    lines.append(f"Recommendation: {result.recommendation}")
    for r in result.reasoning:
        lines.append(f"  - {r}")
    lines.append("")
    lines.append("Next 24 hours:")
    for f in result.next_3_days[:24]:
        rain = f" rain={f.precip_prob}%" if f.precip_prob is not None else ""
        temp = f" {f.temp_f}°F" if f.temp_f is not None else ""
        lines.append(f"  {f.time[5:16].replace('T', ' ')} {temp}{rain}  {f.short_forecast}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Pre-dig weather check for excavation work.")
    p.add_argument("--lat", type=float, default=DEFAULT_LAT)
    p.add_argument("--lon", type=float, default=DEFAULT_LON)
    p.add_argument("--location", default=DEFAULT_LOCATION)
    p.add_argument("--hours", type=int, default=72)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args()

    try:
        result = run(args.lat, args.lon, args.location, args.hours)
    except Exception as e:
        print(f"weather check failed: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))
    else:
        print(render_text(result))

    return 0 if result.recommendation == "DIG" else 1


if __name__ == "__main__":
    sys.exit(main())
