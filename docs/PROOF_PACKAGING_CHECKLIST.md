# MarketVista Dashboard — Proof Packaging Checklist

## Goal

Use this checklist before publishing the project to GitHub, sharing it with recruiters, or pinning it on your profile.

---

## Product and codebase

- [ ] project identity is locked to **MarketVista Dashboard**
- [ ] no misleading overlap remains from earlier project naming
- [ ] legacy files that conflict with the monitoring-only story are removed or renamed
- [ ] dashboard loads correctly with seeded demo data
- [ ] admin monitoring models are visible and inspectable

---

## Validation

- [ ] `python manage.py check` passes
- [ ] `python manage.py migrate` runs cleanly
- [ ] `python manage.py seed_demo_data` works
- [ ] `python manage.py test` passes
- [ ] `python manage.py collectstatic --noinput` completes without concerning issues

---

## Demo state

- [ ] seeded state includes BTC/USD and ETH/USD
- [ ] seeded state includes 50 OHLC rows
- [ ] seeded state includes 2 snapshots
- [ ] seeded state includes 3 signals
- [ ] seeded state includes watchlist entries
- [ ] dashboard surfaces are populated before screenshots

---

## Screenshot pack

- [ ] `00_dashboard_full_hero_and_signals.png`
- [ ] `01_dashboard_charts.png`
- [ ] `02_dashboard_tables.png`
- [ ] `03_dashboard_operational_and_watchlist.png`
- [ ] `04_admin_monitoring_index.png`
- [ ] `05_admin_market_signals.png`
- [ ] `06_admin_price_ohlc.png`
- [ ] `07_admin_price_snapshots.png`

---

## README and docs

- [ ] README reflects the final repo state
- [ ] screenshot paths in README are correct
- [ ] setup commands are accurate
- [ ] project structure tree matches the real repo
- [ ] docs files are present:
  - [ ] `docs/README_INDEX.md`
  - [ ] `docs/REVIEWER_WALKTHROUGH.md`
  - [ ] `docs/INTERVIEW_TALKING_POINTS.md`
  - [ ] `docs/SCREENSHOT_SHORTLIST.md`
  - [ ] `docs/PROOF_PACKAGING_CHECKLIST.md`

---

## GitHub publish readiness

- [ ] repo name is correct
- [ ] About description is filled in
- [ ] topics are added
- [ ] LICENSE file exists
- [ ] no secrets are committed
- [ ] `.env` is ignored
- [ ] only `.env.example` is tracked
- [ ] repo is public if intended for portfolio use

---

## Reviewer experience

- [ ] a reviewer can run 3 core commands quickly:
  - [ ] `python manage.py migrate`
  - [ ] `python manage.py seed_demo_data`
  - [ ] `python manage.py runserver`
- [ ] `/dashboard/` is reviewable immediately
- [ ] `/admin/` is accessible with a superuser
- [ ] signals, snapshots, and OHLC rows are visible in admin

---

## Final release check

- [ ] repo homepage renders the README correctly
- [ ] screenshots load on GitHub
- [ ] docs links open correctly
- [ ] pinned repo order on profile is updated
- [ ] project is ready to share in recruiter outreach or LinkedIn posts

---

## Final status line

```text
Ready to publish when all boxes above are complete.
```
