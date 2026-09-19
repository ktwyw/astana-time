# Astana time

A time-zone converter that always starts from Astana, so you never set your
own zone again. Shows the current Astana time, converts any Astana time (or a
time in another city) to your list of cities, and draws a meeting-planner grid
that shows at a glance which Astana hours fall in working hours elsewhere.

Two versions with identical logic:

- `index.html` — web page. Live at https://ktwyw.github.io/astana-time/
- `astana_time.py` — desktop app (tkinter, Python 3.9+)

## Web version

The top shows the live Astana clock. In **Convert a time**, enter a date and
time; by default it's an Astana time, but choose another city if the time you
have is in that city ("9:00 New York → when is that in Astana?"). Every row
shows the local time, date, UTC offset and difference from Astana, with a
"+1 day" badge when the date rolls over.

The **meeting planner** has one row per city and one column per Astana hour
for the chosen date: green cells are 9–18 local time, amber are early morning
and evening, grey is night. Click a column to jump the converter to that hour.

Cities are always ordered west to east by their UTC offset at the chosen
moment, with Astana highlighted in its natural place, so the table and the
planner read like a map. Add and remove cities as you like; the list is
remembered in your browser.

## Desktop version

```
python astana_time.py
```

Same features in a window: live clock, converter table, planner strip, add
and remove cities (the list is saved to `astana_time_cities.json` next to the
script). On Windows run `pip install tzdata` once, because Windows has no
built-in time-zone database.

## How it works

Neither version stores any offsets. The browser's `Intl.DateTimeFormat` and
Python's `zoneinfo` module both use the IANA time-zone database, which knows
every zone's rules, including daylight-saving changes and their historical
dates. Kazakhstan moved to a single zone, UTC+5 with no daylight saving, on
1 March 2024; that is `Asia/Almaty` in IANA terms, and Astana shares it.

To add a city to the menu, add a line to `CATALOG` in either file with an
IANA zone name (for example `"Lisbon": "Europe/Lisbon"`).

## Ideas for next steps

- Share a converter link with the time encoded in the URL
- Show sunrise and sunset for Astana
- A "find a slot" button that highlights hours inside working time for all cities
- Kazakh and Russian interface
