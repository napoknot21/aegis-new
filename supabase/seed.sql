-- Local seed data only.
-- Keep this file free of production or sensitive data.

-- ============================================================
-- SHARED REFERENCES
-- Safe to replay locally.
-- ============================================================

INSERT INTO currencies (
    code,
    name,
    symbol,
    iso_numeric,
    decimals,
    sort_order,
    is_active
)
VALUES
    ('EUR', 'Euro',               '€',  978,  3, 10,  TRUE),
    ('USD', 'US Dollar',          '$',  840,  3, 20,  TRUE),
    ('GBP', 'Pound Sterling',     '£',  826,  3, 30,  TRUE),
    ('CHF', 'Swiss Franc',        'Fr', 756,  3, 40,  TRUE),
    ('JPY', 'Japanese Yen',       '¥',  392,  3, 50,  TRUE),
    ('CAD', 'Canadian Dollar',    '$',  124,  3, 60,  TRUE),
    ('AUD', 'Australian Dollar',  '$',  36,   3, 70,  TRUE),
    ('SEK', 'Swedish Krona',      'kr', 752,  3, 80,  TRUE),
    ('NOK', 'Norwegian Krone',    'kr', 578,  3, 90,  TRUE),
    ('DKK', 'Danish Krone',       'kr', 208,  3, 100, TRUE),
    ('SGD', 'Singapore Dollar',   '$',  702,  3, 110, TRUE),
    ('HKD', 'Hong Kong Dollar',   '$',  344,  3, 120, TRUE),
    ('CNH', 'Offshore Renminbi',  '¥',  NULL, 3, 130, TRUE)
ON CONFLICT (code) DO UPDATE
SET
    symbol      = EXCLUDED.symbol,
    iso_numeric = EXCLUDED.iso_numeric,
    decimals    = EXCLUDED.decimals,
    sort_order  = EXCLUDED.sort_order,
    is_active   = EXCLUDED.is_active;


INSERT INTO asset_classes (
    code,
    ice_code,
    name,
    description,
    sort_order,
    is_active
)
VALUES
    ('FX', 'FX', 'Foreign Exchange', 'FX spot, forwards, swaps, options, and structured FX products.', 10, TRUE),
    ('EQUITY', 'EQ', 'Equity', 'Listed equities and equity-linked instruments.', 20, TRUE),
    ('CASH', 'Cash', 'Cash', 'Cash and cash equivalents including deposits and money market instruments.', 25, TRUE),
    ('RATES', 'IR', 'Rates', 'Interest-rate products including swaps, swaptions, and bonds.', 30, TRUE),
    ('COMMODITY', 'CD', 'Commodity', 'Commodity-linked derivatives and underlyings.', 40, TRUE),
    ('HYBRID', 'HB', 'Hybrid', 'Hybrid and cross-asset products combining multiple risk buckets.', 55, TRUE),
    ('OTHER', NULL, 'Other', 'Temporary fallback for instruments not yet classified.', 999, TRUE)

ON CONFLICT (code) DO UPDATE
SET
    ice_code = EXCLUDED.ice_code,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;
