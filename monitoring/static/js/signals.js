(function () {
  "use strict";

  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
  }

  function signalSeverity(card) {
    const value = (card.dataset.severity || "").toLowerCase();
    if (value) return value;

    if (card.classList.contains("elevated")) return "elevated";
    if (card.classList.contains("watchlist")) return "watchlist";
    if (card.classList.contains("info")) return "info";
    return "";
  }

  function initSignalsPage() {
    const root = document.querySelector(".mv-signals-page");
    if (!root) return;

    const cards = qsa(".mv-sig-card", root);
    const searchInput = qs("#signalSearch", root) || qs("[data-signal-search]", root);
    const severityFilter = qs("#signalSeverityFilter", root) || qs("[data-signal-severity]", root);
    const visibleCount = qs("[data-signal-visible-count]", root);
    const emptyMessage = qs("[data-signal-no-results]", root);

    function applyFilters() {
      const query = (searchInput?.value || "").trim().toLowerCase();
      const severity = (severityFilter?.value || "").trim().toLowerCase();

      let visible = 0;

      cards.forEach((card) => {
        const text = card.textContent.toLowerCase();
        const matchesQuery = !query || text.includes(query);
        const matchesSeverity = !severity || signalSeverity(card) === severity;
        const show = matchesQuery && matchesSeverity;

        card.style.display = show ? "" : "none";
        if (show) visible += 1;
      });

      if (visibleCount) {
        visibleCount.textContent = String(visible);
      }

      if (emptyMessage) {
        emptyMessage.hidden = visible !== 0;
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", applyFilters);
    }

    if (severityFilter) {
      severityFilter.addEventListener("change", applyFilters);
    }

    applyFilters();
  }

  document.addEventListener("DOMContentLoaded", initSignalsPage);
})();