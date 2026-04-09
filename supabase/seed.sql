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
    ('EUR', 'Euro', 'EUR', 978, 2, 10, TRUE),
    ('USD', 'US Dollar', '$', 840, 2, 20, TRUE),
    ('GBP', 'Pound Sterling', 'GBP', 826, 2, 30, TRUE),
    ('CHF', 'Swiss Franc', 'CHF', 756, 2, 40, TRUE),
    ('JPY', 'Japanese Yen', 'JPY', 392, 0, 50, TRUE),
    ('CAD', 'Canadian Dollar', 'CAD', 124, 2, 60, TRUE),
    ('AUD', 'Australian Dollar', 'AUD', 36, 2, 70, TRUE),
    ('SEK', 'Swedish Krona', 'SEK', 752, 2, 80, TRUE),
    ('NOK', 'Norwegian Krone', 'NOK', 578, 2, 90, TRUE),
    ('DKK', 'Danish Krone', 'DKK', 208, 2, 100, TRUE),
    ('SGD', 'Singapore Dollar', 'SGD', 702, 2, 110, TRUE),
    ('HKD', 'Hong Kong Dollar', 'HKD', 344, 2, 120, TRUE),
    ('CNH', 'Offshore Renminbi', 'CNH', NULL, 2, 130, TRUE)
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    symbol = EXCLUDED.symbol,
    iso_numeric = EXCLUDED.iso_numeric,
    decimals = EXCLUDED.decimals,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;


INSERT INTO asset_classes (
    code,
    ice_code,
    name,
    description,
    sort_order,
    is_active
)
VALUES
    ('EQUITY', 'EQ', 'Equity', 'Listed equities and equity-linked instruments.', 10, TRUE),
    ('FX', 'FX', 'Foreign Exchange', 'FX spot, forwards, swaps, options, and structured FX products.', 20, TRUE),
    ('RATES', 'IR', 'Rates', 'Interest-rate products including swaps, swaptions, and bonds.', 30, TRUE),
    ('CREDIT', NULL, 'Credit', 'Credit derivatives, bonds, and spread products.', 40, TRUE),
    ('COMMODITY', 'CD', 'Commodity', 'Commodity-linked derivatives and underlyings.', 50, TRUE),
    ('HYBRID', 'HB', 'Hybrid', 'Hybrid and cross-asset products combining multiple risk buckets.', 55, TRUE),
    ('INDEX', NULL, 'Index', 'Equity, credit, or macro indices used as instruments or underlyings.', 60, TRUE),
    ('FUND', NULL, 'Fund', 'Fund interests, NAV-linked products, and fund exposures.', 70, TRUE),
    ('ETF', NULL, 'ETF', 'Exchange-traded funds and ETF-linked products.', 80, TRUE),
    ('VOL', NULL, 'Volatility', 'Volatility-linked products and variance instruments.', 90, TRUE),
    ('OTHER', NULL, 'Other', 'Temporary fallback for instruments not yet classified.', 999, TRUE)
ON CONFLICT (code) DO UPDATE
SET
    ice_code = EXCLUDED.ice_code,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;
