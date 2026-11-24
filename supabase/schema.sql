-- StudieBuddy: de standaard ECTS-fiches waaruit de chat zijn bronnen haalt (assistent.py, laad_vakken).
-- Scholen, richtingen, pakketten en moderatie staan in ../supabase.sql (onboarding).
--
-- Volgorde voor een nieuw project: supabase/schema.sql, supabase/seed.sql, supabase/verbruik.sql, supabase.sql.
-- (Het bestaande project kreeg dezelfde vorm via supabase/merge_onboarding.sql.)

create schema if not exists private;  -- niet via de REST-API bereikbaar (verbruik, instellingen)
grant usage on schema private to anon, authenticated;

create table public.vakken (
  id bigint generated always as identity primary key,
  pakket_id bigint,                          -- verwees naar de eerste pakkettabel, niet meer gebruikt
  naam text not null,
  aliassen text[] not null default '{}',     -- bijnamen waarmee studenten naar het vak vragen (BAP, stage, ...)
  studiepunten numeric,
  semester text,
  fiche_md text,                             -- de fiche in markdown, met "## 1. Algemene informatie" enz.
  fiche_pdf_pad text,
  eigenaar_id uuid references auth.users,    -- NULL = standaardfiche voor iedereen
  verwijderd boolean not null default false, -- nooit echt verwijderen
  aangemaakt_op timestamptz not null default now()
);

-- De publieke (anon) key mag enkel de standaardfiches lezen; schrijven kan niemand via de API.
alter table public.vakken enable row level security;
create policy lezen on public.vakken for select using (not verwijderd and eigenaar_id is null);
