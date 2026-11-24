-- Verbruik en limieten van de AI (zie assistent.py). Op Vercel is er geen vaste schijf, dus dit staat in de database.
-- De tabel staat in `private` (niet via de REST-API bereikbaar). Enkel de functies hieronder kunnen erbij,
-- en die werken alleen met de geheime serversleutel (SUPABASE_SERVER_SLEUTEL in .env / Vercel).
-- Eenmalig na deze migratie (niet in git, enkel de hash staat in de database):
--   insert into private.instellingen values ('server_sleutel_sha256', '<sha256 in hex van SUPABASE_SERVER_SLEUTEL>');

create extension if not exists pgcrypto schema extensions;

create table private.instellingen (naam text primary key, waarde text not null);

create table private.verbruik (
  id bigint generated always as identity primary key,
  tijd timestamptz not null default now(),
  browser text,
  vraag text,
  context boolean,
  tokens_in int,
  tokens_uit int,
  euro numeric not null default 0,
  klaar boolean not null default false  -- false = AI-oproep nog bezig
);
create index on private.verbruik (browser, id);
create index on private.verbruik (tijd);

create function private.controleer_sleutel(p_sleutel text) returns void
language plpgsql stable security definer set search_path = '' as $$
begin
  if p_sleutel is null or encode(extensions.digest(p_sleutel, 'sha256'), 'hex') is distinct from
     (select waarde from private.instellingen where naam = 'server_sleutel_sha256') then
    raise exception 'geen toegang' using errcode = '42501';
  end if;
end $$;

create function private.laatste_vragen(p_browser text) returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(vraag order by id), '[]'::jsonb)
  from (select id, vraag from private.verbruik where browser = p_browser order by id desc limit 5) t
$$;

-- Controleert totaalbudget, daglimiet en vragen per browser, en reserveert dan één vraag.
create function public.vraag_reserveren(p_sleutel text, p_browser text, p_vraag text, p_context boolean,
                                         p_max_per_browser int, p_budget numeric, p_dag_budget numeric)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_totaal numeric;
  v_vandaag numeric;
  v_aantal int := 0;
  v_id bigint;
begin
  perform private.controleer_sleutel(p_sleutel);
  -- één reservatie tegelijk, zodat gelijktijdige vragen de limieten niet omzeilen
  perform pg_advisory_xact_lock(hashtext('studiebuddy_verbruik'));

  select coalesce(sum(euro), 0) into v_totaal from private.verbruik;
  if v_totaal >= p_budget then
    return jsonb_build_object('ok', false, 'reden', 'budget', 'euro', v_totaal);
  end if;

  select coalesce(sum(euro), 0) into v_vandaag from private.verbruik
  where tijd >= (date_trunc('day', now() at time zone 'Europe/Brussels') at time zone 'Europe/Brussels');
  if v_vandaag >= p_dag_budget then
    return jsonb_build_object('ok', false, 'reden', 'dag');
  end if;

  if p_browser is not null then
    select count(*) into v_aantal from private.verbruik where browser = p_browser;
    if v_aantal >= p_max_per_browser then
      return jsonb_build_object('ok', false, 'reden', 'browser');
    end if;
  end if;

  insert into private.verbruik (browser, vraag, context) values (p_browser, left(p_vraag, 500), p_context)
  returning id into v_id;
  return jsonb_build_object('ok', true, 'id', v_id,
    'resterend', case when p_browser is null then null else p_max_per_browser - v_aantal - 1 end,
    'vragen', case when p_browser is null then '[]'::jsonb else private.laatste_vragen(p_browser) end);
end $$;

create function public.vraag_afronden(p_sleutel text, p_id bigint, p_euro numeric, p_tokens_in int, p_tokens_uit int)
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform private.controleer_sleutel(p_sleutel);
  update private.verbruik set euro = p_euro, tokens_in = p_tokens_in, tokens_uit = p_tokens_uit, klaar = true
  where id = p_id and not klaar;
end $$;

-- Mislukte AI-oproep: reservatie weer weg, dus de vraag telt niet mee.
create function public.vraag_annuleren(p_sleutel text, p_id bigint)
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform private.controleer_sleutel(p_sleutel);
  delete from private.verbruik where id = p_id and not klaar;
end $$;

