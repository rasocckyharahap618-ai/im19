-- IM 19 Institutional RAG: restricted RPC bridge for Dropbox ingestion.
-- Depends on institutional_rag_core_20261019 creating schema rag, rag.documents,
-- rag.document_chunks, and the pgvector extension in schema extensions.
-- Do not expose raw rag tables to anon/authenticated. Use these RPCs only server-side.

grant usage on schema rag to service_role;
grant select, insert, update, delete on table rag.documents to service_role;
grant select, insert, update, delete on table rag.document_chunks to service_role;
grant usage, select on sequence rag.document_chunks_id_seq to service_role;
alter table rag.documents enable row level security;
alter table rag.document_chunks enable row level security;

create or replace function public.upsert_rag_document(
  p_source_uri text,
  p_source_version text,
  p_title text,
  p_content_hash text,
  p_metadata jsonb default '{}'::jsonb
)
returns uuid
language plpgsql
set search_path = ''
as $function$
declare v_id uuid;
begin
  insert into rag.documents(source_type, source_uri, source_version, title, language, content_hash, status, metadata, indexed_at, updated_at)
  values ('internal_doc', p_source_uri, coalesce(p_source_version, '1'), p_title, 'und', p_content_hash, 'indexed', coalesce(p_metadata, '{}'::jsonb), now(), now())
  on conflict (source_uri, content_hash) do update
    set source_version = excluded.source_version,
        title = excluded.title,
        status = 'indexed',
        metadata = excluded.metadata,
        indexed_at = now(),
        updated_at = now()
  returning id into v_id;
  return v_id;
end;
$function$;

create or replace function public.replace_rag_document_chunks(
  p_document_id uuid,
  p_chunks jsonb
)
returns integer
language plpgsql
set search_path = ''
as $function$
declare v_count integer;
begin
  if jsonb_typeof(coalesce(p_chunks, '[]'::jsonb)) <> 'array' then
    raise exception 'p_chunks must be a JSON array';
  end if;
  delete from rag.document_chunks where document_id = p_document_id;
  insert into rag.document_chunks(
    document_id, chunk_index, content, content_hash, token_count,
    embedding, embedding_model, metadata
  )
  select p_document_id, x.chunk_index, x.content, x.content_hash, x.token_count,
         (x.embedding::text)::extensions.vector, x.embedding_model, coalesce(x.metadata, '{}'::jsonb)
  from jsonb_to_recordset(coalesce(p_chunks, '[]'::jsonb)) as x(
    chunk_index integer, content text, content_hash text, token_count integer,
    embedding jsonb, embedding_model text, metadata jsonb
  )
  order by x.chunk_index;
  get diagnostics v_count = row_count;
  return v_count;
end;
$function$;

create or replace function public.rag_connector_health()
returns jsonb
language sql
stable
set search_path = ''
as $function$
  select jsonb_build_object(
    'documents', (select count(*) from rag.documents),
    'chunks', (select count(*) from rag.document_chunks),
    'status', 'ok'
  );
$function$;

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

revoke all on function public.upsert_rag_document(text, text, text, text, jsonb) from public, anon, authenticated;
revoke all on function public.replace_rag_document_chunks(uuid, jsonb) from public, anon, authenticated;
revoke all on function public.rag_connector_health() from public, anon, authenticated;
revoke all on function public.match_rag_chunks(extensions.vector, integer, jsonb) from public, anon, authenticated;
grant execute on function public.upsert_rag_document(text, text, text, text, jsonb) to service_role;
grant execute on function public.replace_rag_document_chunks(uuid, jsonb) to service_role;
grant execute on function public.rag_connector_health() to service_role;
grant execute on function public.match_rag_chunks(extensions.vector, integer, jsonb) to service_role;
