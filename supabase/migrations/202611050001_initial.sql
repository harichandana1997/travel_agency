create table if not exists public.travel_memory (
    id integer primary key check (id = 1),
    summary text not null default '',
    preferences jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create table if not exists public.saved_trips (
    id uuid primary key,
    origin text not null,
    destination text not null,
    travel_date date not null,
    preferences jsonb not null default '{}'::jsonb,
    itinerary jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

alter table public.travel_memory enable row level security;
alter table public.saved_trips enable row level security;
