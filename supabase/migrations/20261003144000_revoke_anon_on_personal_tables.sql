-- Belt and braces: row-level security already blocks anonymous access, but visitors who
-- aren't signed in have no business with these tables at all.
revoke all on table public.profiles from anon;
revoke all on table public.charts from anon;
