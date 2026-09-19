#!/usr/bin/env python3
"""
astana_time.py — a desktop time-zone converter that always starts from Astana.

Run:  python astana_time.py

Python 3.9+ (uses the built-in zoneinfo module). On Windows, run
    pip install tzdata
once, because Windows has no system time-zone database.
"""

import json
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ---------- configuration ----------
HOME_NAME, HOME_ZONE = "Astana", "Asia/Almaty"       # UTC+5, no DST since March 2024

CATALOG = {
    "Almaty": "Asia/Almaty", "London": "Europe/London", "Paris": "Europe/Paris", "Berlin": "Europe/Berlin",
    "Rome": "Europe/Rome", "Madrid": "Europe/Madrid", "Warsaw": "Europe/Warsaw", "Kyiv": "Europe/Kyiv",
    "Moscow": "Europe/Moscow", "Istanbul": "Europe/Istanbul", "Tbilisi": "Asia/Tbilisi", "Baku": "Asia/Baku",
    "Tehran": "Asia/Tehran", "Dubai": "Asia/Dubai", "Riyadh": "Asia/Riyadh", "Tashkent": "Asia/Tashkent",
    "Bishkek": "Asia/Bishkek", "Dushanbe": "Asia/Dushanbe", "Ashgabat": "Asia/Ashgabat", "Kabul": "Asia/Kabul",
    "New Delhi": "Asia/Kolkata", "Dhaka": "Asia/Dhaka", "Bangkok": "Asia/Bangkok", "Jakarta": "Asia/Jakarta",
    "Singapore": "Asia/Singapore", "Kuala Lumpur": "Asia/Kuala_Lumpur", "Hong Kong": "Asia/Hong_Kong",
    "Beijing": "Asia/Shanghai", "Taipei": "Asia/Taipei", "Seoul": "Asia/Seoul", "Tokyo": "Asia/Tokyo",
    "Ulaanbaatar": "Asia/Ulaanbaatar", "Sydney": "Australia/Sydney", "Auckland": "Pacific/Auckland",
    "Cairo": "Africa/Cairo", "Nairobi": "Africa/Nairobi", "Johannesburg": "Africa/Johannesburg",
    "New York": "America/New_York", "Toronto": "America/Toronto", "Chicago": "America/Chicago",
    "Denver": "America/Denver", "Los Angeles": "America/Los_Angeles", "Vancouver": "America/Vancouver",
    "Mexico City": "America/Mexico_City", "São Paulo": "America/Sao_Paulo",
    "Buenos Aires": "America/Argentina/Buenos_Aires", "UTC": "UTC",
}
DEFAULT_CITIES = ["London", "Berlin", "Moscow", "Istanbul", "Dubai", "Tashkent", "Beijing", "Seoul", "Tokyo", "New York"]
SETTINGS = Path(__file__).with_name("astana_time_cities.json")   # remembers your city list

# ---------- palette ----------
BG, CARD, FIELD, TEXT, MUTED, ACCENT, LINE = "#F2F4F8", "#FFFFFF", "#EEF1F6", "#16213A", "#5F6B85", "#2456C7", "#D6DCE8"
WORK, EDGE, NIGHT = "#BFE8CF", "#FBE3B0", "#E6E9F0"
FONT = "Segoe UI"


# ---------- time helpers ----------
def zone_of(name: str) -> ZoneInfo:
    return ZoneInfo(HOME_ZONE if name == HOME_NAME else CATALOG[name])


