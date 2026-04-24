(function () {
  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
  }

  function formatMoney(value, digits = 2) {
    const number = Number(value || 0);
    return `$${number.toLocaleString(undefined, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })}`;
  }

  function formatPercent(value) {
    const number = Number(value || 0);
    const sign = number >= 0 ? "+" : "";
    return `${sign}${number.toFixed(2)}%`;
  }

  function formatDateTimeLabel(value) {
    try {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "Stored OHLC history";

      return date.toLocaleString(undefined, {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (error) {
      return "Stored OHLC history";
    }
  }

  function relativeTimeText(isoString) {
    if (!isoString) return "";

    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return "";

    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

    if (seconds < 60) return "Just now";

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;

    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;

    const months = Math.floor(days / 30);
    return `${months} month${months === 1 ? "" : "s"} ago`;
  }

  function refreshRelativeTimeLabels() {
    qsa("[data-relative-time]").forEach((node) => {
      const value = node.getAttribute("data-relative-time");
      const label = relativeTimeText(value);
      if (label) node.textContent = label;
    });
  }

  function roundToBucket(date, bucketMinutes) {
    const copy = new Date(date);
    copy.setSeconds(0, 0);
    copy.setMinutes(copy.getMinutes() - (copy.getMinutes() % bucketMinutes));
    return copy;
  }

  function bucketRows(rows, bucketMinutes) {
    const buckets = new Map();

    rows.forEach((row) => {
      const bucketDate = roundToBucket(row.timestamp, bucketMinutes);
      const key = bucketDate.toISOString();

      buckets.set(key, {
        timestamp: bucketDate,
        close: row.close,
      });
    });

    return Array.from(buckets.values()).sort((a, b) => a.timestamp - b.timestamp);
  }

  function getPaddedYRange(rows) {
    if (!rows.length) return undefined;

    const values = rows.map((row) => row.close);
    const min = Math.min(...values);
    const max = Math.max(...values);

    if (min === max) {
      const pad = Math.max(Math.abs(max) * 0.035, 1);
      return [min - pad, max + pad];
    }

    const pad = Math.max((max - min) * 0.14, Math.abs(max) * 0.01);
    return [min - pad, max + pad];
  }

  function getPaddedXRange(rows, rangeConfig) {
    if (!rows.length) return undefined;

    if (rows.length === 1) {
      const center = rows[0].timestamp.getTime();
      const halfWindow = Math.max(
        (rangeConfig.windowHours * 60 * 60 * 1000) / 2,
        15 * 60 * 1000
      );

      return [
        new Date(center - halfWindow),
        new Date(center + halfWindow),
      ];
    }

    const first = rows[0].timestamp.getTime();
    const last = rows[rows.length - 1].timestamp.getTime();
    const pad = Math.max((last - first) * 0.12, 10 * 60 * 1000);

    return [
      new Date(first - pad),
      new Date(last + pad),
    ];
  }

  function ensureDensityNote(chartEl) {
    let note = qs("#priceHistoryDensityNote");

    if (!note) {
      note = document.createElement("div");
      note.id = "priceHistoryDensityNote";
      note.className = "mv-ad-chart-density-note";
      note.hidden = true;

      chartEl.insertAdjacentElement("afterend", note);
    }

    return note;
  }

  function setDensityNote(chartEl, message) {
    const note = ensureDensityNote(chartEl);

    if (!message) {
      note.hidden = true;
      note.innerHTML = "";
      return;
    }

    note.hidden = false;
    note.innerHTML = message;
  }

  function getTrendNarrative(stats, rangeKey, state) {
    const { usedFallback, isSparse, usedLatestSnapshot } = state;

    if (!stats) {
      return {
        title: "No usable stored history is available for this asset yet.",
        badge: "Unavailable",
        explainer:
          rangeKey === "1d"
            ? "No stored daily trend history is available for this asset yet."
            : "No stored intraday history is available for this monitoring window yet.",
        why:
          "This limits what the chart can say about the selected monitoring window.",
        use:
          "Store denser OHLC history to make this view more useful for reviewer inspection.",
      };
    }

    if (isSparse) {
      if (rangeKey === "1h") {
        return {
          title: "This 1H view has limited stored intraday samples.",
          badge: "Sparse sample",
          explainer:
            "Showing latest stored snapshot context instead of pretending full one-hour intraday coverage.",
          why:
            "This keeps the page honest while still giving the reviewer useful short-window context.",
          use:
            "Use this as a short-window marker view. Use 1D for the broader stored trend.",
        };
      }

      if (rangeKey === "4h") {
        return {
          title: "This 4H view has limited stored session samples.",
          badge: "Sparse sample",
          explainer:
            "Showing sparse stored OHLC context for the selected session window.",
          why:
            "This prevents a sparse dataset from being displayed as a misleading full intraday chart.",
          use:
            "Use this as session context only. Use 1D when you need a fuller stored trend view.",
        };
      }

      return {
        title: "This view has limited stored samples.",
        badge: "Sparse sample",
        explainer:
          "Showing the available stored points without overclaiming data density.",
        why:
          "Sparse data should be presented as context, not as a complete market feed.",
        use:
          "Use this view alongside signals, alerts, and the broader stored trend.",
      };
    }

    if (usedFallback || usedLatestSnapshot) {
      return {
        title: "This view is using the best available stored history for this asset.",
        badge: "Stored history",
        explainer:
          "Intraday data is limited, so this chart uses the most relevant stored price history available.",
        why:
          "This keeps the page useful while staying honest about what data is currently stored.",
        use:
          "Use this as broader context only. Exact intraday monitoring becomes stronger when denser OHLC history is stored.",
      };
    }

    const changePct = stats.startPrice
      ? ((stats.latestPrice - stats.startPrice) / stats.startPrice) * 100
      : 0;

    if (changePct >= 3) {
      return {
        title: "This asset is showing a strong upward move across the selected window.",
        badge: "Positive trend",
        explainer:
          rangeKey === "1h"
            ? "Intraday marker view showing short-term upside pressure."
            : rangeKey === "4h"
              ? "Session view showing upward movement."
              : "Broader daily view showing a meaningful upward trend.",
        why:
          "This supports continued analyst attention, especially when paired with elevated signals or active thresholds.",
        use:
          "Use this to judge whether signal strength is aligned with stored price direction.",
      };
    }

    if (changePct <= -3) {
      return {
        title: "This asset is weakening across the selected monitoring window.",
        badge: "Negative trend",
        explainer:
          rangeKey === "1h"
            ? "Intraday marker view showing short-term downside pressure."
            : rangeKey === "4h"
              ? "Session view showing weakness."
              : "Broader daily view showing a downward move across the selected period.",
        why:
          "This can strengthen the case for downside-focused alert review or deeper investigation.",
        use:
          "Compare this move against active alerts, thresholds, and signal severity.",
      };
    }

    return {
      title: "This asset is moving in a relatively stable range across the selected window.",
      badge: "Stable range",
      explainer:
        rangeKey === "1h"
          ? "Short-window marker view showing limited directional conviction."
          : rangeKey === "4h"
            ? "Session view showing a relatively balanced range."
            : "Broader daily view showing a controlled range rather than a decisive breakout.",
      why:
        "This helps distinguish noise from genuinely important monitoring conditions.",
      use:
        "Use this before deciding whether an alert level or signal deserves escalation.",
    };
  }

  function renderEmptyChart(chartEl, message) {
    if (typeof Plotly !== "undefined") {
      Plotly.purge(chartEl);
    }

    chartEl.innerHTML = `<div class="mv-ad-history-empty">${message}</div>`;
  }

  async function fetchAssetHistory(symbol) {
    const response = await fetch(
      `/api/ohlc/?symbol=${encodeURIComponent(symbol)}`,
      {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`History request failed with status ${response.status}`);
    }

    const data = await response.json();

    const rows = (data.ohlc || [])
      .map((row) => {
        const timestamp = new Date(row.timestamp);
        const close = Number(row.close);

        if (Number.isNaN(timestamp.getTime()) || !Number.isFinite(close)) {
          return null;
        }

        return {
          timestamp,
          close,
        };
      })
      .filter(Boolean)
      .sort((a, b) => a.timestamp - b.timestamp);

    return {
      rows,
      lastUpdated: data.last_updated || data.server_time || null,
    };
  }

  function buildSeries(allRows, rangeConfig) {
    const end = new Date();
    const start = new Date(end.getTime() - rangeConfig.windowHours * 60 * 60 * 1000);

    let filteredRows = allRows.filter(
      (row) => row.timestamp >= start && row.timestamp <= end
    );

    let usedFallback = false;
    let usedLatestSnapshot = false;
    let isSparse = false;
    let footerLabel = rangeConfig.label;
    let updateSuffix = "Using stored OHLC history";

    if (filteredRows.length) {
      filteredRows = bucketRows(filteredRows, rangeConfig.bucketMinutes);
    }

    if (
      filteredRows.length < rangeConfig.minPoints &&
      rangeConfig.allowFallback &&
      allRows.length >= 2
    ) {
      filteredRows = allRows.slice(-Math.min(rangeConfig.fallbackRows, allRows.length));
      usedFallback = true;
      footerLabel = `${rangeConfig.label} · best available stored history`;
      updateSuffix = "Using best available stored price history";
    }

    if (
      filteredRows.length < rangeConfig.minPoints &&
      !rangeConfig.allowFallback &&
      allRows.length
    ) {
      if (!filteredRows.length) {
        filteredRows = [allRows[allRows.length - 1]];
        usedLatestSnapshot = true;
      }

      isSparse = true;
      footerLabel = `${rangeConfig.label} · sparse stored sample`;
      updateSuffix = "Using sparse stored snapshot context";
    }

    return {
      rows: filteredRows,
      usedFallback,
      usedLatestSnapshot,
      isSparse,
      footerLabel,
      updateSuffix,
    };
  }

  function updateSummary(rows, changeEl, latestEl, highEl, lowEl) {
    if (!rows.length) {
      latestEl.textContent = "—";
      changeEl.textContent = "—";
      highEl.textContent = "—";
      lowEl.textContent = "—";
      changeEl.classList.remove("is-up", "is-down");
      return null;
    }

    const closes = rows.map((row) => row.close);
    const latestPrice = closes[closes.length - 1];
    const startPrice = closes[0];
    const highestPrice = Math.max(...closes);
    const lowestPrice = Math.min(...closes);
    const pctChange = startPrice
      ? ((latestPrice - startPrice) / startPrice) * 100
      : 0;

    latestEl.textContent = formatMoney(latestPrice);
    changeEl.textContent = formatPercent(pctChange);
    highEl.textContent = formatMoney(highestPrice);
    lowEl.textContent = formatMoney(lowestPrice);

    changeEl.classList.remove("is-up", "is-down");
    changeEl.classList.add(pctChange >= 0 ? "is-up" : "is-down");

    return {
      latestPrice,
      startPrice,
      highestPrice,
      lowestPrice,
      pctChange,
    };
  }

  function renderChart(chartEl, rows, rangeConfig, state) {
    const closes = rows.map((row) => row.close);
    const x = rows.map((row) => row.timestamp);
    const latestPrice = closes[closes.length - 1];
    const startPrice = closes[0];
    const isUp = latestPrice >= startPrice;
    const yRange = getPaddedYRange(rows);
    const xRange = state.isSparse ? getPaddedXRange(rows, rangeConfig) : undefined;

    const trace = {
      x,
      y: closes,
      type: "scatter",
      mode: state.isSparse ? "markers" : "lines+markers",
      line: {
        color: isUp ? "#18d1c8" : "#ef6b7a",
        width: state.isSparse ? 0 : 3,
        shape: "spline",
        smoothing: 0.35,
      },
      marker: {
        size: state.isSparse ? 11 : 6,
        color: isUp ? "#18d1c8" : "#ef6b7a",
        line: {
          width: state.isSparse ? 2 : 0,
          color: state.isSparse
            ? "rgba(255, 255, 255, 0.78)"
            : "transparent",
        },
      },
      hovertemplate:
        "<b>%{x|%d %b %Y %H:%M}</b><br>" +
        "Price: <b>$%{y:,.2f}</b><extra></extra>",
    };

    const annotations = [];

    if (state.isSparse) {
      annotations.push({
        text: "Sparse stored sample",
        xref: "paper",
        yref: "paper",
        x: 0.5,
        y: 1.08,
        showarrow: false,
        font: {
          size: 12,
          color: "rgba(253, 230, 138, 0.88)",
        },
      });
    }

    Plotly.newPlot(
      chartEl,
      [trace],
      {
        margin: { t: state.isSparse ? 42 : 22, r: 18, b: 50, l: 62 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: false,
        hovermode: "closest",
        annotations,
        xaxis: {
          range: xRange,
          showgrid: true,
          gridcolor: "rgba(255,255,255,0.08)",
          zeroline: false,
          tickfont: {
            color: "rgba(214, 226, 245, 0.55)",
            size: 11,
          },
        },
        yaxis: {
          range: yRange,
          title: "Price",
          showgrid: true,
          gridcolor: "rgba(255,255,255,0.08)",
          zeroline: false,
          tickprefix: "$",
          tickfont: {
            color: "rgba(214, 226, 245, 0.55)",
            size: 11,
          },
          titlefont: {
            color: "rgba(214, 226, 245, 0.55)",
            size: 12,
          },
        },
      },
      {
        responsive: true,
        displayModeBar: false,
      }
    );
  }

  function initAssetHistoryChart() {
    const chartEl = qs("#priceHistoryChart");
    if (!chartEl || typeof Plotly === "undefined") return;

    const symbol = chartEl.dataset.symbol;
    const tabs = qsa("[data-price-range]");

    const latestEl = qs("#priceHistoryLatest");
    const changeEl = qs("#priceHistoryChange");
    const highEl = qs("#priceHistoryHigh");
    const lowEl = qs("#priceHistoryLow");
    const explainerEl = qs("#priceHistoryExplainer");
    const windowLabelEl = qs("#priceHistoryWindowLabel");
    const updatedLabelEl = qs("#priceHistoryUpdatedLabel");

    const insightTitleEl = qs("#priceHistoryInsightTitle");
    const trendBadgeEl = qs("#priceHistoryTrendBadge");
    const whyTextEl = qs("#priceHistoryWhyText");
    const useTextEl = qs("#priceHistoryUseText");

    const RANGE_CONFIG = {
      "1h": {
        label: "1H · intraday marker view",
        windowHours: 1,
        bucketMinutes: 5,
        minPoints: 4,
        allowFallback: false,
        fallbackRows: 0,
      },
      "4h": {
        label: "4H · session marker view",
        windowHours: 4,
        bucketMinutes: 15,
        minPoints: 4,
        allowFallback: false,
        fallbackRows: 0,
      },
      "1d": {
        label: "1D · broader stored trend",
        windowHours: 24,
        bucketMinutes: 60,
        minPoints: 2,
        allowFallback: true,
        fallbackRows: 45,
      },
    };

    function setActiveTab(rangeKey) {
      tabs.forEach((tab) => {
        const isActive = tab.dataset.priceRange === rangeKey;
        tab.classList.toggle("is-active", isActive);
        tab.setAttribute("aria-pressed", isActive ? "true" : "false");
      });
    }

    function updateNarrative(stats, rangeKey, state) {
      const narrative = getTrendNarrative(stats, rangeKey, state);

      if (explainerEl) explainerEl.textContent = narrative.explainer;
      if (insightTitleEl) insightTitleEl.textContent = narrative.title;
      if (trendBadgeEl) trendBadgeEl.textContent = narrative.badge;
      if (whyTextEl) whyTextEl.textContent = narrative.why;
      if (useTextEl) useTextEl.textContent = narrative.use;
    }

    async function loadRange(rangeKey) {
      const rangeConfig = RANGE_CONFIG[rangeKey];
      if (!rangeConfig) return;

      setActiveTab(rangeKey);

      try {
        const { rows: allRows, lastUpdated } = await fetchAssetHistory(symbol);

        const series = buildSeries(allRows, rangeConfig);
        const stats = updateSummary(
          series.rows,
          changeEl,
          latestEl,
          highEl,
          lowEl
        );

        updateNarrative(stats, rangeKey, series);

        if (!series.rows.length) {
          setDensityNote(chartEl, "");
          renderEmptyChart(
            chartEl,
            rangeKey === "1d"
              ? "No stored daily trend history is available yet for this asset."
              : `No stored intraday history is available yet for ${rangeKey.toUpperCase()}.`
          );
        } else {
          renderChart(chartEl, series.rows, rangeConfig, series);

          if (series.isSparse) {
            setDensityNote(
              chartEl,
              `<strong>Limited intraday density.</strong> Sparse stored sample shown for context. Use 1D for the fuller stored trend.`
            );
          } else {
            setDensityNote(chartEl, "");
          }
        }

        if (windowLabelEl) {
          windowLabelEl.textContent = series.footerLabel;
        }

        if (updatedLabelEl) {
          updatedLabelEl.textContent = lastUpdated
            ? `${series.updateSuffix} · ${formatDateTimeLabel(lastUpdated)}`
            : series.updateSuffix;
        }
      } catch (error) {
        console.error("Failed to load asset history:", error);

        setDensityNote(chartEl, "");
        renderEmptyChart(
          chartEl,
          "Unable to load price history for this asset right now."
        );

        if (windowLabelEl) {
          windowLabelEl.textContent = rangeConfig.label;
        }

        if (updatedLabelEl) {
          updatedLabelEl.textContent = "History load failed";
        }
      }
    }

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        loadRange(tab.dataset.priceRange);
      });
    });

    loadRange("1d");
  }

  refreshRelativeTimeLabels();
  setInterval(refreshRelativeTimeLabels, 60000);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAssetHistoryChart);
  } else {
    initAssetHistoryChart();
  }
})();