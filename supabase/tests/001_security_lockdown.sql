BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(5);

SELECT ok(
    EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon'),
    'anon role exists in the Supabase cluster'
);

SELECT ok(
    EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'),
    'authenticated role exists in the Supabase cluster'
);

SELECT ok(
    NOT has_table_privilege('anon', 'public.organisations', 'SELECT'),
    'anon cannot select organisations'
);

SELECT ok(
    NOT has_table_privilege('authenticated', 'public.ingestion_runs', 'SELECT'),
    'authenticated cannot select ingestion_runs'
);

SELECT ok(
    has_table_privilege('service_role', 'public.ingestion_runs', 'SELECT'),
    'service_role keeps backend access to ingestion_runs'
);

SELECT * FROM finish();

ROLLBACK;
