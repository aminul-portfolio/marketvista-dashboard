# MarketVista Dashboard

Monitoring-first analyst visibility for a fintech data-to-decision suite.

## Overview

MarketVista Dashboard is the **monitoring and analyst-visibility layer** in a broader fintech workflow:

**DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360**

Its role is to help users monitor tracked assets, review market signals, inspect freshness, manage a watchlist, and decide which assets need deeper investigation.

This project is designed to demonstrate a **monitoring-first data product**. It is intentionally not positioned as a trade journal, pre-trade risk planner, or post-trade analytics dashboard.

---

## What this project is

MarketVista Dashboard is a Django-based market monitoring product that provides:

- signal-aware dashboard surfaces
- watchlist support
- data freshness visibility
- top mover tracking
- historical OHLC-backed charting
- live snapshot inspection
- admin-side monitoring model inspection
- seeded demo data for reviewer-friendly resets
- smoke-test baseline for validation

It is intended to feel like the analyst-monitoring layer in a fintech suite.

---

## What this project is not

This project is **not**:

- a market data ingestion platform
- a pre-trade risk planning product
- a trade journal
- a post-trade analytics dashboard

Those responsibilities belong elsewhere in the suite:

- **DataBridge Market API** → upstream market data source
- **RiskWise Planner** → deeper planning and pre-trade analysis
- **TradeIntel 360** → post-trade outcome review and performance analysis

---

## Suite position

MarketVista sits between raw market data and deeper decision-making.

### Upstream
**DataBridge Market API** powers the monitoring layer.

### Downstream
When MarketVista identifies elevated conditions, the user can route into:

- **RiskWise Planner** for deeper planning
- **TradeIntel 360** for post-trade outcome review

---

## Core dashboard surfaces

The main dashboard includes:

- **Snapshot Freshness**
- **Assets Tracked**
- **Active Alerts**
- **Signals Today**
- **Elevated Signals**
- **Latest Signals**
- **Operational Status**
- **Top Mover**
- **Watchlist Quick View**
- **Line Price History Chart**
- **Candlestick Chart (with Volume)**
- **Live Price Table**
- **Recent OHLC Candles**

These surfaces are designed to answer:

- what changed
- what matters
- whether the data is fresh
- which assets need attention
- where deeper investigation should go next

---

## Signal logic

The project includes signal generation logic for monitoring use cases, including:

- **3-day percentage move**
- **volatility spike detection**
- severity mapping:
  - `INFO`
  - `WATCHLIST`
  - `ELEVATED`

Signals are persisted and surfaced both in the dashboard and Django admin.

---

## Technical highlights

### Backend
- Django
- services-based monitoring logic
- persisted market signals
- seeded demo reset command
- smoke-test baseline
- admin inspection layer for monitoring models

### Frontend
- premium dark SaaS-style dashboard
- monitoring-first layout
- OHLC-backed charts
- watchlist and operational panels
- analyst-oriented card hierarchy

### Data surfaces
- `Asset`
- `PriceSnapshot`
- `PriceOHLC`
- `MarketSignal`
- `WatchlistItem`
- `Alert`

---

## Demo and reviewer workflow

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Apply migrations

```bash
python manage.py migrate
```

### 3. Seed reviewer-ready demo data

```bash
python manage.py seed_demo_data
```

### 4. Run the server

```bash
python manage.py runserver
```

### 5. Open the dashboard

```text
/dashboard/
```

---

## Test and validation commands

### Django checks

```bash
python manage.py check
```

### Run smoke tests

```bash
python manage.py test
```

### Collect static files

```bash
python manage.py collectstatic --noinput
```

---

## What the seeded demo state includes

Running:

```bash
python manage.py seed_demo_data
```

creates a reviewer-ready state with:

- BTC/USD and ETH/USD assets
- historical OHLC rows
- fresh snapshots
- generated market signals
- watchlist items
- dashboard-ready monitoring context

This makes the project easier to review and reset consistently.

---

## Reviewer path

A reviewer can inspect the project in this order:

