// Licht/donker-knop. Elke knop met [data-theme-toggle] wisselt het thema.
// De keuze wordt onthouden; zonder keuze volgt de app de instelling van het toestel.
// (Het startthema wordt al in <head> gezet, zodat de pagina niet eerst in het verkeerde thema flitst.)
(function () {
  const KEY = "sb-theme";
  const root = document.documentElement;

  function huidig() {
    return root.dataset.theme === "light" ? "light" : "dark";
  }

  let wisselTimer;
  function zet(thema) {
    root.classList.add("thema-wissel");
    clearTimeout(wisselTimer);
    wisselTimer = setTimeout(() => root.classList.remove("thema-wissel"), 400);
    root.dataset.theme = thema;
    try { localStorage.setItem(KEY, thema); } catch (e) { /* privémodus: niet onthouden */ }
    update();
  }

  function update() {
    const licht = huidig() === "light";
    document.querySelectorAll("[data-theme-toggle]").forEach((knop) => {
      knop.setAttribute("aria-label", licht ? "Schakel naar donkere modus" : "Schakel naar lichte modus");
      knop.title = knop.getAttribute("aria-label");
    });
  }

  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-theme-toggle]")) zet(huidig() === "light" ? "dark" : "light");
  });
  document.addEventListener("DOMContentLoaded", update);
})();
