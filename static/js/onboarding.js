// Onboarding-flow: school en richting → pakket kiezen → nieuw pakket of aanpassen → klaar.
// Alle data loopt via SB (static/js/data.js).
(function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // Vercel laat per serverless-request maar ~4,5 MB door; grotere PDF's zouden daar stranden.
  const MAX_PDF = 4 * 1024 * 1024;

  const state = {
    school: "",
    richting: "",
    gevonden: null,          // {schoolId, richtingId, aantalPakketten} of null
    pakketten: [],
    jaar: null,
    fase: null,
    gekozenId: null,
    vorige: "start",         // waar "Terug" op het nieuw-scherm naartoe gaat
    nieuw: { vakken: [], files: [], kies: {} },
    aanpassen: { pakket: null, uitgezet: new Set(), keuzes: {}, overgeslagen: new Set(), eigen: [] },
  };

  // ---------- schermen ----------
  const STAP = { start: 1, kies: 2, nieuw: 3, aanpassen: 3, status: 4 };
  let huidigScherm = null;
  function toon(naam) {
    const richting = huidigScherm && STAP[naam] < STAP[huidigScherm] ? "in-terug" : "in-vooruit";
    huidigScherm = naam;
    document.querySelectorAll(".screen").forEach((s) => {
      const zichtbaar = s.id === "scr-" + naam;
      s.hidden = !zichtbaar;
      s.classList.remove("in-vooruit", "in-terug");
      if (zichtbaar) { void s.offsetWidth; s.classList.add(richting); }
    });
    const stap = Math.min(STAP[naam], 3);
    document.querySelectorAll("#steps li").forEach((li) => {
      const n = Number(li.dataset.step);
      li.className = n === stap ? "now" : n < stap ? "done" : "";
      if (n === stap) li.setAttribute("aria-current", "step"); else li.removeAttribute("aria-current");
    });
    window.scrollTo(0, 0);
    const kop = document.querySelector("#scr-" + naam + " h1");
    if (kop && naam !== "start") kop.focus({ preventScroll: true });
  }

  function toast(tekst) {
    document.querySelectorAll(".toast").forEach((x) => x.remove());
    const t = document.createElement("div");
    t.className = "toast";
    t.setAttribute("role", "status");
    t.textContent = tekst;
    document.body.appendChild(t);
    setTimeout(() => { t.classList.add("weg"); t.addEventListener("animationend", () => t.remove(), { once: true }); }, 2400);
  }

  // Knop toont een laadanimatie zolang een actie bezig is.
  function bezig(knop, aan) {
    knop.classList.toggle("bezig", aan);
    knop.disabled = aan;
    knop.setAttribute("aria-busy", String(aan));
  }

  function fout(id, tekst) {
    const el = $(id);
    el.textContent = tekst || "";
    el.hidden = !tekst;
  }

  function richtingSub() {
    document.querySelectorAll('[data-veld="richting-sub"]').forEach((el) => {
      el.textContent = state.richting + " · " + state.school;
    });
  }

  // ---------- 1. school en richting ----------
  function koppelSuggesties(input, lijst, zoek, render) {
    let timer;
    const sluit = () => { lijst.hidden = true; input.setAttribute("aria-expanded", "false"); };
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        const q = input.value.trim();
        if (!q) { sluit(); checkGevonden(); return; }
        let items;
        try {
          items = await zoek(q);
        } catch {
          sluit();
          checkGevonden();
          return;
        }
        lijst.innerHTML = items.map((it, i) =>
          `<li role="none"><button type="button" role="option" data-i="${i}">${render(it, q)}</button></li>`).join("");
        lijst.hidden = items.length === 0;
        input.setAttribute("aria-expanded", String(items.length > 0));
        lijst.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
          input.value = items[Number(b.dataset.i)].naam;
          sluit();
          input.dispatchEvent(new Event("change"));
          checkGevonden();
        }));
        checkGevonden();
      }, 120);
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape" || e.key === "Tab") sluit();
      if (e.key === "ArrowDown" && !lijst.hidden) { e.preventDefault(); lijst.querySelector("button").focus(); }
    });
    lijst.addEventListener("keydown", (e) => {
      const knoppen = [...lijst.querySelectorAll("button")];
      const i = knoppen.indexOf(document.activeElement);
      if (e.key === "ArrowDown") { e.preventDefault(); (knoppen[i + 1] || knoppen[0]).focus(); }
      if (e.key === "ArrowUp") { e.preventDefault(); i <= 0 ? input.focus() : knoppen[i - 1].focus(); }
      if (e.key === "Escape") { sluit(); input.focus(); }
      if (e.key === "Tab") sluit();
    });
    document.addEventListener("click", (e) => { if (!input.parentElement.contains(e.target)) sluit(); });

  }

  function markeer(naam, q) {
    const i = naam.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return esc(naam);
    return esc(naam.slice(0, i)) + "<strong>" + esc(naam.slice(i, i + q.length)) + "</strong>" + esc(naam.slice(i + q.length));
  }

  koppelSuggesties($("in-school"), $("sugg-school"), (q) => SB.zoekScholen(q), (s, q) => `<span>${markeer(s.naam, q)}</span>`);
  koppelSuggesties($("in-richting"), $("sugg-richting"), (q) => SB.zoekRichtingen($("in-school").value, q), (r, q) =>
    `<span>${markeer(r.naam, q)}</span><span class="cnt">${r.aantalPakketten} ${r.aantalPakketten === 1 ? "pakket" : "pakketten"}</span>`);

  let checkNr = 0;
  async function checkGevonden() {
    const nr = ++checkNr;
    const school = $("in-school").value.trim();
    const richting = $("in-richting").value.trim();
    const box = $("found");
    const knop = $("btn-start").querySelector("span");
    if (!school || !richting) { box.innerHTML = ""; box.dataset.soort = ""; knop.textContent = "Verder"; state.gevonden = null; return; }
    let res;
    try {
      res = await SB.vindRichting(school, richting);
    } catch {
      if (nr === checkNr) {
        box.innerHTML = '<p class="error">Kan de server niet bereiken. Probeer het zo opnieuw.</p>';
        box.dataset.soort = "";
      }
      return;
    }
    if (nr !== checkNr) return;
    state.gevonden = res;
    const soort = res && res.aantalPakketten > 0 ? "ja-" + res.aantalPakketten : "nee";
    if (box.dataset.soort === soort) return;
    box.dataset.soort = soort;
    if (res && res.aantalPakketten > 0) {
      box.innerHTML = `<div class="found anim-pop">
        <span class="ok" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg></span>
        <div><strong>Gevonden!</strong><span class="small" style="font-weight: 500;">${res.aantalPakketten} ${res.aantalPakketten === 1 ? "pakket" : "pakketten"} van je klasgenoten staan klaar.</span></div>
      </div>`;
      knop.textContent = "Toon mijn pakketten";
    } else {
      box.innerHTML = `<div class="found empty anim-pop">
        <span class="sticker sticker-groen" style="transform: rotate(-4deg);">Nieuw</span>
        <div><strong>Nog geen pakketten</strong><span class="small muted">Jij kan het eerste pakket voor deze richting maken.</span></div>
      </div>`;
      knop.textContent = "Maak het eerste pakket";
    }
  }
  $("in-school").addEventListener("change", checkGevonden);
  $("in-richting").addEventListener("change", checkGevonden);

  $("form-start").addEventListener("submit", async (e) => {
    e.preventDefault();
    const school = $("in-school").value.trim();
    const richting = $("in-richting").value.trim();
    if (!school || !richting) {
      fout("err-start", !school ? "Vul je school in." : "Vul je richting in.");
      (!school ? $("in-school") : $("in-richting")).focus();
      return;
    }
    fout("err-start", "");
    bezig($("btn-start"), true);
    try {
      state.school = school;
      state.richting = richting;
      state.gevonden = await SB.vindRichting(school, richting);
      richtingSub();
      if (state.gevonden && state.gevonden.aantalPakketten > 0) {
        state.pakketten = await SB.haalPakketten(state.gevonden.richtingId);
        state.jaar = state.pakketten[0].academiejaar;
        state.fase = null;
        state.gekozenId = null;
        renderKies();
        toon("kies");
      } else {
        await openNieuw("start");
      }
    } catch (err) {
      fout("err-start", err.message || "Kan de server niet bereiken.");
    } finally {
      bezig($("btn-start"), false);
    }
  });
  ["in-school", "in-richting"].forEach((id) => $(id).addEventListener("input", () => fout("err-start", "")));

  // ---------- hulp: semesters, studiepunten, groepen ----------
  const SEM_VOLGORDE = ["1", "2", "1of2", "jaar"];
  const semNaam = (s) => SB.SEMESTERS[s] || "Semester onbekend";
  const som = (vakken) => vakken.reduce((t, v) => t + (Number(v.sp) || 0), 0);
  const plural = (n, een, meer) => `${n} ${n === 1 ? een : meer}`;
  function afkorting(afst) {
    if (!afst) return "ALG";
    const woorden = afst.split(/\s+/).filter(Boolean);
    return (woorden.length > 1 ? woorden.map((w) => w[0]).join("") : afst.slice(0, 4)).toUpperCase().slice(0, 4);
  }
  function groepUitleg(p, g) {
    const leden = p.vakken.filter((v) => v.groep === g.id);
    if (g.soort === "optie") {
      const opties = [...new Set(leden.map((v) => v.optie))];
      return `${g.naam}: kies ${g.kies} van ${opties.length} (${opties.join(", ")})`;
    }
    return `${g.naam}: kies ${g.kies} van ${leden.length}`;
  }

  // ---------- 2. pakket kiezen ----------
  function renderKies() {
    const jaren = [...new Set(state.pakketten.map((p) => p.academiejaar))];
    $("jaren").innerHTML = jaren.map((j) =>
      `<button type="button" class="pill" aria-pressed="${j === state.jaar}" data-jaar="${esc(j)}">${esc(j)}</button>`).join("");
    $("jaren").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      state.jaar = b.dataset.jaar;
      state.fase = null;
      renderKies();
    }));

    const inJaar = state.pakketten.filter((p) => p.academiejaar === state.jaar);
    const fases = [...new Set(inJaar.map((p) => p.fase))];
    if (!fases.includes(state.fase)) state.fase = fases[0];
    $("fases").innerHTML = fases.map((f) =>
      `<button type="button" class="pill" aria-pressed="${f === state.fase}" data-fase="${esc(f)}">${esc(f)}</button>`).join("");
    $("fases").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      state.fase = b.dataset.fase;
      state.gekozenId = null;
      renderKies();
    }));

    const lijst = inJaar.filter((p) => p.fase === state.fase);
    if (!lijst.some((p) => p.id === state.gekozenId)) state.gekozenId = lijst[0] ? lijst[0].id : null;
    $("pkgs").innerHTML = lijst.map((p) => {
      const nr = (p.fase.match(/\d/) || [p.fase[0]])[0];
      const verplicht = p.vakken.filter((v) => !v.groep);
      const perSem = SEM_VOLGORDE.map((s) => [s, verplicht.filter((v) => v.semester === s).length]).filter(([, n]) => n);
      const fiches = p.vakken.filter((v) => v.fiche).length;
      const titel = p.afstudeerrichting || "Gemeenschappelijk jaar";
      return `<label class="pkg">
        <span class="tile" aria-hidden="true"><b>${esc(nr)}</b><small>${esc(afkorting(p.afstudeerrichting))}</small></span>
        <span class="pkg-body">
          <span class="pkg-title">${esc(titel)}</span>
          <span class="muted small">${esc(p.fase)} · ${plural(p.vakken.length, "vak", "vakken")} · ${plural(fiches, "fiche", "fiches")}</span>
          <span class="pkg-meta">${perSem.map(([s, n]) => `<span class="badge">${esc(s === "1of2" ? "S1 of S2" : s === "jaar" ? "Jaarvak" : "S" + s)}: ${n}</span>`).join("")}
</span>
          ${(p.groepen || []).map((g) => `<span class="small" style="font-weight: 600;">${esc(groepUitleg(p, g))}</span>`).join("")}
          ${p.mogelijkVerouderd
            ? `<span class="warn">! Misschien niet meer up-to-date</span>`
            : `<span class="small" style="font-weight: 600; color: var(--groen-text);">${p.gebruikers || 0} studenten gebruiken dit</span>`}
        </span>
        <input type="radio" name="pakket" value="${esc(p.id)}" ${p.id === state.gekozenId ? "checked" : ""} aria-label="${esc(titel + ", " + p.fase + ", " + p.academiejaar)}">
        <span class="sticker">✓ Nagekeken</span>
      </label>`;
    }).join("");
    $("pkgs").querySelectorAll("input").forEach((r) => r.addEventListener("change", () => { state.gekozenId = r.value; }));
  }

  $("btn-naar-nieuw").addEventListener("click", () => openNieuw("kies"));
  $("btn-kies").addEventListener("click", async () => {
    const p = state.pakketten.find((x) => x.id === state.gekozenId);
    if (!p) return;
    // standaard: in elke groep de eerste keuze(s) aanvinken, de student past aan
    const keuzes = {};
    (p.groepen || []).forEach((g) => {
      const leden = p.vakken.filter((v) => v.groep === g.id);
      const opties = g.soort === "optie" ? [...new Set(leden.map((v) => v.optie))] : leden.map((v) => v.naam);
      keuzes[g.id] = opties.slice(0, g.kies);
    });
    state.aanpassen = { pakket: p, uitgezet: new Set(), keuzes, overgeslagen: new Set(), eigen: [] };
    renderAanpassen();
    toon("aanpassen");
  });

  $("in-eigen-sem").innerHTML = SEM_VOLGORDE.map((s) => `<option value="${s}">${esc(s === "1of2" ? "S1 of S2" : s === "jaar" ? "Jaar" : "Sem " + s)}</option>`).join("");

  // ---------- 3a. nieuw pakket ----------
  async function openNieuw(vanaf) {
    state.vorige = vanaf;
    $("in-ajaar").innerHTML = SB.ACADEMIEJAREN.map((j) => `<option>${esc(j)}</option>`).join("");
    $("in-fase").innerHTML = SB.FASES.map((f) => `<option>${esc(f)}</option>`).join("");
    $("in-vak-sem").innerHTML = SEM_VOLGORDE.map((s) => `<option value="${s}">${esc(semNaam(s))}</option>`).join("");
    let afst = [];
    try {
      afst = state.gevonden ? await SB.haalAfstudeerrichtingen(state.gevonden.richtingId) : [];
    } catch { /* geen suggesties als de server even niet antwoordt */ }
    $("afst-lijst").innerHTML = afst.map((a) => `<option value="${esc(a)}"></option>`).join("");
    if (state.fase) $("in-fase").value = state.fase;
    renderNieuwVakken();
    renderFiles();
    zichtUitleg();
    fout("err-nieuw", "");
    toon("nieuw");
  }

  // keuzevakken worden per semester gegroepeerd, optievakken per optie (samen één groep "Keuzeoptie")
  function groepIdVoor(v) {
    if (v.soort === "keuze") return "keuze-" + v.semester;
    if (v.soort === "optie") return "optie";
    return null;
  }

  function renderNieuwVakken() {
    const box = $("nieuw-vakken");
    const vakken = state.nieuw.vakken;
    if (!vakken.length) {
      box.innerHTML = `<span class="muted small">Nog geen vakken toegevoegd.</span>`;
    } else {
      box.innerHTML = SEM_VOLGORDE.filter((s) => vakken.some((v) => v.semester === s)).map((s) => {
        const inSem = vakken.filter((v) => v.semester === s);
        return `<div class="sem">
          <div class="sem-h"><h2>${esc(semNaam(s))}</h2><span>${som(inSem)} sp</span></div>
          ${inSem.map((v) => {
            const i = vakken.indexOf(v);
            const soort = v.soort === "keuze" ? `<span class="badge groen">Keuzevak</span>`
              : v.soort === "optie" ? `<span class="badge groen">Optie: ${esc(v.optie)}</span>` : "";
            return `<div class="nrow${i === vakken.length - 1 && state.nieuw.netToegevoegd ? " anim-pop" : ""}"><span class="nm">${esc(v.naam)}</span>${soort}<span class="badge">${v.sp} sp</span>
              <button type="button" data-i="${i}" aria-label="Verwijder ${esc(v.naam)}">×</button></div>`;
          }).join("")}
        </div>`;
      }).join("");
      box.querySelectorAll("button[data-i]").forEach((b) => b.addEventListener("click", () => {
        vakken.splice(Number(b.dataset.i), 1);
        renderNieuwVakken();
      }));
    }
    state.nieuw.netToegevoegd = false;
    renderGroepInstellingen();
    renderFiles();
    const opties = [...new Set(vakken.filter((v) => v.soort === "optie").map((v) => v.optie))];
    $("optie-lijst").innerHTML = opties.map((o) => `<option value="${esc(o)}"></option>`).join("");
  }

  // Per groep: hoeveel moet de student kiezen?
  function renderGroepInstellingen() {
    const vakken = state.nieuw.vakken;
    const groepen = {};
    vakken.forEach((v) => {
      const id = groepIdVoor(v);
      if (!id) return;
      groepen[id] = groepen[id] || { id, soort: v.soort, semester: v.semester, leden: new Set() };
      groepen[id].leden.add(v.soort === "optie" ? v.optie : v.naam);
    });
    const lijst = Object.values(groepen);
    $("groep-instellingen").innerHTML = lijst.map((g) => {
      const max = Math.max(1, g.leden.size);
      const huidig = Math.min(state.nieuw.kies[g.id] || 1, max);
      state.nieuw.kies[g.id] = huidig;
      const naam = g.soort === "optie" ? "Keuzeoptie" : `Keuzevakken ${semNaam(g.semester).toLowerCase()}`;
      return `<div class="groep"><div class="groep-h">
        <label for="kies-${esc(g.id)}"><strong>${esc(naam)}</strong><br><span class="muted small">Hoeveel ${g.soort === "optie" ? "opties" : "vakken"} kiest een student? (${g.leden.size} beschikbaar)</span></label>
        <input class="kies-n" id="kies-${esc(g.id)}" type="number" min="1" max="${max}" value="${huidig}" data-groep="${esc(g.id)}">
      </div></div>`;
    }).join("");
    $("groep-instellingen").querySelectorAll("input").forEach((inp) => inp.addEventListener("change", () => {
      const max = Number(inp.max);
      const n = Math.min(Math.max(1, Math.round(Number(inp.value) || 1)), max);
      inp.value = n;
      state.nieuw.kies[inp.dataset.groep] = n;
    }));
  }

  $("in-vak-soort").addEventListener("change", () => {
    $("optie-veld").hidden = $("in-vak-soort").value !== "optie";
  });

  function voegVakToe() {
    const naam = $("in-vak").value.trim();
    if (!naam) { fout("err-nieuw", "Geef het vak een naam."); $("in-vak").focus(); return false; }
    const soort = $("in-vak-soort").value;
    const optie = $("in-vak-optie").value.trim();
    if (soort === "optie" && !optie) { fout("err-nieuw", "Geef de optie een naam, bv. Startup."); $("in-vak-optie").focus(); return false; }
    const sp = Math.round(Number($("in-vak-sp").value));
    if (!(sp >= 1 && sp <= 60)) { fout("err-nieuw", "Studiepunten moeten tussen 1 en 60 liggen."); $("in-vak-sp").focus(); return false; }
    if (state.nieuw.vakken.some((v) => v.naam.toLowerCase() === naam.toLowerCase())) {
      fout("err-nieuw", "Dit vak staat er al in."); $("in-vak").focus(); return false;
    }
    state.nieuw.vakken.push({ naam, semester: $("in-vak-sem").value, sp, soort, optie: soort === "optie" ? optie : null });
    state.nieuw.netToegevoegd = true;
    $("in-vak").value = "";
    fout("err-nieuw", "");
    renderNieuwVakken();
    $("in-vak").focus();
    return true;
  }
  $("btn-vak").addEventListener("click", voegVakToe);
  $("in-vak").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); voegVakToe(); } });
  ["in-vak", "in-vak-optie", "in-vak-sp"].forEach((id) => $(id).addEventListener("input", () => fout("err-nieuw", "")));

  function grootte(b) { return b > 1024 * 1024 ? (b / 1024 / 1024).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " kB"; }

  function voegFilesToe(lijst) {
    const geweigerd = [];
    for (const f of lijst) {
      const isPdf = f.type === "application/pdf" || /\.pdf$/i.test(f.name);
      if (!isPdf || f.size > MAX_PDF) { geweigerd.push(f.name); continue; }
      if (!state.nieuw.files.some((x) => x.name === f.name && x.size === f.size)) state.nieuw.files.push(f);
    }
    renderFiles();
    if (geweigerd.length) toast("Niet toegevoegd (geen PDF of te groot): " + geweigerd.join(", "));
  }

  // Bij welk vak hoort een PDF? Zelf gekozen (f.vak) of automatisch op bestandsnaam.
  const sleutel = (s) => s.toLowerCase().replace(/\.pdf$/, "").replace(/^ects[_ -]?fiche[_ -]?/, "").replace(/[^a-z0-9]/g, "");
  function raadVak(bestandsnaam) {
    const b = sleutel(bestandsnaam);
    if (!b) return null;
    const v = state.nieuw.vakken.find((x) => { const n = sleutel(x.naam); return n && (b.includes(n) || n.includes(b)); });
    return v ? v.naam : null;
  }
  function vakVoorFile(f) {
    if (f.vak !== undefined && (f.vak === "" || state.nieuw.vakken.some((v) => v.naam === f.vak))) return f.vak || null;
    return raadVak(f.name);
  }

  function renderFiles() {
    const vakken = state.nieuw.vakken;
    $("files").innerHTML = state.nieuw.files.map((f, i) => {
      const gekozen = vakVoorFile(f);
      const opties = [`<option value="">${vakken.length ? "— kies het vak —" : "voeg eerst vakken toe"}</option>`]
        .concat(vakken.map((v) => `<option value="${esc(v.naam)}"${v.naam === gekozen ? " selected" : ""}>${esc(v.naam)}</option>`)).join("");
      return `<div class="file${gekozen ? "" : " los"}">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true" style="color: var(--groen-text); flex-shrink: 0;"><path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4"/></svg>
      <span class="nm" title="${esc(f.name)}">${esc(f.name)}<small class="muted">${grootte(f.size)}</small></span>
      <select class="file-vak" data-i="${i}" aria-label="Vak voor ${esc(f.name)}">${opties}</select>
      <button type="button" data-i="${i}" aria-label="Verwijder ${esc(f.name)}">×</button></div>`;
    }).join("");
    $("files").querySelectorAll("select").forEach((sel) => sel.addEventListener("change", () => {
      state.nieuw.files[Number(sel.dataset.i)].vak = sel.value;
      renderFiles();
    }));
    $("files").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      state.nieuw.files.splice(Number(b.dataset.i), 1);
      renderFiles();
    }));
  }

  $("in-pdf").addEventListener("change", (e) => { voegFilesToe(e.target.files); e.target.value = ""; });
  const drop = $("drop");
  ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, () => drop.classList.remove("over")));
  drop.addEventListener("drop", (e) => { e.preventDefault(); voegFilesToe(e.dataTransfer.files); });

  function zicht() { return document.querySelector('input[name="zicht"]:checked').value; }
  function zichtUitleg() {
    $("zicht-uitleg").textContent = zicht() === "publiek"
      ? "Top dat je deelt! Een moderator checkt het pakket eerst, daarna kunnen je klasgenoten het gebruiken."
      : "Alleen jij ziet dit pakket. Je kan het meteen gebruiken.";
    $("btn-nieuw").textContent = zicht() === "publiek" ? "Pakket indienen" : "Pakket opslaan";
  }
  document.querySelectorAll('input[name="zicht"]').forEach((r) => r.addEventListener("change", zichtUitleg));

  $("form-nieuw").addEventListener("submit", async (e) => {
    e.preventDefault();
    if ($("in-vak").value.trim() && !voegVakToe()) return;
    if (!state.nieuw.vakken.length) {
      fout("err-nieuw", "Voeg minstens één vak toe.");
      $("in-vak").focus();
      return;
    }
    const los = state.nieuw.files.filter((f) => !vakVoorFile(f));
    if (los.length) {
      fout("err-nieuw", "Kies bij elke PDF het vak waar hij bij hoort (of verwijder hem): " + los.map((f) => f.name).join(", "));
      return;
    }
    const dubbel = state.nieuw.vakken.find((v) => state.nieuw.files.filter((f) => vakVoorFile(f) === v.naam).length > 1);
    if (dubbel) {
      fout("err-nieuw", `Er zijn meerdere PDF's gekoppeld aan "${dubbel.naam}". Kies er één per vak.`);
      return;
    }
    const knop = $("btn-nieuw");
    bezig(knop, true);
    try {
      const teUploaden = state.nieuw.files;
      const fiches = await SB.uploadFiches(teUploaden);
      const waarschuwingen = fiches.filter((x) => x.waarschuwing).map((x) => `${x.naam}: ${x.waarschuwing}`);
      if (waarschuwingen.length) toast(waarschuwingen.join(" · "));
      const groepen = [];
      const vakken = state.nieuw.vakken.map((v) => {
        const i = teUploaden.findIndex((f) => vakVoorFile(f) === v.naam);
        const f = i >= 0 ? fiches[i] : null;
        const groep = groepIdVoor(v);
        if (groep && !groepen.some((g) => g.id === groep)) {
          groepen.push({
            id: groep, soort: v.soort, kies: state.nieuw.kies[groep] || 1,
            naam: v.soort === "optie" ? "Keuzeoptie" : `Keuzevakken ${semNaam(v.semester).toLowerCase()}`,
          });
        }
        return { naam: v.naam, semester: v.semester, sp: v.sp,
                 fiche: f ? { naam: f.naam, pad: f.pad || null, tekst: f.tekst || undefined } : null, groep, optie: v.optie };
      });
      const pakket = await SB.maakPakket({
        schoolNaam: state.school, richtingNaam: state.richting,
        academiejaar: $("in-ajaar").value, fase: $("in-fase").value, afstudeerrichting: $("in-afst").value,
        vakken, groepen, zichtbaarheid: zicht(),
      });
      klaar();
      if (pakket.status === "in_controle") {
        toon("status");
      } else {
        toast("Pakket opgeslagen");
        setTimeout(() => { location.href = "/"; }, 900);
      }
    } catch (err) {
      fout("err-nieuw", err.message || "Opslaan lukte niet. Probeer opnieuw.");
    } finally {
      bezig(knop, false);
    }
  });

  // ---------- 3b. aanpassen ----------
  // Welke vakken volgt de student nu? (verplicht en niet uitgezet + gekozen keuzevakken/opties + eigen vakken)
  function gevolgdeVakken() {
    const { pakket, uitgezet, keuzes, overgeslagen, eigen } = state.aanpassen;
    return SB.gevolgdeVakken(pakket, { uitgezet: [...uitgezet], keuzes, overgeslagen: [...overgeslagen], eigenVakken: eigen });
  }

  function renderSom() {
    const vakken = gevolgdeVakken();
    $("sp-sum").innerHTML = `<span>Jouw pakket · ${plural(vakken.length, "vak", "vakken")}</span><b>${som(vakken)} sp</b>`;
  }

  function vakRij(v) {
    const { uitgezet } = state.aanpassen;
    return `<label class="vak">
      <span class="dot" aria-hidden="true"></span>
      <span class="nm"><span>${esc(v.naam)}</span><small>${v.sp ? v.sp + " sp" : ""}${v.fiche ? " · ECTS-fiche" : ""}</small></span>
      <input type="checkbox" class="switch" data-vak="${esc(v.naam)}" ${uitgezet.has(v.naam) ? "" : "checked"} aria-label="${esc(v.naam)} volgen">
    </label>`;
  }

  function renderAanpassen() {
    const { pakket, keuzes, eigen } = state.aanpassen;
    const groepen = pakket.groepen || [];
    $("aanpassen-sub").innerHTML = `Gebaseerd op <strong style="color: var(--text);">${esc(pakket.afstudeerrichting || "Gemeenschappelijk")} · ${esc(pakket.fase)} · ${esc(pakket.academiejaar)}</strong>. Zet uit wat je niet volgt en maak je keuzes.`;

    const delen = [];
    // verplichte vakken per semester (+ eigen vakken in dat semester)
    SEM_VOLGORDE.forEach((s) => {
      const verplicht = pakket.vakken.filter((v) => !v.groep && v.semester === s);
      const eigenHier = eigen.map((v, i) => ({ ...v, i })).filter((v) => v.semester === s);
      if (!verplicht.length && !eigenHier.length) return;
      delen.push(`<div class="sem">
        <div class="sem-h"><h2>${esc(semNaam(s))}</h2><span>${som(verplicht) + som(eigenHier)} sp</span></div>
        ${verplicht.map(vakRij).join("")}
        ${eigenHier.map((v) => `<div class="vak eigen">
          <span class="sticker sticker-groen">Eigen vak</span>
          <span class="dot" aria-hidden="true"></span>
          <span class="nm"><span>${esc(v.naam)}</span>${v.sp ? `<small>${v.sp} sp</small>` : ""}</span>
          <button type="button" class="del" data-eigen="${v.i}" aria-label="Verwijder ${esc(v.naam)}">×</button>
        </div>`).join("")}
      </div>`);
    });

    // keuzevakken en keuzeopties
    groepen.forEach((g) => {
      const leden = pakket.vakken.filter((v) => v.groep === g.id);
      const gekozen = keuzes[g.id] || [];
      const uit = state.aanpassen.overgeslagen.has(g.id);
      const type = g.kies === 1 ? "radio" : "checkbox";
      let items;
      if (g.soort === "optie") {
        const opties = [...new Set(leden.map((v) => v.optie))];
        items = opties.map((o) => {
          const vk = leden.filter((v) => v.optie === o);
          const vol = type === "checkbox" && !gekozen.includes(o) && gekozen.length >= g.kies;
          return `<label class="keuze"><input type="${type}" name="g-${esc(g.id)}" value="${esc(o)}" data-groep="${esc(g.id)}" ${gekozen.includes(o) && !uit ? "checked" : ""} ${vol || uit ? "disabled" : ""}>
            <span class="nm">${esc(o)}<small>${vk.map((v) => `${esc(v.naam)} (${v.sp} sp, ${esc(semNaam(v.semester).toLowerCase())})`).join(" · ")}</small></span></label>`;
        });
      } else {
        items = leden.map((v) => {
          const vol = type === "checkbox" && !gekozen.includes(v.naam) && gekozen.length >= g.kies;
          return `<label class="keuze"><input type="${type}" name="g-${esc(g.id)}" value="${esc(v.naam)}" data-groep="${esc(g.id)}" ${gekozen.includes(v.naam) && !uit ? "checked" : ""} ${vol || uit ? "disabled" : ""}>
            <span class="nm">${esc(v.naam)}<small>${v.sp} sp · ${esc(semNaam(v.semester))}${v.fiche ? " · ECTS-fiche" : ""}</small></span></label>`;
        });
      }
      const n = g.soort === "optie" ? new Set(leden.map((v) => v.optie)).size : leden.length;
      delen.push(`<fieldset class="groep${uit ? " uit" : ""}" style="border: 0; margin: 0;">
        <legend class="sr-only">${esc(g.naam)}, kies ${g.kies}</legend>
        <div class="groep-h">
          <span style="display: flex; flex-direction: column; gap: 2px;"><strong>${esc(g.naam)}</strong>
            <span class="small muted">${uit ? "Je volgt deze keuze niet" : `Kies ${g.kies} van ${n}`}</span></span>
          <label class="volg"><span class="small">Volg ik</span>
            <input type="checkbox" class="switch" data-volg="${esc(g.id)}" ${uit ? "" : "checked"} aria-label="${esc(g.naam)} volgen"></label>
        </div>
        ${items.join("")}
      </fieldset>`);
    });

    $("vakken").innerHTML = delen.join("");
    $("vakken").querySelectorAll(".switch[data-vak]").forEach((sw) => sw.addEventListener("change", () => {
      sw.checked ? state.aanpassen.uitgezet.delete(sw.dataset.vak) : state.aanpassen.uitgezet.add(sw.dataset.vak);
      renderSom();
    }));
    $("vakken").querySelectorAll("input[data-groep]").forEach((inp) => inp.addEventListener("change", () => {
      const id = inp.dataset.groep;
      if (inp.type === "radio") keuzes[id] = [inp.value];
      else keuzes[id] = [...$("vakken").querySelectorAll(`input[data-groep="${CSS.escape(id)}"]:checked`)].map((x) => x.value);
      renderAanpassen();
      const terug = $("vakken").querySelector(`input[data-groep="${CSS.escape(id)}"][value="${CSS.escape(inp.value)}"]`);
      if (terug) terug.focus();
    }));
    $("vakken").querySelectorAll("[data-volg]").forEach((sw) => sw.addEventListener("change", () => {
      const id = sw.dataset.volg;
      sw.checked ? state.aanpassen.overgeslagen.delete(id) : state.aanpassen.overgeslagen.add(id);
      renderAanpassen();
      const terug = $("vakken").querySelector(`[data-volg="${CSS.escape(id)}"]`);
      if (terug) terug.focus();
    }));
    $("vakken").querySelectorAll("[data-eigen]").forEach((b) => b.addEventListener("click", (e) => {
      e.preventDefault();
      eigen.splice(Number(b.dataset.eigen), 1);
      renderAanpassen();
    }));
    renderSom();
  }

  function voegEigenToe() {
    const naam = $("in-eigen").value.trim();
    if (!naam) return;
    const bestaat = state.aanpassen.pakket.vakken.some((v) => v.naam.toLowerCase() === naam.toLowerCase())
      || state.aanpassen.eigen.some((v) => v.naam.toLowerCase() === naam.toLowerCase());
    if (bestaat) { toast("Dat vak staat al in je pakket"); return; }
    const sp = Math.min(60, Math.max(0, Math.round(Number($("in-eigen-sp").value) || 0)));
    state.aanpassen.eigen.push({ naam, semester: $("in-eigen-sem").value, sp });
    $("in-eigen").value = "";
    renderAanpassen();
    const nieuw = [...$("vakken").querySelectorAll(".vak.eigen")].find((el) => el.textContent.includes(naam));
    if (nieuw) nieuw.classList.add("anim-pop");
    $("in-eigen").focus();
  }
  $("btn-eigen").addEventListener("click", voegEigenToe);
  $("in-eigen").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); voegEigenToe(); } });

  $("btn-voorstel-open").addEventListener("click", (e) => {
    const open = $("voorstel-form").hidden;
    $("voorstel-form").hidden = !open;
    if (open) { $("voorstel-form").classList.remove("anim-in"); void $("voorstel-form").offsetWidth; $("voorstel-form").classList.add("anim-in"); }
    e.currentTarget.setAttribute("aria-expanded", String(open));
    if (open) $("in-voorstel").focus();
  });
  $("voorstel-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const tekst = $("in-voorstel").value.trim();
    if (tekst.length < 5) { fout("err-voorstel", "Beschrijf kort wat er moet veranderen."); return; }
    fout("err-voorstel", "");
    const knop = e.submitter || $("voorstel-form").querySelector("button");
    bezig(knop, true);
    try {
      await SB.stelWijzigingVoor(state.aanpassen.pakket.id, tekst);
      fout("err-voorstel", "");
      $("in-voorstel").value = "";
      $("voorstel-form").hidden = true;
      $("btn-voorstel-open").setAttribute("aria-expanded", "false");
      toast("Voorstel verstuurd naar de moderators");
    } catch (err) {
      fout("err-voorstel", err.message || "Versturen lukte niet. Probeer opnieuw.");
    } finally {
      bezig(knop, false);
    }
  });
  $("in-voorstel").addEventListener("input", () => fout("err-voorstel", ""));

  $("btn-opslaan").addEventListener("click", async (e) => {
    const { pakket, uitgezet, keuzes, overgeslagen, eigen } = state.aanpassen;
    const onvolledig = (pakket.groepen || []).find((g) => !overgeslagen.has(g.id) && (keuzes[g.id] || []).length !== g.kies);
    if (onvolledig) {
      toast(`Kies nog ${onvolledig.kies - (keuzes[onvolledig.id] || []).length} bij "${onvolledig.naam}"`);
      return;
    }
    const knop = e.currentTarget;
    bezig(knop, true);
    const bewaard = {};
    Object.keys(keuzes).forEach((id) => { bewaard[id] = overgeslagen.has(id) ? [] : keuzes[id]; });
    try {
      await SB.slaMijnPakketOp({ basisPakketId: pakket.id, uitgezet: [...uitgezet], keuzes: bewaard, overgeslagen: [...overgeslagen], eigenVakken: eigen });
      klaar();
      location.href = "/";
    } catch (err) {
      toast(err.message || "Opslaan lukte niet. Probeer opnieuw.");
    } finally {
      bezig(knop, false);
    }
  });

  // ---------- terug ----------
  document.querySelectorAll("[data-terug]").forEach((b) => b.addEventListener("click", () => {
    const doel = b.dataset.terug === "vorige" ? state.vorige : b.dataset.terug;
    toon(doel);
  }));

  function klaar() {
    try { localStorage.setItem("sb-onboarding-klaar", "1"); } catch (e) { /* ok */ }
  }

  // ---------- bestaand pakket hervatten ----------
  async function toonHervat() {
    let info = null;
    try {
      info = await SB.haalMijnPakketVolledig();
    } catch { /* geen hervat-blok als de server even niet antwoordt */ }
    const box = $("hervat");
    if (!info) { box.innerHTML = ""; return; }
    const { pakket, mijn, vakken } = info;
    const status = pakket.status === "in_controle" ? `<span class="badge">In controle</span>`
      : pakket.status === "afgewezen" ? `<span class="badge">Afgewezen${pakket.afwijsReden ? ": " + esc(pakket.afwijsReden) : ""}</span>`
      : pakket.status === "prive" ? `<span class="badge">Privé</span>` : "";
    box.innerHTML = `<div class="hervat anim-in">
      <div style="display: flex; flex-direction: column; gap: 4px;">
        <span class="rowlab">Jouw pakket</span>
        <strong>${esc(pakket.afstudeerrichting || "Gemeenschappelijk")} · ${esc(pakket.fase)}</strong>
        <span class="small muted">${esc(pakket.richtingNaam)} · ${esc(pakket.academiejaar)} · ${vakken.length} vakken · ${som(vakken)} sp</span>
        ${status ? `<span style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">${status}</span>` : ""}
      </div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button class="btn btn-groen btn-sm" type="button" id="btn-hervat">Aanpassen</button>
        <a class="btn btn-ghost btn-sm" href="/">Naar de chat</a>
      </div>
    </div>`;
    $("btn-hervat").addEventListener("click", async (e) => {
      const knop = e.currentTarget;
      bezig(knop, true);
      try {
        state.school = pakket.schoolNaam;
        state.richting = pakket.richtingNaam;
        $("in-school").value = pakket.schoolNaam;
        $("in-richting").value = pakket.richtingNaam;
        state.gevonden = await SB.vindRichting(pakket.schoolNaam, pakket.richtingNaam);
        state.pakketten = state.gevonden ? await SB.haalPakketten(state.gevonden.richtingId) : [];
        state.jaar = pakket.academiejaar;
        state.fase = pakket.fase;
        state.gekozenId = pakket.id;
        richtingSub();
        if (state.pakketten.length) renderKies();
        state.aanpassen = {
          pakket, uitgezet: new Set(mijn.uitgezet || []), keuzes: mijn.keuzes || {},
          overgeslagen: new Set(mijn.overgeslagen || []), eigen: mijn.eigenVakken || [],
        };
        renderAanpassen();
        toon("aanpassen");
      } catch (err) {
        toast(err.message || "Kan je pakket niet laden.");
      } finally {
        bezig(knop, false);
      }
    });
  }

  // ---------- start ----------
  toon("start");
  toonHervat();
})();
