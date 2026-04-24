# MarketVista Dashboard — Interview Talking Points

## One-paragraph explanation

MarketVista Dashboard is the monitoring and analyst-visibility layer in my broader FinTech data-to-decision portfolio:

```text
DataBridge Market API → MarketVista Dashboard → RiskWise Planner → TradeIntel 360
```

Its role is to help users review stored market snapshots and OHLC history, surface severity-ranked market signals, manage watchlists, review user-defined threshold alerts, and inspect which assets deserve deeper planning in RiskWise. I built it as a monitoring-first Django data product, not as a trading bot, broker integration, risk calculator, or trade journal.

---

## Short recruiter version

MarketVista is a Django-based FinTech monitoring dashboard that turns reviewer-ready seeded market data into signal review, watchlist visibility, threshold alerts, asset inspection, and planned risk-planning handoff context.

---

## One-line version

```text
MarketVista proves monitoring-first product thinking, service-layer Django design, signal/alert separation, and reviewer-ready FinTech dashboard delivery.
```

---

## What problem it solves

Raw market data is not enough for an analyst workflow. A reviewer needs to see:

- what changed
- which assets need attention
- whether data is current or seeded
- which signals are elevated
- which assets are on watchlist
- which threshold alerts are pending or triggered
- where deeper planning should happen next

MarketVista turns stored market data into a structured monitoring surface.

---

## How it fits into the four-project suite

| Project | Role |
|---|---|
| DataBridge Market API | Planned upstream ingestion / ETL layer |
| MarketVista Dashboard | Monitoring, signals, watchlist, alerts, and asset visibility |
| RiskWise Planner | Planned pre-trade risk and scenario-planning layer |
| TradeIntel 360 | Planned post-trade performance and outcome-review layer |

Good interview wording:

```text
I separated the suite into clear layers. DataBridge is the planned upstream data layer, MarketVista is the monitoring and attention-routing layer, RiskWise is the deeper risk-planning layer, and TradeIntel is the post-trade review layer. MarketVista proves the monitoring layer without pretending that the other apps are live integrations inside this repo.
```

---

## What this project proves

### Product thinking

MarketVista has a clear product boundary. It does not try to do ingestion, risk simulation, trading execution, and post-trade analytics in one project. It focuses on monitoring, signals, watchlists, alerts, and asset inspection.

### Backend design

The app uses a service-layer pattern so business logic does not drift into templates. Dashboard context, signal generation, watchlist state, and alert review logic live in service modules.

### Domain modelling

The project separates:

- Asset
- PriceSnapshot
- PriceOHLC
- MarketSignal
- WatchlistItem
- Alert

This separation makes the monitoring workflow easier to inspect, test, and extend.

### Signal logic

Market signals are system-generated from stored OHLC behaviour. They are grouped by severity:

- `ELEVATED`
- `WATCHLIST`
- `INFO`

Signal rows explain methodology, such as percentage movement, volatility baseline, or moving-average crossover context.

### Alert logic

Alerts are user-defined threshold conditions. They are different from system-generated signals. An alert can be pending or triggered depending on the latest stored price snapshot.

### Data integrity

Sparse intraday chart handling is one of the strongest engineering decisions. When the selected time window has sparse stored samples, the UI shows a labelled sparse sample with explanatory copy instead of pretending full live intraday coverage.

### Reviewer readiness

The project uses seeded demo data so a reviewer can run and inspect a stable product state without third-party credentials.

---

## Best hiring-manager proof points

Use these in interview answers:

- clear four-project FinTech suite positioning
- monitoring-first product boundary
- service-layer Django architecture
- persisted market signal records
- signal/alert separation
- watchlist and alert workflows
- honest sparse-data handling
- Django admin inspectability
- reviewer-ready seeded demo state
- premium SaaS-style UI execution
- validation commands and test baseline

---

## If asked: “What is MarketVista?”

Answer:

