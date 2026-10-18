# excavation-weather-check-texas

A small Python CLI that tells you whether the next 48 hours look safe to dig. Built for excavation contractors in rural North Texas. Default location is Lone Camp, TX (the Out West Septic service area).

It hits the public NOAA weather API. No API key. No account. No rate limit worth worrying about for personal use.

## What it does

- Looks up your gridpoint from your lat/lon
- Pulls the next 72 hours of hourly forecast
- Scans for the things that ruin a dig day: heavy rain, thunderstorms, freezing temps, frozen precipitation
- Prints a `DIG` or `HOLD` recommendation with the reason

It's not a substitute for looking out the window. It is a quick sanity check before you load the excavator.

## Install

No install. The script is stdlib only.

```
git clone https://github.com/TexasSepticEnthusiast/excavation-weather-check-texas
cd excavation-weather-check-texas
python weather_check.py
```

## Usage

Default location (Lone Camp, TX):

```
python weather_check.py
```

Specific coordinates:

```
python weather_check.py --lat 32.75 --lon -98.40
```

Machine-readable output:

```
python weather_check.py --json | jq
```

Use a non-default exit code to gate scripts:

```
if python weather_check.py > /dev/null 2>&1; then
    echo "go for it"
else
    echo "hold off"
fi
```

The script exits `0` on `DIG` and `1` on `HOLD`.

## What it checks for

The recommendation is `HOLD` if any of these are in the next 48 hours:

- `Heavy Rain` in the short forecast
- `Showers And Thunderstorms` in the short forecast
- `Thunderstorms` in the short forecast
- `Freezing`, `Frost`, `Snow`, `Sleet`, `Wintry Mix`, or `Ice` in the short forecast
- Hourly temperature at or below 32°F

Anything else: `DIG`.

The thresholds are conservative. A "Chance Rain Showers" forecast will pass. A "Rain Showers Likely" forecast will pass. The tool errs on the side of "you can probably still dig" because the operator has the final call.

## Running the tests

```
python -m unittest test_weather_check.py -v
```

The tests cover the `decide()` function. They don't make network calls.

## Customizing

To change the default location, edit the constants at the top of `weather_check.py`:

```python
DEFAULT_LAT = 32.78
DEFAULT_LON = -98.32
DEFAULT_LOCATION = "Lone Camp, TX"
```

If you want a different hold threshold (say, anything below 40°F instead of 32°F), edit the `decide()` function. The function is 20 lines.

## Known limitations

- The NOAA API covers US locations only. The script will fail outside the US.
- The forecast only goes 7 days out. The script looks at 48 hours. Anything beyond is not factored in.
- "Recent rainfall" is not checked. The script reads the forecast, not observed past precipitation. If it rained 4 inches yesterday, the tool won't know.
- "Ground saturation" is not checked. A saturated yard after a wet week will still read `DIG`. The operator has to know their ground.

## Credits

NOAA weather data is public domain. The script's User-Agent identifies the project so NOAA can contact us if we abuse the API.

## License

MIT. See `LICENSE`.
