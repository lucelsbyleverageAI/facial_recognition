alter table "public"."cards" drop constraint "cards_status_check";
alter table "public"."cards" add constraint "cards_status_check" check (status = ANY (ARRAY['pending'::text, 'paused'::text, 'generating_embeddings'::text, 'processing'::text, 'error'::text, 'complete'::text]));
