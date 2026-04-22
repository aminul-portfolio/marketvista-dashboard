document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("mv-sidebar");
  const overlay = document.querySelector("[data-sidebar-overlay]");
  const toggleButton = document.querySelector("[data-sidebar-toggle]");

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
    const isOpen = sidebar.classList.contains("is-open");
    setSidebarState(!isOpen);
  }

  toggleButton.addEventListener("click", toggleSidebar);
  overlay.addEventListener("click", closeSidebar);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeSidebar();
    }
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth > 1080) {
      closeSidebar();
    }
  });
});