### 1. Dashboard
Open `/dashboard/` and review:

- freshness
- stat cards
- latest signals
- top mover
- watchlist
- charts
- live price table
- OHLC table

### 2. Admin
Open `/admin/` and inspect:

- Assets
- Price snapshots
- Price ohlcs
- Market signals
- Alerts
- Watchlist items

This shows that the project has an inspectable admin/data layer, not just a styled frontend.

---

## Screenshots

### 1. Full dashboard — hero, signals, and operational workflow
![MarketVista Dashboard — Hero and Signals](docs/screenshots/00_dashboard_full_hero_and_signals.png)

Shows the monitoring-first dashboard identity, hero section, freshness panel, stat cards, latest signals, operational status, and watchlist quick view.

---

### 2. Dashboard charts
![MarketVista Dashboard — Charts](docs/screenshots/01_dashboard_charts.png)

Shows the line history chart and candlestick chart backed by historical OHLC monitoring data.

---

### 3. Dashboard tables
![MarketVista Dashboard — Tables](docs/screenshots/02_dashboard_tables.png)

Shows the live snapshot table and recent OHLC table used for analyst inspection.

---

### 4. Operational and watchlist surfaces
![MarketVista Dashboard — Operational Status and Watchlist](docs/screenshots/03_dashboard_operational_and_watchlist.png)

Shows top-mover context, operational status, and tracked watchlist items.

---

### 5. Admin monitoring index
![MarketVista Admin — Monitoring Models](docs/screenshots/04_admin_monitoring_index.png)

Shows the reviewer-facing admin layer focused on monitoring models only.

---

### 6. Market signals admin
![MarketVista Admin — Market Signals](docs/screenshots/05_admin_market_signals.png)

Shows that signal generation is persisted and inspectable in the database.

---

### 7. Price OHLC admin
![MarketVista Admin — Price OHLC](docs/screenshots/06_admin_price_ohlc.png)

Shows the stored historical market structure backing charting and signal generation.

---

### 8. Price snapshots admin
![MarketVista Admin — Price Snapshots](docs/screenshots/07_admin_price_snapshots.png)

Shows the snapshot layer used for freshness and live table surfaces.

---

## Project structure

```text
marketvista-dashboard/
├── marketvista/
├── monitoring/
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo_data.py
│   ├── migrations/
│   ├── services/
│   ├── static/
│   ├── templates/
│   ├── tests/
│   │   └── test_smoke.py
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── analysis/
├── docs/
└── requirements.txt
```

---

## Documentation

Additional documentation is included under `docs/`:

- `docs/REVIEWER_WALKTHROUGH.md`
- `docs/SCREENSHOT_SHORTLIST.md`
- `docs/PROOF_PACKAGING_CHECKLIST.md`
- `docs/README_INDEX.md`
- `docs/INTERVIEW_TALKING_POINTS.md`

---

## What this project proves

This project demonstrates that I can build a monitoring-first fintech data product with:

- Django application structure
- service-oriented monitoring logic
- persisted market signals
- watchlist workflow
- freshness-aware dashboard design
- chart and table inspection surfaces
- seeded reviewer-ready demo state
- smoke-test baseline and validation workflow

For hiring managers, the strongest proof is that this project is not just a UI mockup. It combines:

- stored market data
- generated signals
- operational monitoring surfaces
- admin inspectability
- repeatable reviewer setup
- automated smoke validation

---

## Best-fit role relevance

This project is most relevant to roles involving:

- Analytics Engineering
- Data Engineering
- FinTech analytics products
- BI / reporting surfaces
- Python / Django data products
- operational monitoring dashboards

---

## Current status

- premium dark dashboard UI completed
- demo seed command completed
- reviewer walkthrough completed
- proof-packaging checklist completed
- smoke-test baseline completed
- screenshot pack completed

---

## One-line summary

MarketVista Dashboard is a monitoring-first analyst console that turns seeded market data into signals, freshness awareness, watchlist visibility, and chart/table inspection surfaces within a broader fintech decision workflow.
