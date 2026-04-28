BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(5);

INSERT INTO countries (
    id_country,
    iso2,
    iso3,
    name,
    official_name,
    region,
    sub_region
)
VALUES
    (
        950001,
        'XT',
        'XTT',
        'Testland',
        'Republic of Testland',
        'Test Region',
        'Test Subregion'
    );

INSERT INTO cities (
    id_city,
    id_country,
    name,
    ascii_name,
    admin_area,
    timezone_name
)
VALUES
    (
        950001,
        950001,
        'Test City',
        'Test City',
        'Test Admin',
        'Europe/Luxembourg'
    );

SELECT is(
    (
        SELECT name
        FROM countries
        WHERE iso2 = 'XT'
    ),
    'Testland',
    'countries stores global ISO-style country references'
);

SELECT is(
    (
        SELECT countries.iso2
        FROM cities
        JOIN countries USING (id_country)
        WHERE cities.id_city = 950001
    ),
    'XT',
    'cities links back to countries'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO cities (
            id_city,
            id_country,
            name,
            admin_area
        )
        VALUES
            (950002, 950001, 'Test City', 'Test Admin');
        RAISE EXCEPTION 'expected unique_violation for duplicate city/admin area';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('cities are unique by country, name, and admin area');

INSERT INTO organisations (
    id_org,
    code,
    legal_name,
    display_name
)
VALUES
    (950001, 'TESTORG_LOC', 'Test Org Location', 'Test Org Location');

INSERT INTO offices (
    id_off,
    id_org,
    code,
    name,
    id_city,
    timezone_name
)
VALUES
    (
        950001,
        950001,
        'LOC',
        'Location Office',
        950001,
        'Europe/Luxembourg'
    );

SELECT is(
    (
        SELECT id_city
        FROM offices
        WHERE id_off = 950001
    ),
    950001::BIGINT,
    'offices can reference normalized cities'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO offices (
            id_off,
            id_org,
            code,
            name,
            id_city
        )
        VALUES
            (950002, 950001, 'BADLOC', 'Bad Location Office', 999999999);
        RAISE EXCEPTION 'expected foreign_key_violation for unknown office city';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('offices reject unknown normalized cities');

SELECT * FROM finish();

ROLLBACK;
