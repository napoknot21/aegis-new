import { createClient } from '@supabase/supabase-js';

// React (Vite) uses import.meta.env instead of process.env for environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);
