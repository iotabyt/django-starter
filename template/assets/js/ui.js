// Close <details class="dropdown"> menus on outside click or Escape. No framework needed.
document.addEventListener("click", (event) => {
  for (const menu of document.querySelectorAll("details.dropdown[open]")) {
    if (!menu.contains(event.target)) menu.removeAttribute("open");
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  for (const menu of document.querySelectorAll("details.dropdown[open]")) {
    menu.removeAttribute("open");
  }
});

// <select data-autosubmit> submits its form on change (e.g. changing a member's role).
document.addEventListener("change", (event) => {
  const select = event.target.closest("select[data-autosubmit]");
  if (select && select.form) select.form.requestSubmit();
});

// <form data-confirm="Remove Kofi?"> asks before submitting.
document.addEventListener("submit", (event) => {
  const message = event.target.dataset?.confirm;
  if (message && !window.confirm(message)) event.preventDefault();
});
