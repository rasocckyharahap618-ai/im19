-- IM 19 Institutional RAG: allow backend Dropbox ingestion into the existing rag schema.
-- This migration assumes institutional_rag_core_20261019 has already created rag.documents
-- and rag.document_chunks. Keep all service-role credentials backend-only.

grant usage on schema rag to service_role;
grant select, insert, update, delete on table rag.documents to service_role;
grant select, insert, update, delete on table rag.document_chunks to service_role;
grant usage, select on sequence rag.document_chunks_id_seq to service_role;

alter table rag.documents enable row level security;
alter table rag.document_chunks enable row level security;

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
as $function$
  select c.id, c.document_id, c.content, c.metadata,
         1 - (c.embedding operator(extensions.<=>) query_embedding) as similarity
  from rag.document_chunks c
  where c.embedding is not null
    and c.metadata @> coalesce(filter_metadata, '{}'::jsonb)
  order by c.embedding operator(extensions.<=>) query_embedding
  limit greatest(1, least(coalesce(match_count, 8), 50));
$function$;

revoke all on function public.match_rag_chunks(extensions.vector, integer, jsonb) from public, anon, authenticated;
grant execute on function public.match_rag_chunks(extensions.vector, integer, jsonb) to service_role;
