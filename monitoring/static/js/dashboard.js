// ===============================
// MarketVista Dashboard Script
// Monitoring-first dashboard behavior
// ===============================

let isMuted = false;
let priceTableInstance = null;
let ohlcTableInstance = null;

const ENDPOINTS = {
  prices: "/api/prices/",
  ohlc: "/api/ohlc/",
  triggeredAlerts: "/api/alerts/triggered/",
};

function qs(id) {
  return document.getElementById(id);
}

function isDarkMode() {
  return document.body.classList.contains("dark-mode");
}

function safeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function updateText(id, value) {
  const el = qs(id);
  if (el) {
    el.textContent = value;
  }
}

function showEmptyState(containerId, message) {
  const el = qs(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="d-flex align-items-center justify-content-center h-100 text-muted small px-3 text-center">
      ${message}
    </div>
  `;
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

  return await response.json();
}

function playAlert(direction) {
  if (isMuted) return;

  const audio = direction === "above" ? qs("soundAbove") : qs("soundBelow");
  const volumeControl = qs("volumeControl");

  if (!audio) return;

  audio.currentTime = 0;
  audio.volume = volumeControl ? parseFloat(volumeControl.value || "0.5") : 0.5;

  audio.play().catch((error) => {
    console.warn("Alert sound play failed:", error);
  });
}

async function pollAlerts() {
  try {
    const data = await fetchJSON(ENDPOINTS.triggeredAlerts);
    const alerts = data.alerts || [];

    if (alerts.length) {
      alerts.forEach((alert) => playAlert(alert.direction));
    }
  } catch (error) {
    console.error("Triggered alert polling failed:", error);
  }
}

function initDataTables() {
  if (!window.jQuery || !$.fn.DataTable) return;

  if (qs("price-table") && !$.fn.DataTable.isDataTable("#price-table")) {
    priceTableInstance = $("#price-table").DataTable({
      pageLength: 10,
      order: [[2, "desc"]],
      responsive: true,
    });
  } else if (qs("price-table")) {
    priceTableInstance = $("#price-table").DataTable();
  }

  if (qs("ohlcTable") && !$.fn.DataTable.isDataTable("#ohlcTable")) {
    ohlcTableInstance = $("#ohlcTable").DataTable({
      pageLength: 10,
      order: [[1, "desc"]],
      responsive: true,
    });
  } else if (qs("ohlcTable")) {
    ohlcTableInstance = $("#ohlcTable").DataTable();
  }
}

function wireTableFilters() {
  const livePriceSymbolFilter = qs("livePriceSymbolFilter");
  const ohlcSymbolFilter = qs("ohlcSymbolFilter");

  if (livePriceSymbolFilter && priceTableInstance) {
    livePriceSymbolFilter.addEventListener("change", function () {
      const selected = this.value;
      priceTableInstance
        .column(0)
        .search(selected ? "^" + selected + "$" : "", true, false)
        .draw();
    });
  }

  if (ohlcSymbolFilter && ohlcTableInstance) {
    ohlcSymbolFilter.addEventListener("change", function () {
      const selected = this.value;
      ohlcTableInstance
        .column(0)
        .search(selected ? "^" + selected + "$" : "", true, false)
        .draw();
    });
  }
}

function renderLivePriceTable(snapshots) {
  if (!qs("price-table")) return;

  if (priceTableInstance) {
    priceTableInstance.clear();

    snapshots.forEach((snapshot) => {
      priceTableInstance.row.add([
        snapshot.symbol,
        `$${safeNumber(snapshot.price).toFixed(2)}`,
        snapshot.timestamp || "—",
      ]);
    });

    priceTableInstance.draw(false);
    return;
  }

  const tbody = qs("price-table").querySelector("tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (!snapshots.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="3" class="text-danger text-center">🚫 No price snapshot data available.</td>
      </tr>
    `;
    return;
  }

  snapshots.forEach((snapshot) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="fw-semibold">${snapshot.symbol}</td>
      <td>$${safeNumber(snapshot.price).toFixed(2)}</td>
      <td class="text-muted">${snapshot.timestamp || "—"}</td>
    `;
    tbody.appendChild(row);
  });
}

async function fetchSnapshotsAndRefreshTable() {
  try {
    const data = await fetchJSON(ENDPOINTS.prices);
    renderLivePriceTable(data.snapshots || []);
  } catch (error) {
    console.error("Snapshot fetch failed:", error);
  }
}

function renderOhlcTable(data, symbol) {
  if (!qs("ohlcTable")) return;

  if (ohlcTableInstance) {
    ohlcTableInstance.clear();

    const rows = data.ohlc || [];
    if (!rows.length) {
      ohlcTableInstance.row.add([
        symbol || "—",
        "—",
        "—",
        "—",
        "—",
        "—",
        "—",
        "—",
      ]);
      ohlcTableInstance.draw(false);
      return;
    }

    rows.forEach((candle) => {
      ohlcTableInstance.row.add([
        symbol || "—",
        new Date(candle.timestamp).toLocaleString(),
        `$${safeNumber(candle.open).toFixed(2)}`,
        `$${safeNumber(candle.high).toFixed(2)}`,
        `$${safeNumber(candle.low).toFixed(2)}`,
        `$${safeNumber(candle.close).toFixed(2)}`,
        safeNumber(candle.volume).toFixed(2),
        "API",
      ]);
    });

    ohlcTableInstance.draw(false);
    return;
  }

  const tbody = qs("ohlcTable").querySelector("tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  const rows = data.ohlc || [];
  if (!rows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-warning">⚠️ No OHLC data available.</td>
      </tr>
    `;
    return;
  }

  rows.forEach((candle) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="fw-semibold">${symbol || "—"}</td>
      <td>${new Date(candle.timestamp).toLocaleString()}</td>
      <td>$${safeNumber(candle.open).toFixed(2)}</td>
      <td>$${safeNumber(candle.high).toFixed(2)}</td>
      <td>$${safeNumber(candle.low).toFixed(2)}</td>
      <td>$${safeNumber(candle.close).toFixed(2)}</td>
      <td>${safeNumber(candle.volume).toFixed(2)}</td>
      <td>API</td>
    `;
    tbody.appendChild(row);
  });
}

async function refreshOhlcTable() {
  const symbol = qs("ohlcSymbolFilter")?.value || qs("candlestickSymbol")?.value;
  if (!symbol) return;

  const url = `${ENDPOINTS.ohlc}?symbol=${encodeURIComponent(symbol)}`;

  try {
    const data = await fetchJSON(url);
    renderOhlcTable(data, symbol);
  } catch (error) {
    console.error("OHLC table refresh failed:", error);
  }
}

async function loadLinePriceHistoryChart(symbol, start = "", end = "") {
  const chartId = "priceHistoryChart";
  const chartEl = qs(chartId);

  if (!chartEl) return;
  if (!symbol) {
    showEmptyState(chartId, "Select an asset to view line-price history.");
    return;
  }

  const params = new URLSearchParams({ symbol });
  if (start) params.append("start", start);
  if (end) params.append("end", end);

  try {
    const data = await fetchJSON(`${ENDPOINTS.ohlc}?${params.toString()}`);
    const rows = data.ohlc || [];

    if (!rows.length) {
      showEmptyState(chartId, "⚠️ No valid OHLC history data.");
      updateText("lineChartLastUpdated", "—");
      return;
    }

    const x = rows.map((item) => new Date(item.timestamp));
    const y = rows.map((item) => safeNumber(item.close));

    Plotly.newPlot(
      chartId,
      [
        {
          x,
          y,
          mode: "lines+markers",
          type: "scatter",
          name: symbol,
          line: { color: "#14b8a6", width: 3 },
          marker: { size: 6 },
          hovertemplate: "%{x}<br>$%{y:.2f}<extra></extra>",
        },
      ],
      {
        title: `${symbol} Close History`,
        margin: { t: 40, r: 20, b: 50, l: 60 },
        template: isDarkMode() ? "plotly_dark" : "plotly_white",
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        yaxis: { title: "Close Price" },
        xaxis: { title: "Time" },
      },
      { responsive: true }
    );

    updateText("lineChartLastUpdated", new Date().toLocaleString());
  } catch (error) {
    console.error("Line chart error:", error);
    showEmptyState(chartId, "⚠️ Unable to load line-price history.");
    updateText("lineChartLastUpdated", "Error");
  }
}

async function loadCandlestickChart(symbol, start = "", end = "") {
  const chartId = "candlestickChart";
  const chartEl = qs(chartId);

  if (!chartEl) return;
  if (!symbol) {
    showEmptyState(chartId, "Select an asset to view OHLC candles.");
    return;
  }

  const params = new URLSearchParams({ symbol });
  if (start) params.append("start", start);
  if (end) params.append("end", end);

  try {
    const data = await fetchJSON(`${ENDPOINTS.ohlc}?${params.toString()}`);
    const ohlc = data.ohlc || [];

    if (!ohlc.length) {
      showEmptyState(chartId, "⚠️ No OHLC data.");
      updateText("candlestickLastUpdated", "—");
      return;
    }

    const timestamps = ohlc.map((item) => new Date(item.timestamp));
    const open = ohlc.map((item) => safeNumber(item.open));
    const high = ohlc.map((item) => safeNumber(item.high));
    const low = ohlc.map((item) => safeNumber(item.low));
    const close = ohlc.map((item) => safeNumber(item.close));
    const volume = ohlc.map((item) => safeNumber(item.volume));

    const traceCandle = {
      x: timestamps,
      open,
      high,
      low,
      close,
      type: "candlestick",
      name: symbol,
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
    };

    const traceVolume = {
      x: timestamps,
      y: volume,
      type: "bar",
      name: "Volume",
      yaxis: "y2",
      marker: { color: "#38bdf8" },
      opacity: 0.24,
      showlegend: false,
    };

    Plotly.newPlot(
      chartId,
      [traceCandle, traceVolume],
      {
        title: `${symbol} Candlestick Chart`,
        template: isDarkMode() ? "plotly_dark" : "plotly_white",
        height: 560,
        margin: { t: 50, b: 60, l: 60, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        xaxis: {
          title: "Time",
          type: "date",
          rangeslider: { visible: false },
          tickangle: -25,
        },
        yaxis: {
          title: "Price",
          domain: [0.30, 1],
          tickprefix: "$",
        },
        yaxis2: {
          title: "Volume",
          domain: [0, 0.22],
          showgrid: true,
        },
        bargap: 0.06,
        showlegend: false,
      },
      { responsive: true }
    );

    updateText("candlestickLastUpdated", new Date().toLocaleString());
  } catch (error) {
    console.error("Candlestick chart error:", error);
    showEmptyState(chartId, "⚠️ Unable to load candlestick data.");
    updateText("candlestickLastUpdated", "Error");
  }
}

function setDefaultDates() {
  const today = new Date();
  const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

  const todayString = today.toISOString().split("T")[0];
  const weekAgoString = weekAgo.toISOString().split("T")[0];

  if (qs("lineStartDate") && !qs("lineStartDate").value) qs("lineStartDate").value = weekAgoString;
  if (qs("lineEndDate") && !qs("lineEndDate").value) qs("lineEndDate").value = todayString;
  if (qs("candleStartDate") && !qs("candleStartDate").value) qs("candleStartDate").value = weekAgoString;
  if (qs("candleEndDate") && !qs("candleEndDate").value) qs("candleEndDate").value = todayString;
}

function initThemeToggle() {
  const themeToggle = qs("themeToggle");
  if (!themeToggle) return;

  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-mode");
    themeToggle.checked = true;
  }

  themeToggle.addEventListener("change", () => {
    document.body.classList.toggle("dark-mode");
    localStorage.setItem("theme", isDarkMode() ? "dark" : "light");

    const lineSymbol = qs("lineChartSymbol")?.value || "";
    const candleSymbol = qs("candlestickSymbol")?.value || "";
    const lineStart = qs("lineStartDate")?.value || "";
    const lineEnd = qs("lineEndDate")?.value || "";
    const candleStart = qs("candleStartDate")?.value || "";
    const candleEnd = qs("candleEndDate")?.value || "";

    if (lineSymbol) loadLinePriceHistoryChart(lineSymbol, lineStart, lineEnd);
    if (candleSymbol) loadCandlestickChart(candleSymbol, candleStart, candleEnd);
  });
}

function initAudioControls() {
  const muteButton = qs("muteButton");
  const volumeControl = qs("volumeControl");
  const testButton = qs("playTestSound");

  if (muteButton) {
    muteButton.addEventListener("click", () => {
      isMuted = !isMuted;
      muteButton.textContent = isMuted ? "🔇 Unmute" : "🔈 Mute";
    });
  }

  if (volumeControl) {
    volumeControl.addEventListener("input", () => {
      ["alertSound", "soundAbove", "soundBelow"].forEach((id) => {
        const audio = qs(id);
        if (audio) {
          audio.volume = parseFloat(volumeControl.value || "0.5");
        }
      });
    });
  }

  if (testButton) {
    testButton.addEventListener("click", () => {
      if (isMuted) return;
      ["soundAbove", "soundBelow"].forEach((id) => {
        const audio = qs(id);
        if (!audio) return;
        audio.currentTime = 0;
        audio.volume = volumeControl ? parseFloat(volumeControl.value || "0.5") : 0.5;
        audio.play().catch((error) => console.warn("Test sound failed:", error));
      });
    });
  }
}

function initChartControls() {
  const lineChartSymbol = qs("lineChartSymbol");
  const candlestickSymbol = qs("candlestickSymbol");
  const timeRange = qs("timeRange");

  if (lineChartSymbol) {
    lineChartSymbol.addEventListener("change", () => {
      loadLinePriceHistoryChart(
        lineChartSymbol.value,
        qs("lineStartDate")?.value || "",
        qs("lineEndDate")?.value || ""
      );
    });
  }

  if (candlestickSymbol) {
    candlestickSymbol.addEventListener("change", () => {
      loadCandlestickChart(
        candlestickSymbol.value,
        qs("candleStartDate")?.value || "",
        qs("candleEndDate")?.value || ""
      );
      refreshOhlcTable();
    });
  }

  if (timeRange) {
    timeRange.addEventListener("change", () => {
      const lineSymbol = lineChartSymbol?.value || "";
      if (lineSymbol) {
        loadLinePriceHistoryChart(lineSymbol, qs("lineStartDate")?.value || "", qs("lineEndDate")?.value || "");
      }
    });
  }
}

function refreshDashboard() {
  fetchSnapshotsAndRefreshTable();
  refreshOhlcTable();
  pollAlerts();

  const lineSymbol = qs("lineChartSymbol")?.value || "";
  const candleSymbol = qs("candlestickSymbol")?.value || "";

  if (lineSymbol) {
    loadLinePriceHistoryChart(
      lineSymbol,
      qs("lineStartDate")?.value || "",
      qs("lineEndDate")?.value || ""
    );
  }

  if (candleSymbol) {
    loadCandlestickChart(
      candleSymbol,
      qs("candleStartDate")?.value || "",
      qs("candleEndDate")?.value || ""
    );
  }
}

function initDashboard() {
  initThemeToggle();
  initAudioControls();
  initDataTables();
  wireTableFilters();
  setDefaultDates();
  initChartControls();

  fetchSnapshotsAndRefreshTable();
  refreshOhlcTable();
  pollAlerts();

  const lineSymbol = qs("lineChartSymbol")?.value || "";
  const candleSymbol = qs("candlestickSymbol")?.value || "";

  if (lineSymbol) {
    loadLinePriceHistoryChart(
      lineSymbol,
      qs("lineStartDate")?.value || "",
      qs("lineEndDate")?.value || ""
    );
  }

  if (candleSymbol) {
    loadCandlestickChart(
      candleSymbol,
      qs("candleStartDate")?.value || "",
      qs("candleEndDate")?.value || ""
    );
  }

  setInterval(refreshDashboard, 30000);
}

window.applyLineChartRange = function () {
  const symbol = qs("lineChartSymbol")?.value || "";
  loadLinePriceHistoryChart(
    symbol,
    qs("lineStartDate")?.value || "",
    qs("lineEndDate")?.value || ""
  );
};

window.applyCandlestickRange = function () {
  const symbol = qs("candlestickSymbol")?.value || "";
  loadCandlestickChart(
    symbol,
    qs("candleStartDate")?.value || "",
    qs("candleEndDate")?.value || ""
  );
  refreshOhlcTable();
};

window.loadLinePriceHistoryChart = loadLinePriceHistoryChart;
window.loadCandlestickChart = loadCandlestickChart;

document.addEventListener("DOMContentLoaded", initDashboard);