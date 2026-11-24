-- Eenmalige migratie (al uitgevoerd op het StudieBuddy-project, 24/11/2026): samenvoegen met de onboarding.
--
-- supabase.sql (onboarding en moderatie) gebruikt de namen scholen, richtingen en pakketten in een andere vorm
-- dan de eerste versie van supabase/schema.sql. Die oude onboarding-tabellen werden nooit door de app gebruikt:
-- ze gaan met hun gegevens naar het schema `archief` (niet via de API bereikbaar), niets wordt verwijderd.
-- De tabel vakken (de standaardfiches waaruit de chat zijn bronnen haalt) blijft en hangt niet meer af van pakketten.
--
-- Volgorde voor een nieuw project: supabase/schema.sql, supabase/seed.sql, supabase/verbruik.sql, supabase.sql.

create schema if not exists archief;

alter table public.vakken drop constraint if exists vakken_pakket_id_fkey;
alter table public.vakken alter column pakket_id drop not null;
drop policy if exists lezen on public.vakken;
create policy lezen on public.vakken for select using (not verwijderd and eigenaar_id is null);

alter table public.uitgevinkt set schema archief;
alter table public.voorstellen set schema archief;
alter table public.profielen set schema archief;
alter table public.pakketten set schema archief;
alter table public.richtingen set schema archief;
alter table public.scholen set schema archief;
