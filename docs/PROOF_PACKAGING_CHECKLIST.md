# MarketVista Dashboard — Proof Packaging Checklist

## Goal

Use this checklist before publishing MarketVista to GitHub, pinning it on your profile, or sharing it with recruiters and hiring managers.

MarketVista should be presented as the **monitoring and analyst-visibility layer** in the four-project FinTech suite:

```text
DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360
```

---

## 1. Product identity

- [ ] Project name is locked to **MarketVista Dashboard**
- [ ] Product role is locked to **monitoring and analyst visibility**
- [ ] README says MarketVista is one of four FinTech projects
- [ ] README clearly separates the four project roles:
  - [ ] DataBridge = planned upstream ingestion / ETL layer
  - [ ] MarketVista = monitoring / signal / watchlist / alert layer
  - [ ] RiskWise = planned pre-trade risk planning layer
  - [ ] TradeIntel = planned post-trade outcome review layer
- [ ] No page claims MarketVista is a trading bot
- [ ] No page claims MarketVista is a broker integration
- [ ] No page claims MarketVista is a full live market-data ingestion service
- [ ] No page claims RiskWise or TradeIntel handoffs are live cross-app execution

---

## 2. Product honesty wording

Search the project for risky wording before publishing.

Avoid:

```text
DataBridge powers MarketVista
Monitoring data powered by DataBridge
live RiskWise handoff
live TradeIntel handoff
live intraday coverage
Signals Today
Live Price Table
```

Prefer:

```text
Reviewer-ready seeded demo data
Planned upstream source: DataBridge Market API
Planned RiskWise handoff
Planned TradeIntel handoff
Stored OHLC
Stored snapshot
Active monitoring signals
```

Checklist:

- [ ] Home page uses reviewer-ready seeded/demo wording
- [ ] Dashboard uses stored snapshot / seeded signal wording
- [ ] Signals page does not imply live signal infrastructure
- [ ] Asset Detail explains sparse intraday data honestly
- [ ] Alerts page uses consistent triggered/pending counts
- [ ] RiskWise and TradeIntel buttons are disabled or clearly planned unless the repos are public and polished
- [ ] README limitations section clearly explains current integration status

---

## 3. Validation commands

Run these before screenshots and before final push:

```bash
python manage.py check
python manage.py migrate
python manage.py seed_demo_data
python manage.py test
```

Optional:

```bash
python manage.py collectstatic --noinput
```

Checklist:

- [ ] `python manage.py check` passes
- [ ] `python manage.py migrate` runs cleanly
- [ ] `python manage.py seed_demo_data` works
- [ ] `python manage.py test` passes
- [ ] `python manage.py collectstatic --noinput` completes without concerning issues

---

## 4. Demo state

After seeding, confirm the app has populated reviewer data.

- [ ] Dashboard loads without error
- [ ] Signals page has active signal rows
- [ ] Asset Browser has multiple asset cards
- [ ] Asset Detail page shows stored price history
- [ ] Sparse 1H/4H view shows honest sparse-sample handling
- [ ] Watchlist page has tracked assets
- [ ] Alerts page has reviewable alert rows
- [ ] Create Alert page loads correctly
- [ ] Django Admin shows Monitoring models

---

## 5. Alerts KPI consistency

Before taking the Alerts screenshot, confirm:

```text
Total Alerts = Triggered + Pending = Alert Rows
```

Checklist:

- [ ] triggered count matches visible `TRIGGERED` rows
- [ ] pending count matches visible `PENDING` rows
- [ ] total alert count equals triggered + pending
- [ ] alert rows count equals visible table rows
- [ ] no screenshot shows `Triggered: 0` while a `TRIGGERED` row is visible

---

## 6. Screenshot pack

Main README screenshots:

- [ ] `docs/screenshots/01_home_command_entry.png`
- [ ] `docs/screenshots/02_dashboard_command_surface.png`
- [ ] `docs/screenshots/03_signals_review_surface.png`
- [ ] `docs/screenshots/04_asset_detail_eth_usd.png`
- [ ] `docs/screenshots/05_asset_detail_sparse_intraday.png`
- [ ] `docs/screenshots/06_watchlist_command_view.png`
- [ ] `docs/screenshots/07_alert_review_console.png`
- [ ] `docs/screenshots/08_create_alert_threshold_setup.png`
- [ ] `docs/screenshots/09_asset_browser.png`
- [ ] `docs/screenshots/10_admin_monitoring_models.png`

Optional proof screenshots:

- [ ] `docs/screenshots/01b_home_reviewer_proof.png`
- [ ] `docs/screenshots/04b_asset_detail_workflow_context.png`

Screenshot quality checklist:

- [ ] no active input cursor/caret unless intentionally shown
- [ ] no accidental text selection
- [ ] screenshot width is readable on GitHub
- [ ] dark SaaS UI is visible clearly
- [ ] sparse intraday screenshot includes explanatory copy
- [ ] admin screenshot shows Monitoring models
- [ ] screenshot filenames match README image paths exactly

---

## 7. README readiness

- [ ] README opens with a clear hiring-manager summary
- [ ] README explains the four-project suite
- [ ] README includes the 10 final screenshots
- [ ] README image paths load on GitHub
- [ ] README has setup commands
- [ ] README has reviewer path
- [ ] README has architecture section
- [ ] README has signal logic section
- [ ] README has alert logic section
- [ ] README has limitations section
- [ ] README has role relevance section
- [ ] README does not overclaim live integrations
- [ ] README does not depend on optional screenshots

---

## 8. Docs pack readiness

Required docs:

- [ ] `docs/README_INDEX.md`
- [ ] `docs/REVIEWER_WALKTHROUGH.md`
- [ ] `docs/INTERVIEW_TALKING_POINTS.md`
- [ ] `docs/SCREENSHOT_SHORTLIST.md`
- [ ] `docs/PROOF_PACKAGING_CHECKLIST.md`

Docs quality:

- [ ] filenames match exactly
- [ ] docs use current screenshot names
- [ ] docs use current reviewer route
- [ ] docs describe DataBridge / RiskWise / TradeIntel as planned suite layers
- [ ] docs do not mention outdated screenshot names
- [ ] docs do not claim live cross-app integration

---

## 9. GitHub publish readiness

- [ ] repository name is correct
- [ ] GitHub About description is filled in
- [ ] repository topics are added
- [ ] LICENSE file exists
- [ ] `.env` is ignored
- [ ] `.env.example` is tracked
- [ ] no secrets are committed
- [ ] no local database is committed unless intentionally documented
- [ ] no `.venv/`, `__pycache__/`, or local cache folders are committed
- [ ] screenshots are committed
- [ ] docs are committed
- [ ] CI workflow is committed if available
- [ ] repository is public if intended for portfolio use

Recommended GitHub topics:

```text
django
python
fintech
analytics-engineering
data-engineering
dashboard
market-data
signals
watchlist
alerts
plotly
portfolio-project
```

---

## 10. Recruiter / hiring-manager readiness

- [ ] README can be understood in under 2 minutes
- [ ] screenshots explain the product without running the project
- [ ] local setup path is clear
- [ ] limitations are honest
- [ ] suite positioning is clear
- [ ] project supports target positioning:

```text
Analytics Engineer | Data Engineer | Python & Django | ETL, KPI Dashboards, FinTech & BI
```

---

## Final release decision

```text
Ready to publish when validation passes, screenshots load, alerts counts are consistent, and README/docs all use the final screenshot names.
```
