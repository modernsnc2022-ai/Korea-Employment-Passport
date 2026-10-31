-- KEP account progress: never store identity documents, payroll or raw form contents.
-- Run once in the selected Supabase project's SQL editor.
create table if not exists public.kep_progress (
  user_id uuid primary key references auth.users(id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint kep_progress_object check (jsonb_typeof(payload)='object'),
  constraint kep_progress_limit check (octet_length(payload::text)<=32768)
);
alter table public.kep_progress enable row level security;
revoke all on public.kep_progress from public, anon, authenticated;
grant select, insert, update, delete on public.kep_progress to authenticated;
create policy "kep_progress_select_own" on public.kep_progress for select to authenticated
  using ((select auth.uid())=user_id);
create policy "kep_progress_insert_own" on public.kep_progress for insert to authenticated
  with check ((select auth.uid())=user_id);
create policy "kep_progress_update_own" on public.kep_progress for update to authenticated
  using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy "kep_progress_delete_own" on public.kep_progress for delete to authenticated
  using ((select auth.uid())=user_id);
