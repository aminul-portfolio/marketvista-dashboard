# MarketVista Dashboard — Documentation Index

## Purpose

This documentation pack supports GitHub reviewers, hiring managers, recruiters, and interview preparation for **MarketVista Dashboard**.

MarketVista is the **monitoring and analyst-visibility layer** in a four-project FinTech portfolio suite:

```text
DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360
```

---

## Core documents

### Main README

```text
README.md
```

Purpose:

- first impression for GitHub
- project summary
- screenshot gallery
- setup commands
- architecture overview
- role relevance
- limitations and future enhancements

Best audience:

```text
Hiring managers · recruiters · technical reviewers
```

---

### Reviewer walkthrough

```text
docs/REVIEWER_WALKTHROUGH.md
```

Purpose:

- gives a reviewer a 10-minute route through the product
- explains what to inspect on each page
- confirms how each surface supports the monitoring workflow
- reinforces product honesty around seeded demo data and planned suite handoffs

Best audience:

```text
Technical reviewers · hiring managers · interviewers
```

---

### Screenshot shortlist

```text
docs/SCREENSHOT_SHORTLIST.md
```

Purpose:

- defines the final screenshot set
- locks filename order
- explains what each screenshot proves
- documents optional proof screenshots
- prevents README image-path drift

Best audience:

```text
You · GitHub packaging reviewer · portfolio maintainer
```

---

### Proof packaging checklist

```text
docs/PROOF_PACKAGING_CHECKLIST.md
```

Purpose:

- final pre-publish checklist
- validation commands
- screenshot checks
- product-honesty checks
- GitHub publish readiness
- recruiter-sharing readiness

Best audience:

```text
You before publishing or sharing the repo
```

---

### Interview talking points

```text
docs/INTERVIEW_TALKING_POINTS.md
```

Purpose:

- explains how to present the project in interviews
- gives concise answers for product, backend, signal, alert, and suite-positioning questions
- highlights the strongest engineering judgement: sparse-data honesty and signal/alert separation

Best audience:

```text
You · interview preparation · recruiter calls
```

---

## Screenshot folder

```text
docs/screenshots/
```

Main README screenshots:

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

Optional proof screenshots:

```text
01b_home_reviewer_proof.png
04b_asset_detail_workflow_context.png
```

---

## Recommended reading order

For a hiring manager:

```text
1. README.md
2. docs/REVIEWER_WALKTHROUGH.md
3. docs/INTERVIEW_TALKING_POINTS.md
```

For final packaging:

```text
1. docs/PROOF_PACKAGING_CHECKLIST.md
2. docs/SCREENSHOT_SHORTLIST.md
3. README.md
```

For interview preparation:

```text
1. docs/INTERVIEW_TALKING_POINTS.md
2. docs/REVIEWER_WALKTHROUGH.md
3. README.md
```

---

## Final documentation QA

Before pushing to GitHub:

- [ ] README screenshot paths match `docs/screenshots/`
- [ ] `SCREENSHOT_SHORTLIST.md` uses the same filenames as README
- [ ] `REVIEWER_WALKTHROUGH.md` uses the same page order as README
- [ ] `PROOF_PACKAGING_CHECKLIST.md` has the current screenshot names
- [ ] `INTERVIEW_TALKING_POINTS.md` does not claim live DataBridge / RiskWise / TradeIntel integration
- [ ] no document uses outdated names such as `Signals Today`, `Live Price Table`, or `DataBridge powers MarketVista`
- [ ] all docs describe the data mode as reviewer-ready seeded demo data

---

## One-line summary

```text
The docs pack is designed to prove MarketVista as a premium, reviewer-ready monitoring layer in a broader FinTech data-to-decision portfolio.
```
