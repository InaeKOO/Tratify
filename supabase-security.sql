-- Tratify Supabase security hardening
-- Run this in Supabase SQL Editor after adding your admin email(s) below.

create table if not exists public.admin_emails (
  email text primary key,
  created_at timestamptz not null default now()
);

-- TODO: replace with your real Supabase Auth admin email, then run once.
-- insert into public.admin_emails (email) values ('your-admin-email@example.com') on conflict do nothing;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.admin_emails a
    where lower(a.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  );
$$;

alter table public.announcements enable row level security;
alter table public.admin_emails enable row level security;

drop policy if exists "Public can read verified announcements" on public.announcements;
drop policy if exists "Anyone can submit unverified announcements" on public.announcements;
drop policy if exists "Admins can read all announcements" on public.announcements;
drop policy if exists "Admins can update announcements" on public.announcements;
drop policy if exists "Admins can delete announcements" on public.announcements;
drop policy if exists "Admins can read admin emails" on public.admin_emails;

create policy "Public can read verified announcements"
on public.announcements
for select
to anon, authenticated
using (verified = true);

create policy "Anyone can submit unverified announcements"
on public.announcements
for insert
to anon, authenticated
with check (verified = false);

create policy "Admins can read all announcements"
on public.announcements
for select
to authenticated
using (public.is_admin());

create policy "Admins can update announcements"
on public.announcements
for update
to authenticated
using (public.is_admin())
with check (public.is_admin());

create policy "Admins can delete announcements"
on public.announcements
for delete
to authenticated
using (public.is_admin());

create policy "Admins can read admin emails"
on public.admin_emails
for select
to authenticated
using (public.is_admin());
