document.addEventListener("DOMContentLoaded", () => {
  const filterButtons = document.querySelectorAll("[data-signal-filter]");
  const signalRows = document.querySelectorAll("[data-signal-severity]");
  const visibleCountLabel = document.querySelector("[data-visible-signal-count]");
  const emptyState = document.querySelector("[data-signal-empty-state]");

  function setActiveButton(activeButton) {
    filterButtons.forEach((button) => {
      const isActive = button === activeButton;

      button.classList.toggle("primary", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function updateEmptyState(visibleCount) {
    if (!emptyState) return;

    if (visibleCount === 0) {
      emptyState.hidden = false;
    } else {
      emptyState.hidden = true;
    }
  }

  function updateVisibleCount(visibleCount) {
    if (!visibleCountLabel) return;

    visibleCountLabel.textContent = `${visibleCount} visible`;
  }

  function applyFilter(filterValue) {
    let visibleCount = 0;

    signalRows.forEach((row) => {
      const rowSeverity = row.dataset.signalSeverity;

      const shouldShow =
        filterValue === "all" || rowSeverity === filterValue;

      row.hidden = !shouldShow;

      if (shouldShow) {
        visibleCount += 1;
      }
    });

    updateVisibleCount(visibleCount);
    updateEmptyState(visibleCount);
  }

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const filterValue = button.dataset.signalFilter || "all";

      setActiveButton(button);
      applyFilter(filterValue);
    });
  });

  const defaultButton =
    document.querySelector('[data-signal-filter="all"]') ||
    filterButtons[0];

  if (defaultButton) {
    setActiveButton(defaultButton);
    applyFilter(defaultButton.dataset.signalFilter || "all");
  }
});