create function public.browser_status(p_sleutel text, p_browser text, p_max_per_browser int)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
begin
  perform private.controleer_sleutel(p_sleutel);
  return jsonb_build_object(
    'resterend', greatest(0, p_max_per_browser - (select count(*) from private.verbruik where browser = p_browser)),
    'vragen', private.laatste_vragen(p_browser));
end $$;

-- Hulpfuncties in `private` mogen niet rechtstreeks aangeroepen worden.
revoke execute on function private.controleer_sleutel(text), private.laatste_vragen(text) from public, anon, authenticated;

-- De server roept deze functies aan met de publieke (anon) key; zonder serversleutel weigeren ze alles.
-- Supabase-advisor waarschuwt daarom "anon can execute SECURITY DEFINER": dat is hier bewust.
revoke execute on function public.vraag_reserveren(text, text, text, boolean, int, numeric, numeric),
  public.vraag_afronden(text, bigint, numeric, int, int), public.vraag_annuleren(text, bigint),
  public.browser_status(text, text, int) from public, authenticated;
grant execute on function public.vraag_reserveren(text, text, text, boolean, int, numeric, numeric),
  public.vraag_afronden(text, bigint, numeric, int, int), public.vraag_annuleren(text, bigint),
  public.browser_status(text, text, int) to anon;

-- Cijfers voor de beheerpagina /admin (ook enkel met de serversleutel).
create or replace function public.admin_statistieken(p_sleutel text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  v_vandaag timestamptz := date_trunc('day', now() at time zone 'Europe/Brussels') at time zone 'Europe/Brussels';
begin
  perform private.controleer_sleutel(p_sleutel);
  return jsonb_build_object(
    'totaal', (select jsonb_build_object('berichten', count(*), 'euro', coalesce(sum(euro), 0),
                 'tokens_in', coalesce(sum(tokens_in), 0), 'tokens_uit', coalesce(sum(tokens_uit), 0),
                 'browsers', count(distinct browser))
               from private.verbruik where klaar),
    'vandaag', (select jsonb_build_object('berichten', count(*), 'euro', coalesce(sum(euro), 0),
                  'tokens_in', coalesce(sum(tokens_in), 0), 'tokens_uit', coalesce(sum(tokens_uit), 0),
                  'browsers', count(distinct browser))
                from private.verbruik where klaar and tijd >= v_vandaag),
    'actief', (select count(distinct browser) from private.verbruik where tijd >= now() - interval '15 minutes'),
    'bezig', (select count(*) from private.verbruik where not klaar and tijd >= now() - interval '2 minutes'),
    -- alle uren van vandaag en alle 14 dagen, ook zonder berichten (0), zodat de grafiek eerlijk is
    'per_uur', (select jsonb_agg(jsonb_build_object('uur', u, 'berichten', coalesce(n, 0), 'euro', coalesce(e, 0)) order by u)
                from generate_series(0, 23) u
                left join (select extract(hour from tijd at time zone 'Europe/Brussels')::int as uur, count(*) as n, sum(euro) as e
                           from private.verbruik where klaar and tijd >= v_vandaag group by 1) x on x.uur = u),
    'per_dag', (select jsonb_agg(jsonb_build_object('dag', to_char(d, 'DD/MM'), 'berichten', coalesce(n, 0), 'euro', coalesce(e, 0),
                  'tokens', coalesce(t, 0), 'browsers', coalesce(b, 0)) order by d desc)
                from generate_series((now() at time zone 'Europe/Brussels')::date - 13, (now() at time zone 'Europe/Brussels')::date, '1 day') d
                left join (select (tijd at time zone 'Europe/Brussels')::date as dag, count(*) as n, sum(euro) as e,
                                  sum(coalesce(tokens_in, 0) + coalesce(tokens_uit, 0)) as t, count(distinct browser) as b
                           from private.verbruik where klaar and tijd >= now() - interval '15 days' group by 1) x on x.dag = d),
    'laatste', (select coalesce(jsonb_agg(jsonb_build_object(
                   'tijd', to_char(tijd at time zone 'Europe/Brussels', 'DD/MM HH24:MI'), 'browser', left(browser, 6),
                   'vraag', vraag, 'tokens_in', tokens_in, 'tokens_uit', tokens_uit, 'euro', euro, 'klaar', klaar)
                 order by id desc), '[]'::jsonb)
                from (select * from private.verbruik order by id desc limit 25) l)
  );
end $$;

revoke execute on function public.admin_statistieken(text) from public, authenticated;
grant execute on function public.admin_statistieken(text) to anon;