```text
MarketVista is the monitoring layer in my FinTech portfolio suite. It reviews stored market snapshots and OHLC history, generates and displays market signals, tracks watchlist assets, manages threshold alerts, and prepares asset context for planned deeper risk analysis in RiskWise.
```

---

## If asked: “Is DataBridge connected?”

Answer:

```text
Not live in this repository. DataBridge is the planned upstream source in the wider suite. MarketVista currently uses reviewer-ready seeded demo data so the monitoring workflow can be inspected reliably without external credentials.
```

---

## If asked: “Why not build everything in one app?”

Answer:

```text
I wanted each project to prove a distinct engineering layer. MarketVista is intentionally monitoring-first. DataBridge handles upstream ingestion, RiskWise handles deeper scenario planning, and TradeIntel handles post-trade review. This separation makes the portfolio easier to evaluate and closer to how real systems are often split by responsibility.
```

---

## If asked: “What was technically challenging?”

Strong answer:

```text
The main challenge was keeping the product honest while still making it feel premium. For example, sparse intraday data could easily be displayed as a misleading chart. Instead, I added a sparse-sample state, explanatory copy, and a best-use note so reviewers understand the data limitation clearly.
```

Other good points:

- keeping signals and alerts separate
- preventing dashboard logic from spreading into templates
- making asset-level inspection combine chart, alert, signal, and watchlist context
- ensuring the Alerts page counts match visible triggered/pending rows
- keeping planned suite handoffs honest instead of pretending live cross-app execution

---

## If asked: “How do signals differ from alerts?”

Answer:

```text
Signals are system-generated from market data behaviour, such as percentage movement, volatility expansion, or moving-average context. Alerts are user-defined threshold conditions. Signals explain market behaviour; alerts track exact user-defined price levels.
```

---

## If asked: “What is the strongest engineering decision?”

Answer:

```text
The sparse intraday chart handling. Instead of pretending the seeded data provides dense live intraday coverage, the UI shows a sparse marker and explains why that matters. It demonstrates data-integrity judgement rather than only UI polish.
```

---

## If asked: “What would you improve next?”

Good answer:

```text
The next step would be connecting a real upstream DataBridge ingestion layer, expanding signal test coverage, adding scheduled refresh tasks, and documenting production deployment. I would still keep MarketVista focused on monitoring rather than turning it into a trading or risk-simulation platform.
```

---

## If asked: “What role does this project support?”

Answer:

```text
This project supports my positioning for Analytics Engineer, Data Engineer, FinTech Analytics Engineer, Python/Django Developer, BI Platform Engineer, and data-product roles. It combines data modelling, service-layer logic, dashboard-ready metrics, and business-facing monitoring workflows.
```

---

## Technical explanation in 60 seconds

```text
MarketVista is a Django app with separate models for assets, snapshots, OHLC rows, market signals, watchlist items, and alerts. The views stay thin and call services for market context, signal logic, watchlist state, and alert summaries. The UI presents a monitoring workflow across Dashboard, Signals, Asset Detail, Watchlist, Alerts, Create Alert, and Admin. It uses seeded data for reviewer reliability and labels planned DataBridge, RiskWise, and TradeIntel connections honestly.
```

---

## Technical explanation in 30 seconds

```text
MarketVista is a monitoring-first Django data product. It turns stored market data into signals, watchlist context, alerts, and asset inspection pages. It is part of my four-project FinTech suite and proves service-layer backend design, persisted monitoring records, and premium analyst-facing dashboard delivery.
```

---

## Interview warning: avoid overclaiming

Do not say:

```text
DataBridge is live
RiskWise handoff is live
TradeIntel integration is live
MarketVista has real-time broker execution
MarketVista is a trading bot
```

Say:

```text
planned upstream source
planned suite handoff
reviewer-ready seeded demo data
stored OHLC and snapshot context
monitoring and analyst visibility
```

---

## Final positioning sentence

```text
MarketVista Dashboard demonstrates that I can build a realistic Python/Django data product with clear product boundaries, inspectable data models, service-layer logic, honest data handling, and recruiter-ready FinTech portfolio presentation.
```
