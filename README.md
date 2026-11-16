# DMI climate data – Gundsømagle Kirke

Downloads 10 years (2015–2024) of daily, quality-controlled climate data from
DMI's Climate Data API for the area around Gundsømagle Kirke (55.735°N, 12.148°E).
Only station data is used, no interpolated values.

## Requirements

- Python 3 with `requests` and `pandas`
- No API key needed

## Scripts

Run them in this order:

1. **`nearest_station.py`** – lists DMI stations within ~20 km of the church
   that were in operation for the whole period, sorted by distance.
2. **`coverage.py`** – checks how many days of data each candidate station has
   for selected parameters (complete = 3,653 days).
3. **`download.py`** – downloads the daily data and saves it as CSV.

## Stations used

| Station | Name              | Distance | Used for                  |
|---------|-------------------|----------|---------------------------|
| 06170   | Roskilde Lufthavn | 16.5 km  | All parameters            |
| 06188   | Sjælsmark         | 22.8 km  | Sunshine hours only       |

Roskilde Lufthavn does not measure sunshine hours, so `bright_sunshine` is taken
from Sjælsmark and stored in a separate column, `bright_sunshine_06188`.

## Output

- `dmi_gundsoemagle_2015-2024.csv` – standard CSV (comma-separated, decimal point)
- `dmi_gundsoemagle_2015-2024_excel.csv` – for Danish Excel (semicolon, decimal comma)

One row per day, one column per parameter.

## Notes

- Dates are taken directly from DMI's day labels (Danish local time), not
  converted to UTC.
- Some parameters (e.g. daily max/min) may carry the time of the extreme in
  their timestamp; only the date part is used.