def offset_label(dt: datetime) -> str:
    """'UTC+5' or 'UTC+5:30' for an aware datetime."""
    secs = int(dt.utcoffset().total_seconds())
    sign = "+" if secs >= 0 else "−"
    h, m = divmod(abs(secs) // 60, 60)
    return f"UTC{sign}{h}" + (f":{m:02d}" if m else "")


def ordered(names, instant: datetime):
    """Sort city names west → east by their UTC offset at the given instant."""
    return sorted(names, key=lambda n: (instant.astimezone(zone_of(n)).utcoffset(), n))


def hour_class(hour: int) -> str:
    if 9 <= hour < 18:
        return WORK
    if 7 <= hour < 21:
        return EDGE
    return NIGHT


class AstanaTimeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Astana time")
        self.configure(bg=BG)
        self.cities = self._load_cities()
        self._style()
        self._build()
        self.set_now()
        self._tick()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    # ---------- persistence ----------
    def _load_cities(self):
        try:
            data = json.loads(SETTINGS.read_text())
            cities = [c for c in data if c in CATALOG]
            if cities:
                return cities
        except (OSError, ValueError):
            pass
        return list(DEFAULT_CITIES)

    def _save_cities(self):
        try:
            SETTINGS.write_text(json.dumps(self.cities))
        except OSError:
            pass

    # ---------- window ----------
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox", fieldbackground=FIELD, background=FIELD, foreground=TEXT,
                    arrowcolor=TEXT, bordercolor=LINE, lightcolor=FIELD, darkcolor=FIELD)
        s.map("TCombobox", fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TEXT)])
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, rowheight=26, font=(FONT, 10))
        s.configure("Treeview.Heading", background=FIELD, foreground=MUTED, font=(FONT, 9, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#fff")])

    def _build(self):
        outer = tk.Frame(self, bg=BG, padx=22, pady=18)
        outer.pack(fill="both", expand=True)

        # live clock
        hero = tk.Frame(outer, bg=BG)
        hero.pack(fill="x", pady=(0, 12))
        tk.Label(hero, text="Astana", bg=BG, fg=MUTED, font=(FONT, 13, "bold")).pack(side="left", anchor="s", padx=(0, 12), pady=(0, 6))
        self.clock = tk.Label(hero, text="--:--:--", bg=BG, fg=TEXT, font=(FONT, 34, "bold"))
        self.clock.pack(side="left")
        self.clock_date = tk.Label(hero, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self.clock_date.pack(side="left", anchor="s", padx=12, pady=(0, 8))

        # converter card
        card = tk.Frame(outer, bg=CARD, padx=16, pady=14, highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="both", expand=True)

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")
        self.in_city = self._combo(row, "Time is in", ordered([HOME_NAME] + self.cities, datetime.now(ZoneInfo(HOME_ZONE))), HOME_NAME, width=16)
        self.in_date = self._entry(row, "Date (YYYY-MM-DD)", width=12)
        self.in_time = self._entry(row, "Time (HH:MM)", width=7)
        tk.Button(row, text="Now", command=self.set_now, bg=CARD, fg=ACCENT, relief="flat", cursor="hand2",
                  font=(FONT, 10, "bold"), highlightthickness=1, highlightbackground=ACCENT).pack(side="left", padx=(8, 0), pady=(18, 0))
        tk.Button(row, text="Convert", command=self.render, bg=ACCENT, fg="#fff", activebackground="#3A6BE0",
                  activeforeground="#fff", relief="flat", cursor="hand2", font=(FONT, 10, "bold"),
                  padx=12).pack(side="left", padx=(8, 0), pady=(18, 0))
        self.bind("<Return>", lambda _: self.render())

        self.error = tk.Label(card, text="", bg=CARD, fg="#B3403A", font=(FONT, 9))
        self.error.pack(anchor="w", pady=(4, 0))

        # results table
        self.tree = ttk.Treeview(card, columns=("city", "time", "date", "offset", "diff"), show="headings", height=11)
        for col, text, w in (("city", "City", 130), ("time", "Time", 90), ("date", "Date", 150), ("offset", "Offset", 90), ("diff", "vs Astana", 110)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(10, 0))
        self.tree.tag_configure("home", background="#E8EEFC")

        # planner strip: 24 cells per city, coloured by local hour
        tk.Label(card, text="Working hours by Astana hour, cities west → east (green 9–18, amber 7–9 / 18–21)", bg=CARD, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w", pady=(12, 4))
        self.planner = tk.Canvas(card, bg=CARD, highlightthickness=0, height=40)
        self.planner.pack(fill="x")

        # add / remove
        bottom = tk.Frame(card, bg=CARD)
        bottom.pack(fill="x", pady=(12, 0))
        self.add_city = self._combo(bottom, "Add a city", [c for c in CATALOG if c not in self.cities], "", width=22)
        tk.Button(bottom, text="Add", command=self.add, bg=CARD, fg=ACCENT, relief="flat", cursor="hand2",
                  font=(FONT, 10, "bold"), highlightthickness=1, highlightbackground=ACCENT).pack(side="left", padx=(8, 0), pady=(18, 0))
        tk.Button(bottom, text="Remove selected", command=self.remove, bg=CARD, fg=MUTED, relief="flat", cursor="hand2",
                  font=(FONT, 10), highlightthickness=1, highlightbackground=LINE).pack(side="left", padx=(8, 0), pady=(18, 0))

    def _combo(self, parent, label, values, default, width):
        f = tk.Frame(parent, bg=CARD); f.pack(side="left", padx=(0, 8))
        tk.Label(f, text=label, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        c = ttk.Combobox(f, values=values, state="readonly", width=width, font=(FONT, 10))
        if default: c.set(default)
        c.pack()
        return c

    def _entry(self, parent, label, width):
        f = tk.Frame(parent, bg=CARD); f.pack(side="left", padx=(0, 8))
        tk.Label(f, text=label, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        e = tk.Entry(f, width=width, bg=FIELD, fg=TEXT, insertbackground=TEXT, relief="flat", font=(FONT, 11),
                     highlightthickness=1, highlightbackground=LINE, highlightcolor=ACCENT)
        e.pack(ipady=4)
        return e

    # ---------- actions ----------
    def _tick(self):
        now = datetime.now(ZoneInfo(HOME_ZONE))
        self.clock.config(text=now.strftime("%H:%M:%S"))
        self.clock_date.config(text=f"{now:%A, %d %B %Y} · {offset_label(now)}")
        self.after(1000, self._tick)

    def set_now(self):
        now = datetime.now(ZoneInfo(HOME_ZONE))
        self.in_city.set(HOME_NAME)
        self.in_date.delete(0, "end"); self.in_date.insert(0, now.strftime("%Y-%m-%d"))
        self.in_time.delete(0, "end"); self.in_time.insert(0, now.strftime("%H:%M"))
        self.render()

    def selected_instant(self):
        try:
            naive = datetime.strptime(f"{self.in_date.get().strip()} {self.in_time.get().strip()}", "%Y-%m-%d %H:%M")
        except ValueError:
            self.error.config(text="Use YYYY-MM-DD for the date and HH:MM for the time.")
            return None
        self.error.config(text="")
        return naive.replace(tzinfo=zone_of(self.in_city.get()))

    def render(self):
        instant = self.selected_instant()
        if not instant:
            return
        home = instant.astimezone(ZoneInfo(HOME_ZONE))
        self.tree.delete(*self.tree.get_children())
        for name in ordered([HOME_NAME] + self.cities, instant):
            local = instant.astimezone(zone_of(name))
            day = (local.date() - home.date()).days
            diff = (local.utcoffset() - home.utcoffset()).total_seconds() / 3600
            diff_text = "home" if name == HOME_NAME else ("same time" if diff == 0 else f"{'+' if diff > 0 else '−'}{abs(diff):g} h")
            time_text = local.strftime("%H:%M") + ("  (+1 day)" if day > 0 else "  (−1 day)" if day < 0 else "")
            self.tree.insert("", "end", values=(name, time_text, local.strftime("%a %d %b %Y"), offset_label(local), diff_text),
                             tags=("home",) if name == HOME_NAME else ())
        self._draw_planner(home)

    def _draw_planner(self, home: datetime):
        c = self.planner
        c.delete("all")
        c.update_idletasks()
        width = max(c.winfo_width(), 400)
        names = ordered([HOME_NAME] + self.cities, home)
        label_w, cell_h = 110, 18
        cell_w = (width - label_w) / 24
        c.config(height=cell_h * (len(names) + 1) + 6)
        for h in range(24):                                   # hour header
            c.create_text(label_w + h * cell_w + cell_w / 2, 8, text=str(h), fill=MUTED, font=(FONT, 7))
        midnight = home.replace(hour=0, minute=0, second=0, microsecond=0)
        for r, name in enumerate(names):
            y = 18 + r * cell_h
            c.create_text(4, y + cell_h / 2, text=name, anchor="w", fill=TEXT, font=(FONT, 8, "bold"))
            for h in range(24):
                local = (midnight + timedelta(hours=h)).astimezone(zone_of(name))
                x = label_w + h * cell_w
                c.create_rectangle(x + 1, y + 1, x + cell_w - 1, y + cell_h - 1, fill=hour_class(local.hour), outline="")
                c.create_text(x + cell_w / 2, y + cell_h / 2, text=str(local.hour), fill=TEXT, font=(FONT, 7))
                if h == home.hour:
                    c.create_rectangle(x + 1, y + 1, x + cell_w - 1, y + cell_h - 1, outline=ACCENT, width=2)

    def add(self):
        name = self.add_city.get()
        if name and name not in self.cities:
            self.cities.append(name)
            self._save_cities()
            self._refresh_menus()
            self.render()

    def remove(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "values")[0]
        if name in self.cities:
            self.cities.remove(name)
            self._save_cities()
            self._refresh_menus()
            self.render()

    def _refresh_menus(self):
        self.in_city.config(values=ordered([HOME_NAME] + self.cities, datetime.now(ZoneInfo(HOME_ZONE))))
        if self.in_city.get() not in [HOME_NAME] + self.cities:
            self.in_city.set(HOME_NAME)
        self.add_city.config(values=[c for c in CATALOG if c not in self.cities])
        self.add_city.set("")


if __name__ == "__main__":
    try:
        ZoneInfo(HOME_ZONE)
    except ZoneInfoNotFoundError:
        raise SystemExit("No time-zone database found. On Windows run:  pip install tzdata")
    AstanaTimeApp().mainloop()
