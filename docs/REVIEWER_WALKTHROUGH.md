# MarketVista Dashboard — Reviewer Walkthrough

## Purpose

This walkthrough gives a reviewer, recruiter, or hiring manager a fast path to understand and inspect **MarketVista Dashboard**.

MarketVista is the **monitoring and analyst-visibility layer** in a four-project FinTech data-to-decision portfolio:

```text
DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360
```

MarketVista demonstrates how stored market data can support monitoring, signal review, watchlist visibility, threshold alerts, asset-level inspection, and planned handoff context for deeper risk planning.

---

## Current integration status

| Layer | Status in this repository |
|---|---|
| DataBridge Market API | Planned upstream source, not live integration |
| MarketVista Dashboard | Current project |
| RiskWise Planner | Planned downstream handoff, not live cross-app execution |
| TradeIntel 360 | Planned outcome-review layer, not live cross-app execution |

This repository uses **reviewer-ready seeded demo data**. It does not claim live market-data ingestion, broker execution, or live cross-app integration.

---

## Quick local run

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Optional validation:

```bash
python manage.py check
python manage.py test
```

---

## Recommended 10-minute reviewer route

```text
Home → Dashboard → Signals → Asset Detail → Sparse Intraday View → Watchlist → Alerts → Create Alert → Asset Browser → Django Admin
```

Direct URLs:

```text
/
/dashboard/
/signals/
/assets/ETH%2FUSD/
/watchlist/
/alerts/
/alerts/create/
/assets/
/admin/
```

Asset detail navigation from the UI handles symbols containing `/`. When typing a URL manually, encoded slashes such as `%2F` may be needed depending on the route implementation.

---

## 1. Home — command entry surface

Open:

```text
/
```

Look for:

- MarketVista product identity
- reviewer-ready seeded demo status
- planned suite flow
- Command Entry panel
- main workflow surfaces
- reviewer-ready proof language

What this proves:

- the product role is clear
- MarketVista is not pretending to be the whole suite
- reviewers can quickly understand where to go next

Screenshot:

```text
docs/screenshots/01_home_command_entry.png
```

Optional lower proof screenshot:

```text
docs/screenshots/01b_home_reviewer_proof.png
```

---

## 2. Dashboard — monitoring command surface

Open:

```text
/dashboard/
```

Look for:

- data mode / seeded demo status
- active signals
- active alerts
- top movers
- latest signals
- watchlist quick view
- triggered alerts
- planned suite handoff section

What this proves:

- MarketVista acts as a monitoring command centre
- dashboard context is assembled from stored snapshot, signal, alert, and watchlist data
- user attention is routed toward meaningful review surfaces

Screenshot:

```text
docs/screenshots/02_dashboard_command_surface.png
```

---

## 3. Signals — signal review surface

Open:

```text
/signals/
```

Look for:

- `ELEVATED`, `WATCHLIST`, and `INFO` severity groups
- signal methodology text
- metric values
- planned RiskWise handoff wording
- seeded demo wording

What this proves:

- signals are not just decorative labels
- signal rows show analytical reasoning
- severity is review-oriented, not trade-instruction wording
- MarketVista separates monitoring signals from user-created alerts

Screenshot:

```text
docs/screenshots/03_signals_review_surface.png
```

---

## 4. Asset Detail — asset inspection surface

Open an asset detail page, for example:

```text
/assets/ETH%2FUSD/
```

Or navigate from the Asset Browser.

Look for:

- asset identity and symbol
- current stored price
- 3-day move
- signal state
- watchlist state
- active alert count
- Analyst Workflow panel
- stored price-history chart
- signal history and active alerts
- planned RiskWise handoff

What this proves:

- the product can inspect one asset in context
- asset state combines price, signal, watchlist, chart, and alert evidence
- MarketVista prepares monitoring context for planned deeper planning without claiming live RiskWise execution

Primary screenshot:

```text
docs/screenshots/04_asset_detail_eth_usd.png
```

Optional lower workflow screenshot:

```text
docs/screenshots/04b_asset_detail_workflow_context.png
```

---

## 5. Sparse Intraday View — honest data handling

On Asset Detail, switch to:

```text
1H or 4H
```

Look for:

- sparse sample marker
- limited intraday density message
- `Why this matters`
- `Best use`

What this proves:

