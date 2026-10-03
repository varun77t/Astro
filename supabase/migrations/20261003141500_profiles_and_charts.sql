-- Saved people (self, family) and their charts. Each row belongs to one auth user, and
-- row-level security lets a signed-in user see and change only their own rows.

create table public.profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  label text not null check (char_length(label) between 1 and 60),
  birth_date date not null,
  birth_time time,
  time_accuracy text not null check (time_accuracy in ('exact', 'approximate', 'unknown')),
  time_window_minutes integer check (time_window_minutes between 1 and 360),
  place_name text not null check (char_length(place_name) between 1 and 200),
  lat double precision not null check (lat between -90 and 90),
  lon double precision not null check (lon between -180 and 180),
  tz_name text not null check (char_length(tz_name) <= 64),
  fold smallint check (fold in (0, 1)),
  utc_offset_minutes integer check (utc_offset_minutes between -720 and 840),
  -- Consent to store these birth details (India's DPDP Act: purpose, consent, deletion).
  consented_at timestamptz not null,
  consent_version text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (birth_time is not null or time_accuracy = 'unknown')
);
create index profiles_user_id_idx on public.profiles (user_id);

create table public.charts (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null unique references public.profiles (id) on delete cascade,
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  chart_json jsonb not null,
  engine_version text not null,
  created_at timestamptz not null default now()
);
create index charts_user_id_idx on public.charts (user_id);

alter table public.profiles enable row level security;
alter table public.charts enable row level security;

create policy "profiles: owner reads" on public.profiles
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "profiles: owner inserts" on public.profiles
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "profiles: owner updates" on public.profiles
  for update to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "profiles: owner deletes" on public.profiles
  for delete to authenticated using ((select auth.uid()) = user_id);

create policy "charts: owner reads" on public.charts
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "charts: owner inserts own profile's chart" on public.charts
  for insert to authenticated with check (
    (select auth.uid()) = user_id
    and exists (
      select 1 from public.profiles p
      where p.id = profile_id and p.user_id = (select auth.uid())
    )
  );
create policy "charts: owner updates" on public.charts
  for update to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "charts: owner deletes" on public.charts
  for delete to authenticated using ((select auth.uid()) = user_id);

create function public.touch_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end;
$$;
create trigger profiles_touch before update on public.profiles
  for each row execute function public.touch_updated_at();

-- "Delete my data": removes the signed-in user; their profiles and charts go with them
-- (on delete cascade). Runs with the definer's rights only to reach auth.users, and only
-- ever for the caller. (The Supabase security advisor flags this; it's intended.)
create function public.delete_my_account() returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  delete from auth.users where id = auth.uid();
end;
$$;
revoke execute on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
