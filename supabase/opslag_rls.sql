-- Onboarding-opslag (opslag.py) zonder service_role-key.
-- De server stuurt zijn geheime SUPABASE_SERVER_SLEUTEL mee in de header x-studiebuddy-sleutel; RLS laat de
-- onboarding-tabellen enkel toe als de hash daarvan klopt (dezelfde hash als in supabase/verbruik.sql).
-- Zo kan een gelekte serversleutel enkel aan deze tabellen, niet aan de hele databank zoals een service_role-key.
-- Uitvoeren na supabase.sql.

create or replace function private.server_ok() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce(
    encode(extensions.digest(current_setting('request.headers', true)::json ->> 'x-studiebuddy-sleutel', 'sha256'), 'hex')
      = (select waarde from private.instellingen where naam = 'server_sleutel_sha256'),
    false)
$$;
revoke execute on function private.server_ok() from public, authenticated;
grant execute on function private.server_ok() to anon;

-- De geüploade PDF's zelf (Supabase Storage kent de header niet; de chat gebruikt enkel de tekst eruit).
create table if not exists public.fiche_pdfs (
  pad text primary key,
  inhoud bytea not null,
  created_at timestamptz not null default now()
);
alter table public.fiche_pdfs enable row level security;

do $$
declare t text;
begin
  foreach t in array array['scholen', 'richtingen', 'pakketten', 'persoonlijke_pakketten', 'wijzigingsvoorstellen', 'fiche_pdfs'] loop
    execute format('drop policy if exists server on public.%I', t);
    -- (select ...) zodat de controle één keer per aanvraag gebeurt, niet per rij
    execute format('create policy server on public.%I for all to anon using ((select private.server_ok())) '
                   'with check ((select private.server_ok()))', t);
  end loop;
end $$;

-- Max. 100 MB aan PDF's: de gratis databank is 500 MB, en een volle databank legt ook de chat stil.
-- Daarboven bewaart de app enkel nog de tekst eruit (opslag.py geeft dan een waarschuwing).
-- shortcut: gelijktijdige uploads kunnen samen enkele MB over de grens gaan; prima zolang de grens ruim onder 500 MB blijft.
create or replace function private.fiche_pdfs_limiet() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if (select coalesce(sum(octet_length(inhoud)), 0) from public.fiche_pdfs) + octet_length(new.inhoud) > 100 * 1024 * 1024 then
    raise exception 'limiet voor PDF-opslag bereikt';
  end if;
  return new;
end $$;
revoke execute on function private.fiche_pdfs_limiet() from public, anon, authenticated;
drop trigger if exists fiche_pdfs_limiet on public.fiche_pdfs;
create trigger fiche_pdfs_limiet before insert on public.fiche_pdfs
  for each row execute function private.fiche_pdfs_limiet();
