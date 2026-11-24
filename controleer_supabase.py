"""
Controleert of de Supabase-instellingen in .env kloppen. Toont nooit de sleutels zelf.

Starten:  python controleer_supabase.py
"""

from pathlib import Path
import os

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TABELLEN = ["scholen", "richtingen", "pakketten", "persoonlijke_pakketten", "wijzigingsvoorstellen", "fiche_pdfs"]


def main():
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    publiek = (os.getenv("SUPABASE_KEY") or "").strip()
    server = (os.getenv("SUPABASE_SERVER_SLEUTEL") or "").strip()
    print(f"SUPABASE_URL:            {'ingevuld' if url.startswith('https://') else 'ONTBREEKT of fout'}")
    print(f"SUPABASE_KEY:            {'publishable key – goed' if publiek.startswith(('sb_publishable_', 'eyJ')) else 'ONTBREEKT'}")
    print(f"SUPABASE_SERVER_SLEUTEL: {'ingevuld' if server else 'ONTBREEKT'}")
    if not url or not publiek or not server:
        print("\nVul eerst SUPABASE_URL, SUPABASE_KEY en SUPABASE_SERVER_SLEUTEL in.")
        return

    alles_ok = True
    print()
    for tabel in TABELLEN:
        try:
            met = httpx.get(f"{url}/rest/v1/{tabel}", params={"select": "*", "limit": "1"},
                            headers={"apikey": publiek, "x-studiebuddy-sleutel": server}, timeout=15)
            zonder = httpx.get(f"{url}/rest/v1/{tabel}", params={"select": "*", "limit": "1"},
                               headers={"apikey": publiek}, timeout=15)
        except httpx.HTTPError as fout:
            print(f"  {tabel:24} geen verbinding ({type(fout).__name__})")
            alles_ok = False
            continue
        if met.status_code == 404 or "does not exist" in met.text or "schema cache" in met.text:
            print(f"  {tabel:24} bestaat niet – voer supabase.sql en supabase/opslag_rls.sql uit")
            alles_ok = False
        elif met.status_code != 200:
            print(f"  {tabel:24} fout {met.status_code}")
            alles_ok = False
        elif zonder.status_code == 200 and zonder.json():
            print(f"  {tabel:24} OPEN voor iedereen – voer supabase/opslag_rls.sql uit")
            alles_ok = False
        elif met.json() == [] and tabel == "scholen":
            print(f"  {tabel:24} leeg: wordt bij de eerste aanvraag gevuld, of de serversleutel klopt niet met de hash")
        else:
            print(f"  {tabel:24} OK")

    print("\nAlles in orde: start de app met  python app.py" if alles_ok else "\nNog niet in orde, zie hierboven.")


if __name__ == "__main__":
    main()
