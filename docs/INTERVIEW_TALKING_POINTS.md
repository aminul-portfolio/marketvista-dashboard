
---

# 2) Create `docs/INTERVIEW_TALKING_POINTS.md`

```markdown id="jjj4wq"
# MarketVista Dashboard — Interview Talking Points

## One-paragraph explanation

MarketVista Dashboard is the monitoring and analyst-visibility layer in a broader fintech workflow: DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360. Its role is to help users monitor tracked assets, review generated market signals, inspect data freshness, manage a watchlist, and identify which assets should be routed into deeper planning or later review. I built it as a monitoring-first Django data product rather than a trade journal or risk calculator.

---

## What problem it solves

The project solves the problem of turning raw market data into a usable analyst-monitoring surface.

Instead of only showing prices, it answers:
- what changed
- what matters
- whether the data is current
- which assets deserve attention now
- where deeper investigation should go next

---

## What makes it different from the other fintech projects

### DataBridge Market API
That is the upstream market data source.

### MarketVista Dashboard
This project is the monitoring layer.

### RiskWise Planner
That is for deeper planning and pre-trade analysis.

### TradeIntel 360
That is for post-trade review and trade outcome analysis.

---

## Best “what this proves” points

### Product thinking
I separated the monitoring role clearly from planning and post-trade review so each project proves a distinct part of a fintech workflow.

### Backend design
I moved monitoring logic into a services-based structure instead of scattering logic across templates and views.

### Monitoring logic
The project includes persisted signal generation, including percentage-move and volatility-style monitoring signals with severity levels.

### Analyst workflow
The dashboard is built to surface freshness, elevated conditions, watchlist visibility, and top-mover context before the user goes deeper.

### Reviewer readiness
I added a repeatable seed command so the project can be reset into a clean demo state quickly.

### Engineering credibility
The project includes smoke tests, validation commands, and a CI-ready baseline rather than being only a visual demo.

---

## If asked “what was technically challenging?”

Good answers:
- keeping MarketVista separate from the other fintech products so it stayed monitoring-first
- turning raw data tables into an analyst workflow rather than a generic dashboard
- implementing signal persistence and severity surfaces cleanly
- making the dashboard reviewer-ready with seeded demo data and repeatable validation

---

## If asked “what would you improve next?”

Good answers:
- expand automated test coverage beyond smoke tests
- add stronger CI validation and deployment checks
- introduce multi-environment settings split if preparing for production deployment
- add broader asset coverage and richer monitoring metrics while keeping the monitoring identity clear

---

## If asked “what is the strongest hiring-manager proof here?”

Best answer:
This project proves I can build a Django-based monitoring product that combines persisted data models, service-oriented logic, generated signals, watchlist support, freshness awareness, admin inspectability, seeded reviewer workflows, and a polished analyst-facing dashboard.

---

## Short version for recruiter or interviewer

MarketVista Dashboard is a monitoring-first fintech data product built with Django. It turns seeded market data into signals, freshness tracking, watchlist visibility, top-mover context, and chart/table inspection surfaces, while fitting clearly into a broader DataBridge → MarketVista → RiskWise → TradeIntel workflow.

---

## One-line summary
MarketVista proves monitoring-first product thinking, service-oriented Django design, and reviewer-ready fintech dashboard delivery.