-- Para+ — server-side admin authorization and news publishing.
-- Run this file in the Supabase SQL Editor for project dmvvezrgaanenwccvhai.
-- It contains no secret or service-role key.

create table if not exists public.app_admins (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null default 'admin' check (role in ('super_admin', 'admin')),
  created_at timestamptz not null default now()
);

alter table public.app_admins enable row level security;
grant select on table public.app_admins to authenticated;

-- A user may see only their own role. There is deliberately no client-side
-- INSERT/UPDATE/DELETE policy: privileges are granted only in SQL Editor.
do $$
declare policy_name text;
begin
  for policy_name in
    select policyname from pg_policies
    where schemaname = 'public' and tablename = 'app_admins'
  loop
    execute format('drop policy if exists %I on public.app_admins', policy_name);
  end loop;
end;
$$;
create policy "admins read own role"
  on public.app_admins for select to authenticated
  using ((select auth.uid()) = user_id);

-- SECURITY DEFINER prevents recursive RLS checks when these functions are
-- evaluated from a policy. They are not writable from the browser.
create or replace function public.is_app_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.app_admins where user_id = auth.uid()
  );
$$;

create or replace function public.is_super_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.app_admins
    where user_id = auth.uid() and role = 'super_admin'
  );
$$;

revoke all on function public.is_app_admin() from public;
revoke all on function public.is_super_admin() from public;
grant execute on function public.is_app_admin() to authenticated;
grant execute on function public.is_super_admin() to authenticated;

-- The existing news table remains publicly readable. Only an authenticated
-- user listed in app_admins can write it.
alter table public.news enable row level security;
grant select on table public.news to anon, authenticated;
grant insert, update, delete on table public.news to authenticated;

-- `news.id` may be backed by a sequence on projects created with older
-- Supabase defaults. Grant only that sequence, if it exists, not every
-- sequence in the public schema.
do $$
declare sequence_name text;
begin
  sequence_name := pg_get_serial_sequence('public.news', 'id');
  if sequence_name is not null then
    execute format('grant usage, select on sequence %s to authenticated', sequence_name);
  end if;
end;
$$;

alter table public.news add column if not exists image_url text;

-- Replace all policies on this application table so an earlier permissive
-- development policy cannot leave a route for anonymous writes.
do $$
declare policy_name text;
begin
  for policy_name in
    select policyname from pg_policies
    where schemaname = 'public' and tablename = 'news'
  loop
    execute format('drop policy if exists %I on public.news', policy_name);
  end loop;
end;
$$;
create policy "public can read news"
  on public.news for select to anon, authenticated
  using (true);

drop policy if exists "admins insert news" on public.news;
create policy "admins insert news"
  on public.news for insert to authenticated
  with check (public.is_app_admin());

drop policy if exists "admins update news" on public.news;
create policy "admins update news"
  on public.news for update to authenticated
  using (public.is_app_admin())
  with check (public.is_app_admin());

drop policy if exists "admins delete news" on public.news;
create policy "admins delete news"
  on public.news for delete to authenticated
  using (public.is_super_admin());

-- Public image bucket. Object writes are guarded by exactly the same server
-- function as news writes; anonymous users can only read published images.
insert into storage.buckets (id, name, public)
values ('news-images', 'news-images', true)
on conflict (id) do update set public = true;

drop policy if exists "public can read news images" on storage.objects;
create policy "public can read news images"
  on storage.objects for select to public
  using (bucket_id = 'news-images');

drop policy if exists "admins upload news images" on storage.objects;
create policy "admins upload news images"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'news-images' and public.is_app_admin());

drop policy if exists "admins update news images" on storage.objects;
create policy "admins update news images"
  on storage.objects for update to authenticated
  using (bucket_id = 'news-images' and public.is_app_admin())
  with check (bucket_id = 'news-images' and public.is_app_admin());

drop policy if exists "admins delete news images" on storage.objects;
create policy "admins delete news images"
  on storage.objects for delete to authenticated
  using (bucket_id = 'news-images' and public.is_super_admin());

-- Bootstrap exactly one first administrator after creating that user in
-- Authentication > Users. Replace the email, run once, then remove this block:
-- insert into public.app_admins (user_id, role)
-- select id, 'super_admin' from auth.users where email = 'YOUR_EMAIL@example.com'
-- on conflict (user_id) do update set role = excluded.role;
