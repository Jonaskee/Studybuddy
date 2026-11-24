-- StudieBuddy – Supabase-schema
--
-- Uitvoeren: Supabase-dashboard → SQL Editor → dit bestand plakken → Run,
-- en daarna supabase/opslag_rls.sql (wie aan deze tabellen mag).
-- De Flask-backend gebruikt de publieke key plus de geheime SUPABASE_SERVER_SLEUTEL
-- in een header; de browser krijgt nooit een sleutel te zien: alle data gaat
-- via /api/data/... in app.py/data_api.py.

create table if not exists scholen (
  id text primary key,
  naam text not null
);

create table if not exists richtingen (
  id text primary key,
  school_id text not null references scholen(id) on delete cascade,
  naam text not null
);
create index if not exists richtingen_school_idx on richtingen (school_id);

create table if not exists pakketten (
  id text primary key,
  richting_id text not null references richtingen(id) on delete cascade,
  academiejaar text not null,
  fase text not null,
  afstudeerrichting text,
  status text not null default 'in_controle'
    check (status in ('prive', 'in_controle', 'publiek', 'afgewezen', 'samengevoegd')),
  gebruikers int not null default 0,
  mogelijk_verouderd boolean not null default false,
  ingediend_door text,
  ingediend_op text,
  afwijs_reden text,
  groepen jsonb not null default '[]'::jsonb,
  vakken jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists pakketten_richting_idx on pakketten (richting_id, status);
create index if not exists pakketten_wachtrij_idx on pakketten (status, created_at);

create table if not exists persoonlijke_pakketten (
  student_id text primary key,              -- de browsercookie (studiebuddy_id)
  basis_pakket_id text not null references pakketten(id) on delete cascade,
  uitgezet jsonb not null default '[]'::jsonb,
  overgeslagen jsonb not null default '[]'::jsonb,
  keuzes jsonb not null default '{}'::jsonb,
  eigen_vakken jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists wijzigingsvoorstellen (
  id text primary key,
  pakket_id text not null references pakketten(id) on delete cascade,
  tekst text not null,
  door text,
  op text,
  status text not null default 'in_controle'
    check (status in ('in_controle', 'goedgekeurd', 'afgewezen')),
  afwijs_reden text,
  created_at timestamptz not null default now()
);
create index if not exists voorstellen_status_idx on wijzigingsvoorstellen (status);

-- Alles dichtzetten voor de publieke (anon) sleutel; supabase/opslag_rls.sql
-- laat enkel de backend (met de serversleutel in de header) erbij.
alter table scholen enable row level security;
alter table richtingen enable row level security;
alter table pakketten enable row level security;
alter table persoonlijke_pakketten enable row level security;
alter table wijzigingsvoorstellen enable row level security;

-- De voorbeelddata wordt automatisch geplaatst bij de eerste data-aanvraag
-- (tenzij SEED_DEMO=0). Handmatig terugzetten kan via /moderatie en
-- "Voorbeelddata terugzetten", maar enkel met ALLOW_RESET=1.
