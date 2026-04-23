(function () {
  "use strict";

  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
  }

  function formatRelativeTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";

    const diffMs = Date.now() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);

    if (diffMinutes <= 0) return "Just now";
    if (diffMinutes === 1) return "1 min ago";
    if (diffMinutes < 60) return `${diffMinutes} min ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours === 1) return "1 hour ago";
    if (diffHours < 24) return `${diffHours} hours ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return "1 day ago";
    return `${diffDays} days ago`;
  }

  function refreshRelativeTimes() {
    qsa("[data-relative-time]").forEach((node) => {
      const value = node.getAttribute("data-relative-time");
      const formatted = formatRelativeTime(value);
      if (formatted) {
        node.textContent = formatted;
      }
    });
  }

  function initSidebar() {
    const sidebar = qs("#mv-sidebar");
    const overlay = qs("[data-sidebar-overlay]");
    const toggleButton = qs("[data-sidebar-toggle]");

    if (!sidebar || !overlay || !toggleButton) {
      return;
    }

    function setSidebarState(isOpen) {
      sidebar.classList.toggle("is-open", isOpen);
      overlay.classList.toggle("is-open", isOpen);
      toggleButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }

    function closeSidebar() {
      setSidebarState(false);
    }

    function toggleSidebar() {
      setSidebarState(!sidebar.classList.contains("is-open"));
    }

    toggleButton.addEventListener("click", toggleSidebar);
    overlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeSidebar();
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 1080) {
        closeSidebar();
      }
    });
  }

  function init() {
    initSidebar();
    refreshRelativeTimes();
    window.setInterval(refreshRelativeTimes, 60000);
  }

  window.MarketVistaUI = {
    formatRelativeTime,
    refreshRelativeTimes,
  };

  document.addEventListener("DOMContentLoaded", init);
})();