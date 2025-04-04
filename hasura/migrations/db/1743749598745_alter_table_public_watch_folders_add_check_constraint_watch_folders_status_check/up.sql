alter table "public"."watch_folders" drop constraint "watch_folders_status_check";
alter table "public"."watch_folders" add constraint "watch_folders_status_check" check (status = ANY (ARRAY['idle'::text, 'scanned'::text, 'active'::text, 'error'::text]));
