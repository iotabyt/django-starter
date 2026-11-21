// Applies the colour theme before the page paints, so load this in <head> without `defer`.
// A choice made with the toggle ("light" or "dark", kept in localStorage) wins; otherwise the
// page follows the operating system setting, including when it changes.
(() => {
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function stored() {
    try {
      return localStorage.getItem("theme");
    } catch {
      return null;
    }
  }

  function apply() {
    const choice = stored();
    document.documentElement.classList.toggle("dark", choice ? choice === "dark" : media.matches);
  }

  window.toggleTheme = () => {
    const dark = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("theme", dark ? "dark" : "light");
    } catch {
      // Private mode or blocked storage: the choice lasts until the next page load.
    }
  };

  apply();
  media.addEventListener("change", apply);
  window.addEventListener("storage", (event) => event.key === "theme" && apply());
})();
