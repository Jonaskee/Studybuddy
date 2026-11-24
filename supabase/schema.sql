-- StudieBuddy datamodel (zie PLAN_ects_onboarding.md, hoofdstuk 4).
-- Nooit echt verwijderen: alles krijgt een status of `verwijderd`.
-- Fase 0: enkel lees-policies. Schrijven komt met de onboarding/upload (fase 1-3);
-- zonder policy weigert RLS elke schrijfactie, dus dat is veilig.

create extension if not exists pg_trgm schema extensions;
create schema if not exists private;  -- niet via de REST-API bereikbaar
grant usage on schema private to anon, authenticated;

create table public.scholen (
  id bigint generated always as identity primary key,
  naam text not null,
  aliassen text[] not null default '{}',
  email_domein text,
  status text not null default 'in_review' check (status in ('in_review', 'goedgekeurd', 'afgekeurd')),
  maker_id uuid references auth.users default auth.uid(),
  aangemaakt_op timestamptz not null default now()
);

create table public.richtingen (
  id bigint generated always as identity primary key,
  school_id bigint not null references public.scholen,
  naam text not null,
  afstudeerrichting text,
  status text not null default 'in_review' check (status in ('in_review', 'goedgekeurd', 'afgekeurd')),
  maker_id uuid references auth.users default auth.uid(),
  aangemaakt_op timestamptz not null default now()
);

create table public.pakketten (
  id bigint generated always as identity primary key,
  richting_id bigint not null references public.richtingen,
  academiejaar text not null check (academiejaar ~ '^\d{4}-\d{2}$'),
  trajectschijf int,
  zichtbaarheid text not null default 'prive' check (zichtbaarheid in ('prive', 'publiek')),
  status text not null default 'in_review' check (status in ('in_review', 'goedgekeurd', 'afgekeurd')),
  maker_id uuid references auth.users default auth.uid(),
  gebaseerd_op_pakket_id bigint references public.pakketten,
  review_opmerking text,
  aangemaakt_op timestamptz not null default now()
);

create table public.vakken (
  id bigint generated always as identity primary key,
  pakket_id bigint not null references public.pakketten,
  naam text not null,
  aliassen text[] not null default '{}',
  studiepunten numeric,
  semester text,
  fiche_md text,
  fiche_pdf_pad text,
  eigenaar_id uuid references auth.users,  -- NULL = hoort bij het pakket, ingevuld = eigen vak van één student
  verwijderd boolean not null default false,
  aangemaakt_op timestamptz not null default now()
);

create table public.profielen (
  user_id uuid primary key references auth.users,
  pakket_id bigint references public.pakketten,
  rol text not null default 'student' check (rol in ('student', 'moderator'))
);

create table public.uitgevinkt (
  user_id uuid not null references auth.users,
  vak_id bigint not null references public.vakken,
  primary key (user_id, vak_id)
);

create table public.voorstellen (
  id bigint generated always as identity primary key,
  pakket_id bigint not null references public.pakketten,
  type text not null check (type in ('vak_toevoegen', 'vak_wijzigen', 'vak_verwijderen')),
  vak_id bigint references public.vakken,
  nieuwe_data jsonb,
  indiener_id uuid not null references auth.users default auth.uid(),
  status text not null default 'in_review' check (status in ('in_review', 'goedgekeurd', 'afgekeurd')),
  review_opmerking text,
  aangemaakt_op timestamptz not null default now()
);

create index on public.vakken (pakket_id);
create index on public.scholen using gin (naam extensions.gin_trgm_ops);
create index on public.richtingen using gin (naam extensions.gin_trgm_ops);

-- security definer: leest profielen zonder RLS, anders roept de policy van profielen zichzelf op
create function private.is_moderator() returns boolean
language sql stable security definer set search_path = ''
as $$ select exists (select 1 from public.profielen where user_id = auth.uid() and rol = 'moderator') $$;

alter table public.scholen     enable row level security;
alter table public.richtingen  enable row level security;
alter table public.pakketten   enable row level security;
alter table public.vakken      enable row level security;
alter table public.profielen   enable row level security;
alter table public.uitgevinkt  enable row level security;
alter table public.voorstellen enable row level security;

create policy lezen on public.scholen for select
  using (status = 'goedgekeurd' or maker_id = auth.uid() or private.is_moderator());

create policy lezen on public.richtingen for select
  using (status = 'goedgekeurd' or maker_id = auth.uid() or private.is_moderator());

create policy lezen on public.pakketten for select
  using ((zichtbaarheid = 'publiek' and status = 'goedgekeurd') or maker_id = auth.uid() or private.is_moderator());

-- Een vak van een pakket zie je als je het pakket mag zien (de subquery volgt de policy van pakketten).
create policy lezen on public.vakken for select
  using (
    private.is_moderator()
    or (not verwijderd and (
      eigenaar_id = auth.uid()
      or (eigenaar_id is null and exists (select 1 from public.pakketten p where p.id = pakket_id))
    ))
  );

create policy lezen on public.profielen for select
  using (user_id = auth.uid() or private.is_moderator());

create policy lezen on public.uitgevinkt for select
  using (user_id = auth.uid());

create policy lezen on public.voorstellen for select
  using (indiener_id = auth.uid() or private.is_moderator());
