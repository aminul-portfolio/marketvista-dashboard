(function () {
  "use strict";

  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
  }

  function rowSeverity(row) {
    const value = (row.dataset.severity || "").toLowerCase();
    if (value) return value;

    if (row.classList.contains("elevated")) return "elevated";
    if (row.classList.contains("watchlist")) return "watchlist";
    if (row.classList.contains("info")) return "info";
    return "";
  }

  function exportVisibleRows(rows) {
    const visibleRows = rows.filter((row) => row.style.display !== "none");
    if (!visibleRows.length) return;

    const lines = [["Asset", "Price", "Change", "Signals", "Added"]];

    visibleRows.forEach((row) => {
      const cells = Array.from(row.children).map((cell) =>
        (cell.textContent || "").replace(/\s+/g, " ").trim()
      );
      lines.push([
        cells[0] || "",
        cells[1] || "",
        cells[2] || "",
        cells[3] || "",
        cells[4] || "",
      ]);
    });

    const csv = lines.map((line) =>
      line.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(",")
    ).join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "marketvista-watchlist.csv";
    link.click();
    window.URL.revokeObjectURL(url);
  }

  function initWatchlist() {
    const root = document.querySelector(".mv-watchlist-page");
    if (!root) return;

    const rows = qsa(".mv-wl-row", root);
    const searchInput = qs("#watchlistSearch", root) || qs("[data-watchlist-search]", root);
    const severityFilter = qs("#watchlistSeverityFilter", root) || qs("[data-watchlist-severity]", root);
    const exportButton = qs("#watchlistExportBtn", root) || qs("[data-watchlist-export]", root);
    const visibleCount = qs("[data-watchlist-visible-count]", root);
    const emptyMessage = qs("[data-watchlist-no-results]", root);

    function applyFilters() {
      const query = (searchInput?.value || "").trim().toLowerCase();
      const severity = (severityFilter?.value || "").trim().toLowerCase();

      let visible = 0;

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        const matchesQuery = !query || text.includes(query);
        const matchesSeverity = !severity || rowSeverity(row) === severity;
        const show = matchesQuery && matchesSeverity;

        row.style.display = show ? "" : "none";
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

    if (exportButton) {
      exportButton.addEventListener("click", function (event) {
        event.preventDefault();
        exportVisibleRows(rows);
      });
    }

    qsa("[data-watchlist-remove-form]", root).forEach((form) => {
      form.addEventListener("submit", function (event) {
        const ok = window.confirm("Remove this asset from your watchlist?");
        if (!ok) {
          event.preventDefault();
        }
      });
    });

    applyFilters();
  }

  document.addEventListener("DOMContentLoaded", initWatchlist);
})();