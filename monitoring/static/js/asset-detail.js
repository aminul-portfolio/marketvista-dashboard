(function () {
  "use strict";

  const ENDPOINTS = {
    ohlc: "/api/ohlc/",
  };

  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
  }

  function hasPlotly() {
    return typeof window.Plotly !== "undefined";
  }

  function safeNumber(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function periodToStartDate(period) {
    const today = new Date();
    const map = {
      "7d": 7,
      "30d": 30,
      "90d": 90,
    };
    const days = map[period] || 7;
    const start = new Date(today.getTime() - days * 24 * 60 * 60 * 1000);
    return start.toISOString().split("T")[0];
  }

  async function fetchJSON(url) {
    const response = await fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }

    return response.json();
  }

  function renderFallbackMessage(host, message) {
    if (!host) return;
    host.innerHTML = `
      <div class="mv-empty">
        <div>${message}</div>
      </div>
    `;
  }

  async function renderAssetChart(host, symbol, period, chartType = "line") {
    if (!host || !symbol) return;
    if (!hasPlotly()) {
      renderFallbackMessage(host, "Plotly is not available.");
      return;
    }

    const params = new URLSearchParams({
      symbol,
      start: periodToStartDate(period),
    });

    try {
      const data = await fetchJSON(`${ENDPOINTS.ohlc}?${params.toString()}`);
      const rows = data.ohlc || [];

      if (!rows.length) {
        renderFallbackMessage(host, "No OHLC data available for this asset.");
        return;
      }

      const timestamps = rows.map((item) => new Date(item.timestamp));
      const open = rows.map((item) => safeNumber(item.open));
      const high = rows.map((item) => safeNumber(item.high));
      const low = rows.map((item) => safeNumber(item.low));
      const close = rows.map((item) => safeNumber(item.close));

      const trace =
        chartType === "candlestick"
          ? {
              x: timestamps,
              open,
              high,
              low,
              close,
              type: "candlestick",
              increasing: {
                line: { color: "#22c55e" },
                fillcolor: "#22c55e",
              },
              decreasing: {
                line: { color: "#ef4444" },
                fillcolor: "#ef4444",
              },
              whiskerwidth: 0.3,
              line: { width: 1 },
              showlegend: false,
            }
          : {
              x: timestamps,
              y: close,
              type: "scatter",
              mode: "lines",
              line: { color: "#14b8a6", width: 3 },
              hovertemplate: "%{x}<br>$%{y:.2f}<extra></extra>",
              showlegend: false,
            };

      window.Plotly.newPlot(
        host,
        [trace],
        {
          margin: { t: 24, r: 16, b: 36, l: 48 },
          template: "plotly_dark",
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          xaxis: {
            title: "Time",
            type: "date",
            rangeslider: { visible: false },
          },
          yaxis: {
            title: "Price",
          },
          showlegend: false,
        },
        { responsive: true }
      );
    } catch (error) {
      console.error("Asset detail chart failed:", error);
      renderFallbackMessage(host, "Unable to load asset chart.");
    }
  }

  function initAssetDetail() {
    const root = document.querySelector(".mv-asset-detail-page");
    if (!root) return;

    const chartHost =
      qs("#assetDetailChart", root) ||
      qs("#asset-chart", root) ||
      qs("[data-asset-chart]", root);

    if (!chartHost) return;

    const symbol =
      chartHost.dataset.symbol ||
      qs("[data-asset-symbol]", root)?.dataset.assetSymbol ||
      qs("#assetSymbol", root)?.value ||
      "";

    let currentPeriod = chartHost.dataset.period || "7d";
    const chartType = chartHost.dataset.chartType || "line";

    function rerender() {
      renderAssetChart(chartHost, symbol, currentPeriod, chartType);
    }

    qsa("[data-asset-period]", root).forEach((button) => {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        currentPeriod = this.dataset.assetPeriod || "7d";

        qsa("[data-asset-period]", root).forEach((node) => {
          node.classList.remove("active");
        });
        this.classList.add("active");

        rerender();
      });
    });

    qsa("[data-watchlist-toggle-form]", root).forEach((form) => {
      form.addEventListener("submit", function () {
        const button = this.querySelector("button");
        if (button) {
          button.disabled = true;
          button.textContent = "Updating...";
        }
      });
    });

    rerender();
  }

  document.addEventListener("DOMContentLoaded", initAssetDetail);
})();