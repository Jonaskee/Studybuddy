// Moderatie (human in the loop): publieke pakketten en wijzigingsvoorstellen nakijken
// voor ze online komen. Data via SB (static/js/data.js).
(function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const REDENEN = ["Pakket bestaat al", "Leeg of onvolledig", "Fiches kloppen niet", "Geen echte vakken / spam"];

  let tab = "pakketten";
  let data = { pakketten: [], voorstellen: [] };
  let gekozen = null;

  function toast(tekst) {
    document.querySelectorAll(".toast").forEach((x) => x.remove());
    const t = document.createElement("div");
    t.className = "toast";
    t.setAttribute("role", "status");
    t.textContent = tekst;
    document.body.appendChild(t);
    setTimeout(() => { t.classList.add("weg"); t.addEventListener("animationend", () => t.remove(), { once: true }); }, 2200);
  }

  const SEM_VOLGORDE = ["1", "2", "1of2", "jaar"];
  const afst = (p) => p.afstudeerrichting || "Gemeenschappelijk";
  const som = (vakken) => vakken.reduce((t, v) => t + (Number(v.sp) || 0), 0);

  // Vakken per semester, met keuzevakken en optievakken gemarkeerd.
  function vakkenHtml(p) {
    if (!p.vakken.length) return `<span class="muted">Geen vakken</span>`;
    const groepNaam = (v) => {
      const g = (p.groepen || []).find((x) => x.id === v.groep);
      if (!g) return "";
      return g.soort === "optie" ? `Optie ${v.optie}` : "Keuzevak";
    };
    const semesters = SEM_VOLGORDE.filter((s) => p.vakken.some((v) => v.semester === s));
    const zonder = p.vakken.filter((v) => !SEM_VOLGORDE.includes(v.semester));
    const blok = (titel, vakken) => `<div style="display: flex; flex-direction: column; gap: 8px;">
      <span class="cap">${esc(titel)} · ${som(vakken)} SP</span>
      <div class="chips">${vakken.map((v) => `<span class="chip" style="padding-right: 14px;">${esc(v.naam)}${v.sp ? ` · ${v.sp} sp` : ""}${groepNaam(v) ? ` · <em style="font-style: normal; color: var(--groen-text);">${esc(groepNaam(v))}</em>` : ""}</span>`).join("")}</div>
    </div>`;
    return semesters.map((s) => blok((SB.SEMESTERS[s] || s).toUpperCase(), p.vakken.filter((v) => v.semester === s))).join("")
      + (zonder.length ? blok("ZONDER SEMESTER", zonder) : "");
  }

  function groepenHtml(p) {
    if (!(p.groepen || []).length) return "";
    return `<div style="display: flex; flex-wrap: wrap; gap: 8px;">${p.groepen.map((g) => {
      const leden = p.vakken.filter((v) => v.groep === g.id);
      const n = g.soort === "optie" ? new Set(leden.map((v) => v.optie)).size : leden.length;
      return `<span class="tag">${esc(g.naam)}: kies ${g.kies} van ${n}</span>`;
    }).join("")}</div>`;
  }

  const nummer = (fase) => (String(fase).match(/\d/) || [String(fase)[0] || "?"])[0];

  async function laad() {
    try {
      data = await SB.haalWachtrij();
    } catch (fout) {
      $("count").textContent = "";
      $("queue").innerHTML = "";
      $("detail").innerHTML = `<div class="empty"><span class="sticker">Niet beschikbaar</span>
        <h2>Kan de wachtrij niet laden</h2><p class="muted">${esc(fout.message || "Onbekende fout.")}</p></div>`;
      return;
    }
    const totaal = data.pakketten.length + data.voorstellen.length;
    $("count").textContent = totaal === 1 ? "1 wacht op jou" : `${totaal} wachten op jou`;
    document.querySelector('[data-tab="pakketten"]').textContent = `Nieuwe pakketten · ${data.pakketten.length}`;
    document.querySelector('[data-tab="voorstellen"]').textContent = `Wijzigingsvoorstellen · ${data.voorstellen.length}`;
    const lijst = data[tab];
    if (!lijst.some((x) => x.id === gekozen)) gekozen = lijst[0] ? lijst[0].id : null;
    render();
  }

  function render() {
    const lijst = data[tab];
    $("queue").innerHTML = lijst.map((x) => {
      if (tab === "pakketten") {
        const c = x.checks;
        const vlag = c.leeg ? "Leeg pakket" : c.overlap ? "Mogelijk duplicaat" : "";
        return `<button type="button" class="item" data-id="${esc(x.id)}" aria-current="${x.id === gekozen}">
          <span class="tile" aria-hidden="true">${esc(nummer(x.fase))}</span>
          <span class="body"><span class="t">${esc(afst(x))} · ${esc(x.fase)}</span>
          <span class="muted small">${esc(x.richtingNaam)} · ${esc(x.schoolNaam)} · ${x.vakken.length} vakken · ${som(x.vakken)} sp</span>
          ${vlag ? `<span class="flag">! ${vlag}</span>` : ""}</span></button>`;
      }
      return `<button type="button" class="item" data-id="${esc(x.id)}" aria-current="${x.id === gekozen}">
        <span class="tile" aria-hidden="true">${esc(x.pakket ? nummer(x.pakket.fase) : "?")}</span>
        <span class="body"><span class="t">${esc(x.pakket ? afst(x.pakket) + " · " + x.pakket.fase : "Onbekend pakket")}</span>
        <span class="muted small">Voorstel van ${esc(x.door)} · ${esc(x.op)}</span></span></button>`;
    }).join("");
    $("queue").querySelectorAll(".item").forEach((b) => b.addEventListener("click", () => {
      gekozen = b.dataset.id;
      render();
      if (window.matchMedia("(max-width: 900px)").matches) $("detail").scrollIntoView({ behavior: "smooth", block: "start" });
    }));

    const x = lijst.find((i) => i.id === gekozen);
    if (!x) {
      $("detail").dataset.id = "";
      $("detail").innerHTML = `<div class="empty"><span class="sticker sticker-groen">Alles nagekeken</span>
        <h2>Niets meer in de wachtrij</h2><p class="muted">Nieuwe inzendingen verschijnen hier automatisch.</p></div>`;
      return;
    }
    tab === "pakketten" ? renderPakket(x) : renderVoorstel(x);
    if ($("detail").dataset.id !== x.id) {
      $("detail").dataset.id = x.id;
      $("detail").classList.remove("anim-in"); void $("detail").offsetWidth; $("detail").classList.add("anim-in");
    }
    $("detail").querySelectorAll(".actions .btn").forEach((b) => b.addEventListener("click", () => {
      if (b.id === "nok" && !$("reden").value) return;
      b.classList.add("bezig"); b.setAttribute("aria-busy", "true");
    }));
  }

  function redenSelect() {
    return `<div class="field">
      <label for="reden">Reden bij afwijzen <span style="font-weight: 400;">(de student ziet dit)</span></label>
      <select class="select" id="reden"><option value="">Kies een reden…</option>${REDENEN.map((r) => `<option>${esc(r)}</option>`).join("")}</select>
      <p class="error" id="err-reden" role="alert" hidden></p>
    </div>`;
  }

  function leesReden() {
    const r = $("reden").value;
    if (!r) {
      $("err-reden").textContent = "Kies eerst een reden.";
      $("err-reden").hidden = false;
      $("reden").focus();
      return null;
    }
    return r;
  }

  function renderPakket(p) {
    const c = p.checks;
    const pct = c.overlap ? Math.round((c.overlap.aantal / Math.max(c.overlap.totaal, 1)) * 100) : 0;
    $("detail").innerHTML = `
      <div class="stack" style="display: flex; flex-direction: column; gap: 6px;">
        <h1>${esc(afst(p))} · ${esc(p.fase)}</h1>
        <span class="muted">${esc(p.richtingNaam)} · ${esc(p.schoolNaam)} · ${esc(p.academiejaar)} · ${som(p.vakken)} sp · ingediend door ${esc(p.ingediendDoor || "?")} op ${esc(p.ingediendOp || "?")}</span>
      </div>
      <div class="panel">
        <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap;">
          <span style="font-weight: 700;">Overlap met bestaand pakket</span>
          <span class="display" style="font-size: 24px;">${c.overlap ? `${c.overlap.aantal} / ${c.overlap.totaal} vakken` : "geen"}</span>
        </div>
        <div class="meter" role="img" aria-label="${pct}% overlap"><i style="width: ${pct}%"></i></div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
          ${c.leeg ? `<span class="tag">! Bevat geen vakken</span>` : `<span class="tag ok">✓ Bevat vakken</span>`}
          ${c.fiches.met > 0 ? `<span class="tag ok">✓ ${c.fiches.met} van ${c.fiches.totaal} fiches</span>` : `<span class="tag">! Geen ECTS-fiches</span>`}
          ${c.zonderSemester ? `<span class="tag">! ${c.zonderSemester} vakken zonder semester</span>` : ""}
          ${c.overlap ? `<span class="tag">! Lijkt op ${esc(afst(c.overlap.met))} ${esc(c.overlap.met.fase)} ${esc(c.overlap.met.academiejaar)}</span>` : ""}
        </div>
      </div>
      <div class="cols">
        <div style="display: flex; flex-direction: column; gap: 16px;">
          ${vakkenHtml(p)}
          ${groepenHtml(p)}
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <span class="cap">ECTS-FICHES</span>
          ${p.vakken.filter((v) => v.fiche).map((v) => `<span style="font-weight: 600;">${esc(v.fiche.naam)}</span>`).join("") || `<span class="muted">Geen</span>`}
        </div>
      </div>
      ${redenSelect()}
      <div class="actions">
        <button class="btn btn-groen btn-sm" type="button" id="ok">Goedkeuren</button>
        ${c.overlap ? `<button class="btn btn-ghost btn-sm" type="button" id="merge">Samenvoegen met bestaand</button>` : ""}
        <button class="btn btn-inv btn-sm" type="button" id="nok">Afwijzen</button>
      </div>`;
    $("reden").addEventListener("change", () => { $("err-reden").hidden = true; });
    $("ok").addEventListener("click", async () => {
      try { await SB.keurPakketGoed(p.id); toast("Goedgekeurd: staat nu online"); }
      catch (fout) { toast(fout.message || "Goedkeuren lukte niet."); }
      laad();
    });
    $("nok").addEventListener("click", async () => {
      const r = leesReden(); if (!r) return;
      try { await SB.wijsPakketAf(p.id, r); toast("Afgewezen"); }
      catch (fout) { toast(fout.message || "Afwijzen lukte niet."); }
      laad();
    });
    if (c.overlap) $("merge").addEventListener("click", async () => {
      try {
        const doel = await SB.voegPakketSamen(p.id);
        toast(doel ? `Samengevoegd met ${afst(doel)} ${doel.fase} ${doel.academiejaar}` : "Samenvoegen lukte niet");
      } catch (fout) {
        toast(fout.message || "Samenvoegen lukte niet.");
      }
      laad();
    });
  }

  function renderVoorstel(v) {
    const p = v.pakket;
    $("detail").innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 6px;">
        <h1>Wijziging voor ${esc(p ? afst(p) + " · " + p.fase + " · " + p.academiejaar : "onbekend pakket")}</h1>
        <span class="muted">${esc(p ? p.richtingNaam + " · " + p.schoolNaam : "")} · voorgesteld door ${esc(v.door)} op ${esc(v.op)}</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <span class="cap">VOORSTEL</span>
        <p class="quote">${esc(v.tekst)}</p>
      </div>
      ${p ? `<div style="display: flex; flex-direction: column; gap: 8px;">
        <span class="cap">HUIDIG PAKKET</span>
        ${vakkenHtml(p)}
        ${groepenHtml(p)}
      </div>` : ""}
      ${redenSelect()}
      <div class="actions">
        <button class="btn btn-groen btn-sm" type="button" id="ok">Goedkeuren</button>
        <button class="btn btn-inv btn-sm" type="button" id="nok">Afwijzen</button>
      </div>`;
    $("reden").addEventListener("change", () => { $("err-reden").hidden = true; });
    $("ok").addEventListener("click", async () => {
      try { await SB.keurVoorstelGoed(v.id); toast("Voorstel goedgekeurd"); }
      catch (fout) { toast(fout.message || "Goedkeuren lukte niet."); }
      laad();
    });
    $("nok").addEventListener("click", async () => {
      const r = leesReden(); if (!r) return;
      try { await SB.wijsVoorstelAf(v.id, r); toast("Voorstel afgewezen"); }
      catch (fout) { toast(fout.message || "Afwijzen lukte niet."); }
      laad();
    });
  }

  document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => {
    tab = b.dataset.tab;
    document.querySelectorAll("[data-tab]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    gekozen = null;
    laad();
  }));
  $("reset").addEventListener("click", async () => {
    try {
      await SB.resetDemo();
      gekozen = null;
      toast("Voorbeelddata teruggezet");
    } catch (fout) {
      toast(fout.message || "Resetten lukte niet.");
    }
    laad();
  });

  laad();
})();
