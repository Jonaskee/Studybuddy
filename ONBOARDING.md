# Onboarding en moderatie

## Pagina's

| URL | Bestand | Wat |
|---|---|---|
| `/onboarding` | `static/onboarding.html` + `static/js/onboarding.js` | School en richting → pakket kiezen → nieuw pakket of aanpassen → status |
| `/moderatie` | `static/moderatie.html` + `static/js/moderatie.js` | Human in the loop: publieke pakketten en wijzigingsvoorstellen nakijken |
| `/` | `static/index.html` | De chat. Stuurt naar `/onboarding` zolang de onboarding niet afgerond is. |
| `/admin` | `templates/admin.html` | Verbruik: kosten, tokens, berichten, actieve sessies en de laatste vragen (beheerderslogin) |

Gedeelde stijl: `static/css/studybuddy.css` (licht en donker). De licht/donker-knop staat in `static/js/theme.js`: elke knop met `data-theme-toggle` wisselt het thema, de keuze wordt bewaard in `localStorage` (`sb-theme`).

Werkt op gsm en pc: onder 960 px breed één kolom zoals op een telefoon, daarboven een zijpaneel met de stappen links en de inhoud rechts.

## Data: frontend → backend → Supabase

De schermen praten enkel met `static/js/data.js` (object `SB`). Dat bestand doet
`fetch("/api/data/...")`; dezelfde functienamen en teruggegeven vormen als vroeger,
dus de UI is niet veranderd. Achter de API staat `opslag.py`:

```
browser (data.js)
   → /api/data/...            (data_api.py, Flask)
       → opslag.py
            → Supabase (REST + Storage)   als SUPABASE_URL + SUPABASE_SERVICE_KEY gezet zijn
            → data_store.json             anders (lokaal ontwikkelen)
```

De API heeft ook `/api/chat` (AI) en `/api/status` (vraaglimiet en eigen vorige
vragen) in `app.py`.

### Supabase klaarzetten

1. Maak een project op supabase.com.
2. SQL Editor → voer na elkaar uit:
   `supabase/schema.sql` (de standaard ECTS-fiches), `supabase/seed.sql` (de 8 fiches),
   `supabase/verbruik.sql` (AI-verbruik en limieten) en `supabase.sql` (onboarding en moderatie).
   Voer in `verbruik.sql` ook de eenmalige `insert` onderaan de commentaar uit (hash van `SUPABASE_SERVER_SLEUTEL`).
3. Storage → New bucket → naam `ects-fiches`, Private (of laat de SQL het doen).
4. Project Settings → API Keys: kopieer de **Project URL**, de **publishable**-key en de **service_role**-key
   (Legacy API keys → service_role → Reveal, begint met `eyJ`).
5. Zet ze in `.env`:

```
SUPABASE_URL=https://jouwproject.supabase.co
SUPABASE_KEY=sb_publishable_...          # mag publiek: leest enkel de standaardfiches
SUPABASE_SERVICE_KEY=eyJ...service_role... # geheim: onboarding, moderatie en PDF's
SUPABASE_SERVER_SLEUTEL=...              # geheim, zelf gekozen: verbruik en limieten (zie verbruik.sql)
```

Drie sleutels, elk met één taak. De service_role-key omzeilt RLS en blijft dus
server-side; de browser krijgt nooit een sleutel te zien. Test met
`python controleer_supabase.py` (toont nooit de sleutels zelf).

De voorbeelddata (scholen, richtingen, pakketten, één voorstel) wordt bij de
eerste data-aanvraag automatisch geplaatst als de databank leeg is. Uitzetten
met `SEED_DEMO=0`.

### Tabellen

`pakketten` bewaart `vakken` en `groepen` als JSONB (één rij per pakket, dus
opslaan is atomair). Dat is een bewuste vereenvoudiging van de vroegere
genormaliseerde tabellen; de veldnamen binnen de JSON zijn dezelfde als in de UI.

```
scholen                (id, naam)
richtingen             (id, school_id → scholen, naam)
pakketten              (id, richting_id → richtingen, academiejaar, fase,
                        afstudeerrichting, status, gebruikers, mogelijk_verouderd,
                        ingediend_door, ingediend_op, afwijs_reden,
                        groepen jsonb, vakken jsonb, created_at)
persoonlijke_pakketten (student_id, basis_pakket_id → pakketten, uitgezet jsonb,
                        overgeslagen jsonb, keuzes jsonb, eigen_vakken jsonb, updated_at)
wijzigingsvoorstellen  (id, pakket_id → pakketten, tekst, door, op, status, afwijs_reden)
```