- the product does not overclaim dense intraday data
- sparse data is labelled honestly
- reviewers can see data-integrity judgement, not just UI styling

Screenshot:

```text
docs/screenshots/05_asset_detail_sparse_intraday.png
```

---

## 6. Watchlist — priority monitoring surface

Open:

```text
/watchlist/
```

Look for:

- tracked assets count
- elevated-on-watchlist count
- active alerts count
- search/filter controls
- tracked asset registry
- signal state per asset
- export-ready monitoring
- planned suite handoff

What this proves:

- important assets can be kept visible
- watchlist supports analyst follow-up
- watchlist connects naturally to alert review and planned RiskWise preparation

Screenshot:

```text
docs/screenshots/06_watchlist_command_view.png
```

---

## 7. Alerts — alert review console

Open:

```text
/alerts/
```

Look for:

- total alerts
- triggered alerts
- pending alerts
- alert rows
- alert registry
- triggered / pending chips
- current stored price where shown
- workflow explanation
- suggested next moves
- planned RiskWise handoff

Critical consistency check:

```text
Total Alerts = Triggered + Pending = Alert Rows
```

What this proves:

- user-defined threshold alerts are reviewable
- triggered and pending states are separated clearly
- alert state is consistent with visible table rows
- alerts support signal and watchlist review

Screenshot:

```text
docs/screenshots/07_alert_review_console.png
```

---

## 8. Create Alert — threshold setup surface

Open:

```text
/alerts/create/
```

Look for:

- asset selection
- direction selection
- target price
- threshold guidance
- pre-submit review
- monitoring fit panel
- workflow metadata

What this proves:

- alert creation is a monitoring workflow, not just a raw form
- users can convert an asset condition into a reviewable trigger
- copy and layout support analyst discipline

Screenshot:

```text
docs/screenshots/08_create_alert_threshold_setup.png
```

---

## 9. Asset Browser — monitored asset universe

Open:

```text
/assets/
```

Look for:

- crypto, FX, index, and commodity examples
- latest stored prices
- 3-day moves
- signal badges
- watchlist controls
- asset detail links

What this proves:

- the monitored universe is visible
- users can move from asset cards into asset-level inspection
- MarketVista supports multiple asset classes in the seeded demo state

Screenshot:

```text
docs/screenshots/09_asset_browser.png
```

---

## 10. Django Admin — backend model inspectability

Open:

```text
/admin/
```

Look for the Monitoring model group:

- Alerts
- Assets
- Market signals
- Price OHLCs
- Price snapshots
- Watchlist items

What this proves:

- the UI is backed by inspectable Django models
- signal, alert, snapshot, and OHLC data are persisted
- this is more than a styled frontend demo

Screenshot:

```text
docs/screenshots/10_admin_monitoring_models.png
```

---

## Product honesty checks

A reviewer should not see wording that implies live integrations that are not implemented.

Avoid:

```text
DataBridge powers MarketVista
live RiskWise handoff
live TradeIntel handoff
live intraday coverage
trading instruction
```

Prefer:

```text
Reviewer-ready seeded demo data
Planned upstream source: DataBridge Market API
Planned RiskWise handoff
Planned TradeIntel handoff
Stored OHLC / stored snapshot context
```

---

## What to mention in review or interview

Use this concise explanation:

```text
MarketVista is the monitoring layer in my FinTech data-to-decision suite. It turns stored market snapshots and OHLC rows into severity-ranked signals, watchlist visibility, user-defined threshold alerts, and asset-level inspection surfaces. It uses reviewer-ready seeded demo data so the project can be inspected reliably without external market-data credentials.
```

---

## Final reviewer checklist

- [ ] Home explains product and suite role clearly
- [ ] Dashboard shows monitoring command context
- [ ] Signals show methodology and severity
- [ ] Asset Detail combines chart, signal, watchlist, and alert context
- [ ] Sparse intraday view is honest about data density
- [ ] Watchlist keeps priority assets visible
- [ ] Alerts page satisfies `Total Alerts = Triggered + Pending = Alert Rows`
- [ ] Create Alert supports threshold workflow
- [ ] Asset Browser routes into inspection
- [ ] Django Admin exposes backend monitoring models

---

## Final status

```text
Reviewer walkthrough is complete when every page above is inspectable after seed_demo_data.
```
