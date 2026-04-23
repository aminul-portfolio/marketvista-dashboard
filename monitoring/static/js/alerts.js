(function () {
  "use strict";

  const ENDPOINTS = {
    triggeredAlerts: "/api/alerts/triggered/",
  };

  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
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

  function updateTriggeredCount(count) {
    qsa("[data-triggered-alert-count]").forEach((node) => {
      node.textContent = String(count);
    });
  }

  async function pollTriggeredAlerts() {
    try {
      const data = await fetchJSON(ENDPOINTS.triggeredAlerts);
      const alerts = data.alerts || [];
      updateTriggeredCount(alerts.length);
    } catch (error) {
      console.error("Alert polling failed:", error);
    }
  }

  function initAlertFiltering(root) {
    const rows = qsa(".mv-alert-item", root);
    const searchInput = qs("#alertSearch", root) || qs("[data-alert-search]", root);
    const statusFilter = qs("#alertStatusFilter", root) || qs("[data-alert-status]", root);
    const emptyMessage = qs("[data-alert-no-results]", root);

    function rowStatus(row) {
      const value = (row.dataset.status || "").toLowerCase();
      if (value) return value;
      return row.textContent.toLowerCase().includes("triggered") ? "triggered" : "pending";
    }

    function applyFilters() {
      const query = (searchInput?.value || "").trim().toLowerCase();
      const status = (statusFilter?.value || "").trim().toLowerCase();

      let visible = 0;

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        const matchesQuery = !query || text.includes(query);
        const matchesStatus = !status || rowStatus(row) === status;
        const show = matchesQuery && matchesStatus;

        row.style.display = show ? "" : "none";
        if (show) visible += 1;
      });

      if (emptyMessage) {
        emptyMessage.hidden = visible !== 0;
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", applyFilters);
    }

    if (statusFilter) {
      statusFilter.addEventListener("change", applyFilters);
    }

    applyFilters();
  }

  function initAlerts() {
    const root = document.querySelector(".mv-alerts-page") || document;
    initAlertFiltering(root);
    pollTriggeredAlerts();
    window.setInterval(pollTriggeredAlerts, 60000);
  }

  document.addEventListener("DOMContentLoaded", initAlerts);
})();