Scholen: `HOGESCHOLEN` in `opslag.py` bevat alle Vlaamse hogescholen (met afkortingen
zoals "kdg", "ehb", "artesis" als zoekwoorden). Ze verschijnen in de onboarding ook zonder
pakket; een school komt pas in de tabel `scholen` bij het eerste pakket.

Vakken toevoegen: een geüploade ECTS-fiche wordt meteen een vak. `fiche_gegevens()` leest
de vaknaam, studiepunten en het semester uit de PDF-tekst; de student kan alles in de lijst
nog aanpassen. Een fiche met dezelfde naam als een bestaand vak wordt aan dat vak gekoppeld.

Hoe keuzes werken:
- **Keuzevak:** vakken met dezelfde `groep` (soort `keuze`); de student kiest er `kies` uit.
- **Keuzeoptie:** een groep met soort `optie`; elk vak in die groep hoort via `optie` bij een bundel (bv. "Startup"). De student kiest `kies` opties en krijgt alle vakken van die optie.
- **Semester:** `1`, `2`, `1of2` (student kiest zelf, bv. stage) of `jaar` (jaarvak). Zo komen de studiepunten per semester uit.

In de voorbeelddata is het pakket "3e bachelor · Artificiële Intelligentie"
overgenomen uit de ECTS-fiches in `context/` (samen 60 sp). De andere pakketten
en de optie "Research" zijn verzonnen voorbeelden.

### Lokaal zonder Supabase

Zonder geldige `SUPABASE_URL` + sleutel gebruikt de backend `data_store.json`
(staat in `.gitignore`). Alles werkt dan lokaal, maar op Vercel is dat bestand
vluchtig: elke cold start begint opnieuw. Gebruik daar Supabase.

## Omgevingsvariabelen

