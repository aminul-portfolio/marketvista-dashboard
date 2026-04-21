# MarketVista Dashboard — Screenshot Shortlist

## Screenshot directory

Store all final images in:

```text
docs/screenshots/
```

---

## Final screenshot set

### 1. Full dashboard — hero, signals, and monitoring command surface
**Filename**
```text
00_dashboard_full_hero_and_signals.png
```

**What to show**
- suite breadcrumb
- hero section
- snapshot freshness
- KPI cards
- latest signals
- operational status
- watchlist quick view

**What it proves**
- monitoring-first identity
- signal workflow
- freshness awareness
- top mover and watchlist prioritization

---

### 2. Dashboard charts
**Filename**
```text
01_dashboard_charts.png
```

**What to show**
- Market Controls
- Line Price History Chart
- Candlestick Chart

**What it proves**
- OHLC-backed charting
- date-range-driven analyst inspection
- historical monitoring support

---

### 3. Dashboard tables
**Filename**
```text
02_dashboard_tables.png
```

**What to show**
- Live Price Table
- Recent OHLC Candles table
- filter controls
- pagination

**What it proves**
- latest snapshot inspection
- historical OHLC inspection
- tabular monitoring surfaces, not just charts

---

### 4. Operational status and watchlist
**Filename**
```text
03_dashboard_operational_and_watchlist.png
```

**What to show**
- Operational Status panel
- Top Mover
- Watchlist Quick View

**What it proves**
- analyst prioritization logic
- tracked asset focus
- decision-support orientation

---

### 5. Admin monitoring index
**Filename**
```text
04_admin_monitoring_index.png
```

**What to show**
- Django admin homepage
- monitoring model group only

**What it proves**
- clean admin/data layer
- reviewer inspectability
- not just a styled frontend

---

### 6. Admin market signals
**Filename**
```text
05_admin_market_signals.png
```

**What to show**
- Market signals list page
- asset
- signal type
- severity
- is_active
- timestamp
- filter sidebar

**What it proves**
- computed signals are persisted
- severity is inspectable
- signal engine is visible beyond dashboard UI

---

### 7. Admin price OHLC
**Filename**
```text
06_admin_price_ohlc.png
```

**What to show**
- Price OHLC list page
- multiple rows
- open/high/low/close/volume/source
- filter sidebar

**What it proves**
- historical price structure is stored
- charting and signal logic are backed by real rows

---

### 8. Admin price snapshots
**Filename**
```text
07_admin_price_snapshots.png
```

**What to show**
- Price snapshots list page
- latest price rows
- timestamps
- filter sidebar

**What it proves**
- freshness layer is backed by persisted snapshots
- live table values come from stored snapshot records

---

## Capture rules

- use dark mode
- keep browser zoom at 100%
- keep a consistent browser width
- prefer section-by-section screenshots over one long stitched image
- keep filters and pagination in intentional states
- avoid duplicate sticky navbars in long captures
- use seeded demo data before capture

---

## Pre-capture commands

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

---

## Best capture order

1. `00_dashboard_full_hero_and_signals.png`
2. `03_dashboard_operational_and_watchlist.png`
3. `01_dashboard_charts.png`
4. `02_dashboard_tables.png`
5. `04_admin_monitoring_index.png`
6. `05_admin_market_signals.png`
7. `06_admin_price_ohlc.png`
8. `07_admin_price_snapshots.png`
