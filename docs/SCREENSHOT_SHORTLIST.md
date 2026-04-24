# MarketVista Dashboard — Screenshot Shortlist

## Purpose

This file defines the final screenshot pack for GitHub, README presentation, and portfolio review.

The screenshots should prove that **MarketVista Dashboard** is a premium, monitoring-first analyst console inside the four-project FinTech workflow:

```text
DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360
```

MarketVista should be shown as the **monitoring and analyst-visibility layer**, not as a live ingestion platform, broker integration, trading bot, risk calculator, or post-trade analytics system.

---

## Screenshot directory

Store all final images in:

```text
docs/screenshots/
```

---

## Final README screenshot set

Use these 10 screenshots in the main README gallery.

### 1. Home — command entry surface

**Filename**

```text
01_home_command_entry.png
```

**What to show**

- MarketVista branding
- sidebar navigation
- seeded demo status
- main `MarketVista Dashboard` hero
- Command Entry panel
- planned suite flow wording

**What it proves**

- product identity is clear
- reviewer can understand the product quickly
- seeded/demo state is labelled honestly
- MarketVista is positioned as one layer in the wider FinTech suite

---

### 2. Dashboard — monitoring command surface

**Filename**

```text
02_dashboard_command_surface.png
```

**What to show**

- monitoring command hero
- data mode
- signal state
- latest context
- tracked assets
- active alerts
- active signals
- top movers
- latest signals
- watchlist quick view
- triggered alerts
- planned suite handoff footer

**What it proves**

- main monitoring workflow is visible in one place
- dashboard summarises stored snapshot, signal, watchlist, and alert state
- page acts as an analyst command surface, not a generic dashboard

---

### 3. Signals — signal review surface

**Filename**

```text
03_signals_review_surface.png
```

**What to show**

- Active monitoring signals hero
- total active signals
- seeded demo data mode
- Elevated / Watchlist / Info cards
- Elevated monitoring state panel
- active signal rows with methodology text and metric values

**What it proves**

- signals are grouped by severity
- signal rows show analytical evidence
- elevated signals are review prompts, not trade instructions
- product keeps system-generated signals separate from user-defined alerts

---

### 4. Asset Detail — ETH/USD inspection surface

**Filename**

```text
04_asset_detail_eth_usd.png
```

**What to show**

- ETH/USD asset inspection hero
- current price
- 3-day move
- signal state
- watchlist badge
- asset alert count
- Analyst Workflow panel
- 1D stored-history chart

**What it proves**

- one asset can be inspected in context
- asset detail combines price, signal, watchlist, alert, and chart evidence
- page prepares context for planned RiskWise handoff without claiming live integration

---

### 5. Asset Detail — sparse intraday handling

**Filename**

```text
05_asset_detail_sparse_intraday.png
```

**What to show**

- 1H or 4H selected range
- labelled sparse sample marker
- limited intraday density notice
- `Why this matters`
- `Best use`

**What it proves**

- sparse data is handled honestly
- the chart does not pretend to show dense real-time intraday coverage
- the product prioritises data integrity over visual overclaiming

---

### 6. Watchlist — priority monitoring surface

**Filename**

```text
06_watchlist_command_view.png
```

**What to show**

- Watchlist command view hero
- tracked assets count
- elevated-on-watchlist count
- active alerts count
- search/filter controls
- tracked asset registry
- export-ready monitoring
- planned suite handoff footer

**What it proves**

- priority assets are kept visible
- watchlist state works as part of the analyst workflow
- watchlist supports alert review and planned risk preparation

---

### 7. Alerts — alert review console

**Filename**

```text
07_alert_review_console.png
```

**What to show**

- Alert review console hero
- total alerts
- triggered alerts
- pending alerts
- alert rows count
- alert registry
- workflow explanation
- suggested next moves
- planned RiskWise handoff footer

**What it proves**

- user-defined threshold alerts are reviewable
- pending and triggered alerts are separated clearly
- alert counts and table status should be mathematically consistent
- alerts pair with signal and watchlist context

**Required consistency rule**

Before capturing this screenshot, verify:

```text
Total Alerts = Triggered + Pending = Alert Rows
```

---

### 8. Create Alert — threshold setup surface

**Filename**

```text
08_create_alert_threshold_setup.png
```

**What to show**

- Create price alert hero
- what-this-does panel
- workflow metadata
- asset select field
- direction selector
- target price field
- threshold guidance
- pre-submit review
- monitoring fit panel

**What it proves**

- user can convert an asset condition into a reviewable alert trigger
- alert creation supports monitoring workflow discipline
- form copy is product-aware, not generic CRUD

---

### 9. Asset Browser — monitored asset universe

**Filename**

```text
09_asset_browser.png
```

**What to show**

- monitored asset universe
- crypto / FX / index / commodity examples
- current prices
- 3-day moves
- signal badges
- watchlist controls
- asset detail links

**What it proves**

- MarketVista covers multiple asset classes in the demo state
- asset cards route users into asset-level inspection
- watched and elevated assets are visible from the browsing layer

---

### 10. Django Admin — monitoring model inspectability

**Filename**

```text
10_admin_monitoring_models.png
```

**What to show**

- Django administration page
- Monitoring model group
- Alerts
- Assets
- Market signals
- Price OHLCs
- Price snapshots
- Watchlist items

**What it proves**

- this is not just a styled frontend
- backend monitoring models are inspectable
- persisted data structures support the UI

---

## Optional proof screenshots

Keep these in `docs/screenshots/`, but do not use them in the main README unless you want a longer gallery.

### Home — reviewer proof section

```text
01b_home_reviewer_proof.png
```

Use this to show the lower Home-page proof area: core surfaces, admin inspectability, monitoring priorities, suite handoff, and reviewer-ready product proof.

### Asset Detail — workflow context

```text
04b_asset_detail_workflow_context.png
```

Use this to show the lower Asset Detail section: signal history, active alerts, and planned RiskWise handoff.

---

## Capture rules

- Use the final seeded demo state.
- Use dark mode.
- Keep browser zoom consistent, preferably `80%` or `90%` for wide SaaS screenshots.
- Capture wide screenshots where possible.
- Avoid active input cursors/carets unless demonstrating search or form entry.
- Avoid accidental text selection.
- Avoid duplicated sticky navbars in long captures.
- Prefer focused screenshots over full-page stitched screenshots.
- Keep the image readable inside GitHub.
- Retake screenshots if count values are inconsistent or misleading.

---

## Pre-capture commands

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Optional validation before capture:

```bash
python manage.py check
python manage.py test
```

---

## Best capture order

```text
01_home_command_entry.png
02_dashboard_command_surface.png
03_signals_review_surface.png
04_asset_detail_eth_usd.png
05_asset_detail_sparse_intraday.png
06_watchlist_command_view.png
07_alert_review_console.png
08_create_alert_threshold_setup.png
09_asset_browser.png
10_admin_monitoring_models.png
```

---

## Final screenshot QA

Before pushing to GitHub, confirm:

- [ ] all screenshot filenames match the README exactly
- [ ] all screenshots are stored in `docs/screenshots/`
- [ ] screenshots load inside GitHub preview
- [ ] Alerts page satisfies `Total Alerts = Triggered + Pending = Alert Rows`
- [ ] no screenshot says live DataBridge, live RiskWise, or live TradeIntel integration
- [ ] sparse intraday screenshot clearly explains limited data density
- [ ] optional screenshots are not required in the main README gallery

---

## Final status

```text
Screenshot pack is ready when the 10 main screenshots load correctly in README.md.
```
