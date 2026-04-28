-- ============================================================
-- AEGIS - official migration: login quotes seed data
--
-- Scope:
--   - seed quotes for login page display
--
-- Notes:
--   - These quotes are displayed on the login page
--   - quotes is created in 20260409020000_init_shared_reference.sql
--   - Not tenant-scoped, shared across all users
-- ============================================================


-- ============================================================
-- SEED INITIAL QUOTES
-- ============================================================

INSERT INTO quotes (quote, author, sort_order) VALUES
    ('Discipline is choosing between what you want now and what you want most.', 'Abraham Lincoln', 10),
    ('Risk comes from not knowing what you''re doing.', 'Warren Buffett', 20),
    ('The first rule is not to lose. The second rule is not to forget the first rule.', 'Warren Buffett', 30),
    ('In investing, what is comfortable is rarely profitable.', 'Robert Arnott', 40)
ON CONFLICT (quote, author) DO NOTHING;
