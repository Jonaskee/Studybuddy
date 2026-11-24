// StudieBuddy – datalaag.
//
// Alle data (scholen, pakketten, mijn pakket, moderatie) komt van de backend:
// /api/data/... (zie data_api.py). De opslag daarachter is Supabase of, lokaal
// zonder Supabase-keys, een JSON-bestand. De schermen roepen enkel de functies
// hieronder aan en merken niet welke opslag erachter zit.

const SB = (() => {
  const FASES = ["1e bachelor", "2e bachelor", "3e bachelor", "Schakeljaar", "Master"];
  const ACADEMIEJAREN = ["2026-2027", "2025-2026"];
  // Wanneer een vak loopt. "1of2" = je kiest zelf (bv. stage), "jaar" = over het hele academiejaar.
  const SEMESTERS = { "1": "Semester 1", "2": "Semester 2", "1of2": "Semester 1 of 2", "jaar": "Hele academiejaar" };

  async function api(pad, opties = {}) {
    let antwoord;
    try {
      antwoord = await fetch("/api/data" + pad, {
        credentials: "same-origin",
        headers: opties.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
        ...opties,
      });
    } catch {
      throw new Error("Kan de server niet bereiken.");
    }
    let data = null;
    try { data = await antwoord.json(); } catch { /* leeg of geen JSON */ }
    if (!antwoord.ok) {
      const fout = new Error((data && data.fout) || `De server gaf fout ${antwoord.status}.`);
      fout.status = antwoord.status;
      throw fout;
    }
    return data;
  }

  const query = (params) => "?" + new URLSearchParams(params).toString();

  return {
    FASES,
    ACADEMIEJAREN,
    SEMESTERS,

    /** Afstudeerrichtingen die al bestaan voor een richting. → ["Artificiële Intelligentie", …] */
    haalAfstudeerrichtingen: (richtingId) =>
      api("/afstudeerrichtingen" + query({ richtingId })),

    /** Scholen waarvan de naam q bevat. → [{id, naam}] */
    zoekScholen: (q) => api("/scholen" + query({ q: q || "" })),

    /** Richtingen van een school (op naam) die q bevatten. → [{id, naam, aantalPakketten}] */
    zoekRichtingen: (schoolNaam, q) =>
      api("/richtingen" + query({ school: schoolNaam || "", q: q || "" })),

    /** Zit deze school + richting al in de data? → {schoolId, richtingId, aantalPakketten} of null */
    vindRichting: (schoolNaam, richtingNaam) =>
      api("/vind-richting" + query({ school: schoolNaam || "", richting: richtingNaam || "" })),

    /** Publieke (nagekeken) pakketten van een richting, nieuwste jaar eerst. */
    haalPakketten: (richtingId) => api("/pakketten" + query({ richtingId })),

    haalPakket: (id) => api("/pakket/" + encodeURIComponent(id)),

    /** PDF's uploaden. Eén request per bestand (Vercel staat max. ~4,5 MB per request toe). → [{naam, pad, tekst, waarschuwing}] */
    async uploadFiches(bestanden) {
      const uit = [];
      for (const bestand of Array.from(bestanden)) {
        const form = new FormData();
        form.append("bestand", bestand, bestand.name);
        let fiche;
        try {
          fiche = await api("/fiches", { method: "POST", body: form });
        } catch (fout) {
          throw new Error(`Upload van "${bestand.name}" mislukt: ${fout.message}`);
        }
        uit.push({ naam: fiche.naam, grootte: bestand.size, pad: fiche.pad || null, tekst: fiche.tekst || "", waarschuwing: fiche.waarschuwing });
      }
      return uit;
    },

    /**
     * Nieuw pakket. Maakt school/richting aan als ze nog niet bestaan.
     * zichtbaarheid 'prive' → meteen bruikbaar; 'publiek' → status 'in_controle' tot een moderator het goedkeurt.
     */
    maakPakket: (gegevens) => api("/pakketten", { method: "POST", body: JSON.stringify(gegevens) }),

    /**
     * Persoonlijke kopie van een pakket bewaren (verandert het gedeelde pakket niet).
     * uitgezet: namen van verplichte vakken die je niet volgt (bv. vrijstelling)
     * keuzes: { groepId: [gekozen vaknamen of optienamen] }
     * overgeslagen: [groepId, …] keuzegroepen die de student helemaal niet volgt
     * eigenVakken: [{ naam, semester, sp }]
     */
    slaMijnPakketOp: (gegevens) => api("/mijn-pakket", { method: "POST", body: JSON.stringify(gegevens) }),

    haalMijnPakket: () => api("/mijn-pakket"),

    /** Welke vakken volgt de student? (verplicht en niet uitgezet + gekozen keuzevakken/opties + eigen vakken) */
    gevolgdeVakken(pakket, mijn) {
      const uitgezet = new Set(mijn.uitgezet || []);
      const overgeslagen = new Set(mijn.overgeslagen || []);
      const keuzes = mijn.keuzes || {};
      const lijst = pakket.vakken.filter((v) => {
        if (!v.groep) return !uitgezet.has(v.naam);
        if (overgeslagen.has(v.groep)) return false;
        const g = (pakket.groepen || []).find((x) => x.id === v.groep);
        const gekozen = keuzes[v.groep] || [];
        return g && g.soort === "optie" ? gekozen.includes(v.optie) : gekozen.includes(v.naam);
      });
      return lijst.concat((mijn.eigenVakken || []).map((v) => ({ ...v, eigen: true })));
    },

    /** Mijn pakket met alles erbij, voor de chat en om de onboarding te hervatten. → {mijn, pakket, vakken} of null */
    haalMijnPakketVolledig: () => api("/mijn-pakket/volledig"),

    /** Wijziging voorstellen aan een gedeeld pakket → gaat naar de moderatie. */
    stelWijzigingVoor: (pakketId, tekst) =>
      api("/voorstellen", { method: "POST", body: JSON.stringify({ pakketId, tekst }) }),

    // ---------- moderatie ----------

    /** Alles wat wacht op controle, met automatische checks. → {pakketten:[…], voorstellen:[…]} */
    haalWachtrij: () => api("/wachtrij"),

    keurPakketGoed: (id) => api(`/pakketten/${encodeURIComponent(id)}/goedkeuren`, { method: "POST" }),

    wijsPakketAf: (id, reden) =>
      api(`/pakketten/${encodeURIComponent(id)}/afwijzen`, { method: "POST", body: JSON.stringify({ reden }) }),

    /** Nieuwe vakken toevoegen aan het bestaande publieke pakket waar het het meest op lijkt. → pakket of null */
    async voegPakketSamen(id) {
      try {
        const data = await api(`/pakketten/${encodeURIComponent(id)}/samenvoegen`, { method: "POST" });
        return data.pakket;
      } catch (fout) {
        if (fout.status === 409) return null;  // geen passend pakket
        throw fout;
      }
    },

    keurVoorstelGoed: (id) => api(`/voorstellen/${encodeURIComponent(id)}/goedkeuren`, { method: "POST" }),

    wijsVoorstelAf: (id, reden) =>
      api(`/voorstellen/${encodeURIComponent(id)}/afwijzen`, { method: "POST", body: JSON.stringify({ reden }) }),

    /** Enkel voor de demo: de server zet de voorbeelddata terug (lokaal; op Supabase enkel met ALLOW_RESET=1). */
    async resetDemo() {
      await api("/reset-demo", { method: "POST" });
      try { localStorage.removeItem("sb-onboarding-klaar"); } catch (e) { /* ok */ }
    },
  };
})();