| Variabele | Wat |
|---|---|
| `R33_API_KEY` | verplicht voor de chat (route33) |
| `SUPABASE_URL` | bv. `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | publishable key: leest enkel de standaard ECTS-fiches (tabel `vakken`) |
| `SUPABASE_SERVER_SLEUTEL` | zelf gekozen geheim: enkel hiermee kan de server het AI-verbruik lezen en boeken (`supabase/verbruik.sql`, de databank bewaart alleen de hash) |
| `SUPABASE_SERVICE_KEY` | service_role-key: onboarding, moderatie en PDF-opslag. Zonder valt de opslag terug op `data_store.json` |
| `SITE_USER` + `SITE_WACHTWOORD` | optioneel: hele site achter HTTP Basic Auth |
| `ADMIN_USER` + `ADMIN_WACHTWOORD` | login voor `/admin` (Basic Auth) en `/moderatie` (of `MODERATIE_CODE` voor enkel moderatie) |
| `SECRET_KEY` | optioneel: eigen geheim voor de moderatorcookie en de handtekening op PDF-tekst (anders afgeleid van de andere geheimen) |
| `TOTAAL_BUDGET` | euro's aan AI in totaal; leeg = 1,00 |
| `DAG_BUDGET` | euro's aan AI per dag; leeg = 0,10. `0` = de chat staat dicht (bewust: een tikfout mag geen onbeperkte kosten geven) |
| `MAX_VRAGEN_PER_BROWSER` | vragen per browser; standaard 5, `0` = onbeperkt |
| `MAX_VRAAG_TEKENS` | standaard 500 |
| `MAX_VRAGEN_PER_MINUUT` | voor de hele site samen; standaard 30 |
| `SEED_DEMO` | `0` = geen voorbeelddata plaatsen |
| `ALLOW_RESET` | `1` = "Voorbeelddata terugzetten" ook op Supabase toelaten |
| `DATA_BESTAND` / `UPLOAD_MAP` | optioneel: ander pad voor de lokale fallback |

Op Vercel zet je dezelfde variabelen bij **Environment Variables** (geheimen als
*Sensitive*). Verplicht daar: `R33_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`,
`SUPABASE_SERVER_SLEUTEL` en `SUPABASE_SERVICE_KEY` (anders ben je de pakketten
kwijt bij elke herstart).

De AI-limieten (totaalbudget, daglimiet, vragen per browser) en de vraaggeschiedenis
staan in Supabase (`private.verbruik`), dus ze overleven een herstart en gelden over
alle Vercel-instanties heen. Enkel de teller per minuut en de login-lockout staan in
het geheugen.

Vercel laat per serverless request max. ~4,5 MB door. Daarom is de PDF-limiet
4 MB (UI en server) en uploadt de frontend één PDF per request.

## De chat: bronnen uit de ECTS-fiches

- Zonder pakket gebruikt de chat de 8 standaardfiches (tabel `vakken`).
- Met een pakket uit de onboarding enkel de vakken van de student: per vak zijn eigen
  geüploade PDF, anders de standaardfiche met dezelfde naam ("Project Start-up" =
  "Project Start up"). Een vak zonder fiche staat in het overzicht met "geen ECTS-fiche",
  zodat de AI dat eerlijk zegt.
- De fiches worden per sectie opgeknipt (algemene info, toetsing, aanwezigheid, ...).
  Bij een PDF zoekt `secties_uit()` in `assistent.py` de gekende koppen; zonder koppen
  wordt hij in stukken van ~1500 tekens geknipt. Elk antwoord vermeldt zijn bronnen,
  die de student in de chat kan openklappen.
- De tekst van een PDF is meteen na de upload bruikbaar (ook als het pakket nog
  `in_controle` staat), maar enkel voor wie hem uploadde.
- Fichetekst wordt alleen aanvaard met de handtekening die de server bij de upload gaf:
  niemand kan zelf "fichetekst" meesturen zonder echte PDF.
- `python eval_bronnen.py` test of de juiste secties gevonden worden (gratis);
  met `--ai` ook de echte antwoorden en bronnen (~1 cent).

## Mijn pakket

Na de onboarding wordt het persoonlijke pakket op de server bewaard
(`slaMijnPakketOp` → `persoonlijke_pakketten`). De chat toont het in de zijbalk
(`haalMijnPakketVolledig`), en `/onboarding` toont bovenaan "Jouw pakket" met
een knop om het verder aan te passen. De status (privé, in controle, afgewezen
+ reden) is daar ook te zien.

## Moderatie afschermen

Zet `ADMIN_USER` + `ADMIN_WACHTWOORD` (of `MODERATIE_CODE`) in `.env` of bij de
Environment Variables op Vercel. Dan vraagt `/moderatie` eerst om in te loggen;
de cookie is 8 uur geldig en bevat een HMAC-token, niet het wachtwoord. Dat token
is afgeleid van de geheimen (nooit van een vaste tekst), dus wie het wachtwoord
verandert, logt alle moderators uit. De moderatie-API (`/api/data/wachtrij`,
goedkeuren, afwijzen, samenvoegen) weigert zonder die cookie. Zonder ingestelde
gegevens is moderatie enkel lokaal open, nooit op Vercel.

De moderator ziet bij een nieuw publiek pakket de tekst van elke ECTS-fiche: na
goedkeuring gebruikt de chat die tekst als bron voor iedereen met dat pakket.

De hele site achter HTTP Basic Auth zetten kan met `SITE_USER` + `SITE_WACHTWOORD`.

## Beveiliging in het kort

- Beveiligingsheaders op elke pagina (CSP: enkel eigen code + Google Fonts, geen iframes, geen caching van pagina's).
- Uploads en wijzigingen: max. 30 per browser per kwartier (300 voor de hele site), JSON max. 256 kB.
- Foutmeldingen van route33 of Supabase gaan naar de serverlog, nooit naar de gebruiker.

## Bekende shortcuts

- Eén gedeelde moderatorlogin in plaats van echte accounts. Vervangen door de rol `moderator` zodra Supabase Auth er is.
- Het persoonlijke pakket hangt aan een browsercookie (`studiebuddy_id`), niet aan een account. Een andere browser of toestel ziet het niet.
- De koppeling tussen een PDF en een vak gebeurt op bestandsnaam (bv. `databanken.pdf` → "Databanken").
- `voegPakketSamen` doet twee updates (doelpakket + status van de bron); er is geen transactie. Bij een netwerkfout halverwege kan de bron op `in_controle` blijven staan.
- De teller per minuut en de login-lockout staan in het geheugen, per Vercel-instantie.
