-- IM 19 Institutional RAG: Dropbox ingestion metadata + pgvector chunks.
-- Backend-only access: do not grant table access to anon/authenticated.
create extension if not exists vector with schema extensions;

create table if not exists public.rag_documents (
  id uuid primary key default gen_random_uuid(),
  source_path text not null unique,
  title text not null,
  content_sha256 text not null,
  source_revision text,
  source_modified_at timestamptz,
  ingested_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.rag_chunks (
  id bigint generated always as identity primary key,
  document_id uuid not null references public.rag_documents(id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  content text not null,
  embedding extensions.vector(384) not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create index if not exists rag_chunks_document_id_idx on public.rag_chunks(document_id);
create index if not exists rag_chunks_embedding_hnsw_idx
  on public.rag_chunks using hnsw (embedding extensions.vector_cosine_ops);

alter table public.rag_documents enable row level security;
alter table public.rag_chunks enable row level security;

revoke all on table public.rag_documents from anon, authenticated;
revoke all on table public.rag_chunks from anon, authenticated;
grant all on table public.rag_documents to service_role;
grant all on table public.rag_chunks to service_role;
grant usage, select on sequence public.rag_chunks_id_seq to service_role;

create or replace function public.match_rag_chunks(
  query_embedding extensions.vector(384),
  match_count integer default 8,
  filter_metadata jsonb default '{}'::jsonb
)
returns table (
  chunk_id bigint,
  document_id uuid,
  content text,
  metadata jsonb,
  similarity double precision
)
language sql
stable
set search_path = ''
as $$
  select c.id, c.document_id, c.content, c.metadata,
         1 - (c.embedding operator(extensions.<=>) query_embedding) as similarity
  from public.rag_chunks c
  where c.metadata @> coalesce(filter_metadata, '{}'::jsonb)
  order by c.embedding operator(extensions.<=>) query_embedding
  limit greatest(1, least(coalesce(match_count, 8), 50));
$$;

revoke all on function public.match_rag_chunks(extensions.vector, integer, jsonb) from public, anon, authenticated;
grant execute on function public.match_rag_chunks(extensions.vector, integer, jsonb) to service_role;
