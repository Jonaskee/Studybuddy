"""
Controleert of de Supabase-instellingen in .env kloppen. Toont nooit de sleutel zelf.

Starten:  python controleer_supabase.py
"""

from pathlib import Path
import os

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TABELLEN = ["scholen", "richtingen", "pakketten", "persoonlijke_pakketten", "wijzigingsvoorstellen"]


def soort_sleutel(k):
    if not k:
        return "LEEG"
    if k.startswith("sb_secret_"):
        return "secret key (sb_secret_…) – goed"
    if k.startswith("sb_publishable_"):
        return "PUBLISHABLE key – fout, dit is de publieke sleutel"
    if k.startswith("eyJ"):
        return "JWT (eyJ…) – goed als het de service_role is, fout als het de anon key is"
    return f"onbekend formaat ({len(k)} tekens) – dit is geen API-sleutel (misschien het JWT secret of het databasewachtwoord?)"


def main():
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    sleutel = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    print(f"SUPABASE_URL:            {'ingevuld' if url.startswith('https://') else 'ONTBREEKT of fout'}")
    print(f"SUPABASE_SERVICE_KEY:    {soort_sleutel(sleutel)}")
    publiek = os.getenv("SUPABASE_KEY", "").strip()
    print(f"SUPABASE_KEY:            {'publishable key – goed (voor de standaardfiches)' if publiek.startswith(('sb_publishable_', 'eyJ')) else 'ONTBREEKT'}")
    print(f"SUPABASE_SERVER_SLEUTEL: {'ingevuld (verbruik en limieten)' if os.getenv('SUPABASE_SERVER_SLEUTEL') else 'ONTBREEKT – de chat start niet'}")
    if not url or not sleutel:
        print("\nVul eerst SUPABASE_URL en SUPABASE_SERVICE_KEY (de service_role-key) in.")
        return

    # Een nieuwe sb_secret_-key mag enkel als apikey; de oude service_role-JWT ook als Bearer.
    kop = {"apikey": sleutel, **({"Authorization": f"Bearer {sleutel}"} if sleutel.startswith("eyJ") else {})}
    alles_ok = True
    print()
    for tabel in TABELLEN:
        try:
            r = httpx.get(f"{url}/rest/v1/{tabel}", params={"select": "*", "limit": "1"}, headers=kop, timeout=15)
        except httpx.HTTPError as fout:
            print(f"  {tabel:24} geen verbinding ({type(fout).__name__})")
            alles_ok = False
            continue
        if r.status_code == 200:
            print(f"  {tabel:24} OK")
        elif r.status_code in (401, 403):
            print(f"  {tabel:24} geweigerd ({r.status_code}) – verkeerde sleutel")
            alles_ok = False
        elif r.status_code == 404 or "does not exist" in r.text or "schema cache" in r.text:
            print(f"  {tabel:24} bestaat niet – voer supabase.sql uit in de SQL Editor")
            alles_ok = False
        else:
            print(f"  {tabel:24} fout {r.status_code}: {r.text[:120]}")
            alles_ok = False

    try:
        r = httpx.get(f"{url}/storage/v1/bucket/ects-fiches", headers=kop, timeout=15)
        if r.status_code == 200:
            print(f"  {'bucket ects-fiches':24} OK")
        else:
            print(f"  {'bucket ects-fiches':24} ontbreekt ({r.status_code}) – voer supabase.sql uit of maak hem aan via Storage")
            alles_ok = False
    except httpx.HTTPError as fout:
        print(f"  {'bucket ects-fiches':24} geen verbinding ({type(fout).__name__})")
        alles_ok = False

    print("\nAlles in orde: start de app met  python app.py" if alles_ok else "\nNog niet in orde, zie hierboven.")


if __name__ == "__main__":
    main()
