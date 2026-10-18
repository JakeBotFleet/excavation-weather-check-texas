"""Tests for the decide() function. No network calls."""
import unittest

from weather_check import decide, HourlyForecast


def make_fcst(time: str, short: str, temp: float | None = 60.0, pop: int | None = 0) -> HourlyForecast:
    return HourlyForecast(
        time=time, temp_f=temp, wind_mph=5.0, precip_prob=pop,
        short_forecast=short, detailed=None,
    )


class TestDecide(unittest.TestCase):
    def test_clear_skies_dig(self):
        fcsts = [make_fcst("2026-10-17T12:00:00", "Sunny", 75, 0)]
        rec, reasons = decide(fcsts)
        self.assertEqual(rec, "DIG")
        self.assertEqual(len(reasons), 1)

    def test_heavy_rain_hold(self):
        fcsts = [make_fcst("2026-10-17T12:00:00", "Heavy Rain", 60, 90)]
        rec, _ = decide(fcsts)
        self.assertEqual(rec, "HOLD")

    def test_thunderstorms_hold(self):
        fcsts = [make_fcst("2026-10-17T12:00:00", "Showers And Thunderstorms", 65, 80)]
        rec, _ = decide(fcsts)
        self.assertEqual(rec, "HOLD")

    def test_freezing_temp_hold(self):
        fcsts = [make_fcst("2026-10-17T12:00:00", "Mostly Clear", 28, 0)]
        rec, reasons = decide(fcsts)
        self.assertEqual(rec, "HOLD")
        self.assertTrue(any("Sub-freezing" in r for r in reasons))

    def test_snow_phrase_hold(self):
        fcsts = [make_fcst("2026-10-17T12:00:00", "Snow", 30, 100)]
        rec, _ = decide(fcsts)
        self.assertEqual(rec, "HOLD")

    def test_outside_48h_window(self):
        # 72h out: should not affect decision
        fcsts = [
            make_fcst("2026-10-17T00:00:00", "Sunny", 70, 0),
            make_fcst("2026-10-20T00:00:00", "Heavy Rain", 60, 90),  # 72h+ out
        ]
        rec, _ = decide(fcsts)
        self.assertEqual(rec, "DIG")

    def test_mixed_24h_window(self):
        fcsts = [
            make_fcst("2026-10-17T06:00:00", "Sunny", 70, 0),
            make_fcst("2026-10-18T14:00:00", "Thunderstorms", 65, 80),
        ]
        rec, _ = decide(fcsts)
        self.assertEqual(rec, "HOLD")


if __name__ == "__main__":
    unittest.main()
