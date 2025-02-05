create extension if not exists "uuid-ossp";

create table if not exists person (
    id uuid default uuid_generate_v4(),
    name text not null,
    age int not null,
    address text not null,
    phone_number text not null,
    created_at timestamp default now(),
    updated_at timestamp default now(),
    deleted_at timestamp
);
