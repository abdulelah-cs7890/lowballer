-- Lowballer schema for Supabase (Postgres). Mirrors the SQLAlchemy models in
-- backend/app/models/tables.py. Run this in the Supabase SQL editor when moving
-- off the local SQLite dev database.

create table if not exists listings (
    id           text primary key,            -- haraj listing id
    source       text not null default 'haraj',
    url          text,
    title        text,
    make         text,
    model        text,
    year         integer,
    mileage_km   integer,
    engine_size  double precision,
    fuel_type    text,
    gear_type    text,
    origin       text,
    region       text,
    color        text,
    options      text,
    asking_price double precision not null,
    image        text,
    condition    text,
    scraped_at   timestamptz not null default now()
);

create table if not exists valuations (
    id              bigint generated always as identity primary key,
    listing_id      text not null references listings(id) on delete cascade,
    predicted_price double precision not null,
    percent_below   double precision not null,   -- (predicted - asking) / predicted
    needs_review    boolean not null default false,
    model_mae       double precision,
    model_version   text,
    created_at      timestamptz not null default now()
);
create index if not exists valuations_listing_idx on valuations(listing_id);

create table if not exists flags (
    id            bigint generated always as identity primary key,
    listing_id    text not null references listings(id) on delete cascade,
    valuation_id  bigint not null references valuations(id) on delete cascade,
    percent_below double precision not null,
    needs_review  boolean not null default false,
    status        text not null default 'open',  -- open | dismissed
    created_at    timestamptz not null default now()
);
create index if not exists flags_listing_idx on flags(listing_id);
create index if not exists flags_status_idx on flags(status);

-- Enable Supabase Realtime on flags so new deals stream to the dashboard (M4).
-- alter publication supabase_realtime add table flags;
