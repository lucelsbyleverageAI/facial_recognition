alter table "public"."cards" drop constraint "cards_status_check";
alter table "public"."cards" add constraint "cards_status_check" check (status = ANY (ARRAY['pending'::text,'generating_embeddings'::text, 'paused'::text, 'processing'::text, 'complete'::text]));
