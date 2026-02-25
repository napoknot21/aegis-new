#!/usr/bin/env python3
"""
scripts/populate_db.py  ·  Aegis — Demo Data Population
─────────────────────────────────────────────────────────
Run AFTER create_db.py (schema + catalogue seed must exist first).

    python create_db.py   --db-path aegis.db
    python populate_db.py --db-path aegis.db

What this populates
───────────────────
  REAL data (from your actual structure):
    organisations       Heroics Capital (provider) + 2 clients
    offices             Luxembourg (discretionary) · Monaco (advisory)
    dept_office_map     which departments live in which office
    dept_position_map   position display overrides (e.g. "Trader Quant")
    funds               HV · WR (Heroics) + AGF (Client Alpha)
    fund_data_paths     all 22 data_type paths per Heroics fund
    users               full Heroics team (Lux + Monaco) + client users
    user_fund_access    explicit grants for provider staff on client funds

  SIMULATED data (realistic but invented):
    control_breaches    ~40 breaches across HV/WR, various statuses
    breach_comments     RM + PM comments on each breach
    breach_attachments  file references on some breaches
    nav_history         2 years of daily NAV per fund
    subred_aum          monthly AUM per fund
    audit_log           system events (login, breach run, exports…)
    chat_messages       compliance channel messages

Safe to re-run — uses INSERT OR IGNORE everywhere.
"""

import os
import sys
import json
import random
import sqlite3
import hashlib
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(42)

# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

def fk(cur, table, col, val):
    """Fetch a single ID by a column value. Raises if not found."""
    row = cur.execute(f"SELECT id FROM {table} WHERE {col}=?", (val,)).fetchone()
    if not row:
        raise ValueError(f"[!] {table}.{col}={val!r} not found — run create_db.py first")
    return row[0]


def business_days(start: date, end: date):
    """Return list of weekdays between start and end inclusive."""
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def fake_hash(name: str) -> str:
    """Deterministic fake bcrypt-like hash for demo users."""
    return "$2b$12$" + hashlib.sha256(name.encode()).hexdigest()[:53]


def isodt(d):
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


# ════════════════════════════════════════════════════════════════════
# 1. ORGANISATIONS
# ════════════════════════════════════════════════════════════════════

ORGS = [
    # (name, slug, is_provider, country)
    ("Heroics Capital",      "heroics",      1, "LU"),
    ("Client Alpha",         "client_alpha", 0, "FR"),
    ("Client Beta",          "client_beta",  0, "GB"),
]

def seed_orgs(cur):
    for name, slug, is_prov, country in ORGS:
        cur.execute(
            "INSERT OR IGNORE INTO organisations (name,slug,is_provider,country) VALUES (?,?,?,?)",
            (name, slug, is_prov, country))
    print(f"  [+] organisations: {len(ORGS)}")


# ════════════════════════════════════════════════════════════════════
# 2. OFFICES  (Heroics only — clients get one implicit office each)
# ════════════════════════════════════════════════════════════════════

# (org_slug, name, city, country_code, office_type)
OFFICES = [
    ("heroics",      "Luxembourg", "Luxembourg City", "LU", "discretionary"),
    ("heroics",      "Monaco",     "Monaco",          "MC", "advisory"),
    ("client_alpha", "Paris",      "Paris",           "FR", "advisory"),
    ("client_beta",  "London",     "London",          "GB", "discretionary"),
]

def seed_offices(cur):
    for org_slug, name, city, cc, otype in OFFICES:
        org_id = fk(cur, "organisations", "slug", org_slug)
        cur.execute(
            "INSERT OR IGNORE INTO offices (org_id,name,city,country_code,office_type) VALUES (?,?,?,?,?)",
            (org_id, name, city, cc, otype))
    print(f"  [+] offices: {len(OFFICES)}")


# ════════════════════════════════════════════════════════════════════
# 3. DEPT-OFFICE MAP  (which departments exist in which office)
# ════════════════════════════════════════════════════════════════════

# (office: org_slug+name, departments)
DEPT_OFFICE = {
    ("heroics", "Luxembourg"): ["PM","RM","Research","Technology","Compliance","Board","Admin"],
    ("heroics", "Monaco"):     ["Compliance","Sales","Advisory","Board","Admin"],
    ("client_alpha", "Paris"): ["PM","RM","Compliance","Admin"],
    ("client_beta","London"):  ["PM","RM","Compliance","Admin"],
}

def seed_dept_office_map(cur):
    count = 0
    for (org_slug, office_name), depts in DEPT_OFFICE.items():
        org_id    = fk(cur, "organisations", "slug", org_slug)
        office_id = cur.execute(
            "SELECT id FROM offices WHERE org_id=? AND name=?", (org_id, office_name)
        ).fetchone()[0]
        for dept_name in depts:
            dept_id = fk(cur, "departments", "name", dept_name)
            cur.execute(
                "INSERT OR IGNORE INTO dept_office_map (department_id,office_id) VALUES (?,?)",
                (dept_id, office_id))
            count += 1
    print(f"  [+] dept_office_map: {count} entries")


# ════════════════════════════════════════════════════════════════════
# 4. DEPT-POSITION MAP  (valid positions per dept + display overrides)
# ════════════════════════════════════════════════════════════════════

# (dept_name, pos_name, display_name_override or None)
DEPT_POSITION = [
    # PM — "officer" is displayed as "Trader Quant" internally
    ("PM", "intern",   None),
    ("PM", "analyst",  "Junior Trader"),
    ("PM", "officer",  "Trader Quant"),       # ← your specific title
    ("PM", "senior",   "Senior Trader"),
    ("PM", "deputy",   "Deputy PM"),
    ("PM", "head_of",  "Head of Trading"),
    # RM
    ("RM", "intern",   None),
    ("RM", "analyst",  None),
    ("RM", "officer",  None),
    ("RM", "senior",   None),
    ("RM", "deputy",   None),
    ("RM", "head_of",  None),
    # Research
    ("Research", "intern",  None),
    ("Research", "analyst", "Research Analyst"),
    ("Research", "officer", "Senior Research Analyst"),
    ("Research", "senior",  None),
    ("Research", "head_of", "Head of Research"),
    # Technology
    ("Technology", "intern",  "Dev Intern"),
    ("Technology", "analyst", "Developer"),
    ("Technology", "officer", "Senior Developer"),
    ("Technology", "senior",  "Lead Developer"),
    ("Technology", "head_of", "Head of Technology"),
    # Compliance
    ("Compliance", "intern",  None),
    ("Compliance", "analyst", None),
    ("Compliance", "officer", "Compliance Officer"),
    ("Compliance", "senior",  "Senior Compliance Officer"),
    ("Compliance", "deputy",  "Deputy Compliance"),
    ("Compliance", "head_of", "Head of Compliance"),
    # Sales (Monaco)
    ("Sales", "intern",  None),
    ("Sales", "analyst", "Sales Analyst"),
    ("Sales", "officer", "Sales Advisor"),
    ("Sales", "senior",  "Senior Sales Advisor"),
    ("Sales", "head_of", "Head of Sales"),
    # Advisory (Monaco)
    ("Advisory", "intern",  None),
    ("Advisory", "analyst", "Junior Advisor"),
    ("Advisory", "officer", "Advisor"),
    ("Advisory", "senior",  "Senior Advisor"),
    ("Advisory", "head_of", "Head of Advisory"),
    # Board
    ("Board", "board_member",   None),
    ("Board", "board_director", "Managing Director"),
    # Admin — all positions valid
    ("Admin", "intern",   None),
    ("Admin", "analyst",  None),
    ("Admin", "officer",  None),
    ("Admin", "senior",   None),
    ("Admin", "deputy",   None),
    ("Admin", "head_of",  None),
]

def seed_dept_position_map(cur):
    for dept_name, pos_name, override in DEPT_POSITION:
        dept_id = fk(cur, "departments", "name", dept_name)
        pos_id  = fk(cur, "positions",   "name", pos_name)
        cur.execute(
            "INSERT OR IGNORE INTO dept_position_map (department_id,position_id,display_name_override) VALUES (?,?,?)",
            (dept_id, pos_id, override))
    print(f"  [+] dept_position_map: {len(DEPT_POSITION)} entries")


# ════════════════════════════════════════════════════════════════════
# 5. FUNDS + DATA PATHS
# ════════════════════════════════════════════════════════════════════

FUNDS = [
    # (org_slug, name, slug, currency, inception_date)
    ("heroics",      "Heroics Volatility Fund",  "HV",  "EUR", "2018-03-01"),
    ("heroics",      "Heroics Westridge Fund",   "WR",  "EUR", "2020-06-01"),
    ("client_alpha", "Alpha Growth Fund",         "AGF", "EUR", "2021-01-15"),
    ("client_beta",  "Beta Fixed Income Fund",    "BFI", "GBP", "2019-09-01"),
]

# Data types matching your folder structure
DATA_TYPES = [
    "NAV", "NAV_Estimate", "Leverage", "Leverage_Per_Trade", "Leverage_Per_Underlying",
    "SIMM", "Portfolio_View", "Counterparty_Concentration", "Cross_Delta", "Cross_Gamma",
    "Delta_P&L_Stress", "Delta_Stress_%_NAV", "Delta_Stress_Abs", "Expiries",
    "Gamma_P&L", "Long_Short_Delta", "Overview_Risks_Credit", "Overview_Risks_Equity_FX",
    "Plot_Risk", "Split_View", "Vega_Bucket", "Vega_Stress_P&L",
]

BASE_PATH = r"N:\INVESTMENT MANAGEMENT"

def fund_path(org_name: str, fund_slug: str, data_type: str) -> str:
    """Build a realistic Windows path matching your structure."""
    org_part = org_name.upper().replace(" ", "_")
    return rf"{BASE_PATH}\{org_part}\{fund_slug}\{data_type}"

def seed_funds(cur):
    for org_slug, name, slug, currency, inception in FUNDS:
        org_id = fk(cur, "organisations", "slug", org_slug)
        cur.execute(
            "INSERT OR IGNORE INTO funds (org_id,name,slug,currency,inception_date) VALUES (?,?,?,?,?)",
            (org_id, name, slug, currency, inception))

    # Fund data paths for Heroics funds only (HV + WR)
    paths_count = 0
    for org_slug, org_name, slug, _, _ in FUNDS:
        org_id  = fk(cur, "organisations", "slug", org_slug)
        fund_id = cur.execute("SELECT id FROM funds WHERE org_id=? AND slug=?", (org_id, slug)).fetchone()[0]
        for dt in DATA_TYPES:
            path = fund_path(org_name, slug, dt)
            cur.execute(
                "INSERT OR IGNORE INTO fund_data_paths (fund_id,data_type,path) VALUES (?,?,?)",
                (fund_id, dt, path))
            paths_count += 1

    print(f"  [+] funds: {len(FUNDS)}  ·  fund_data_paths: {paths_count}")


# ════════════════════════════════════════════════════════════════════
# 6. USERS
# ════════════════════════════════════════════════════════════════════
#
# Real Heroics structure from conversation:
#   Luxembourg  — PM (Trader Quant), RM, Research, Technology, Compliance, Board, Admin
#   Monaco      — Compliance, Sales, Advisory, Board, Admin
#   Clients     — Admin + basic PM/RM/Compliance users

# (org_slug, office: (org_slug,name)|None, dept, pos, first, last, username, email)
USERS = [
    # ── HEROICS LUXEMBOURG ──────────────────────────────────────
    # PM team
    ("heroics", ("heroics","Luxembourg"), "PM", "head_of",  "Alexandre", "Fontaine",  "alex.fontaine",  "a.fontaine@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "PM", "deputy",   "Camille",   "Renard",    "cam.renard",     "c.renard@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "PM", "officer",  "Hugo",      "Marceau",   "hugo.marceau",   "h.marceau@heroics.lu"),   # Trader Quant
    ("heroics", ("heroics","Luxembourg"), "PM", "officer",  "Léa",       "Vidal",     "lea.vidal",      "l.vidal@heroics.lu"),     # Trader Quant
    ("heroics", ("heroics","Luxembourg"), "PM", "analyst",  "Thomas",    "Girard",    "t.girard",       "t.girard@heroics.lu"),    # Junior Trader
    ("heroics", ("heroics","Luxembourg"), "PM", "intern",   "Emma",      "Petit",     "emma.petit",     "e.petit@heroics.lu"),
    # RM team
    ("heroics", ("heroics","Luxembourg"), "RM", "head_of",  "Nathalie",  "Dubois",    "nat.dubois",     "n.dubois@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "RM", "deputy",   "Marc",      "Lefevre",   "marc.lefevre",   "m.lefevre@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "RM", "officer",  "Sophie",    "Laurent",   "soph.laurent",   "s.laurent@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "RM", "analyst",  "Nicolas",   "Bernard",   "nic.bernard",    "n.bernard@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "RM", "intern",   "Julie",     "Moreau",    "julie.moreau",   "j.moreau@heroics.lu"),
    # Research
    ("heroics", ("heroics","Luxembourg"), "Research", "head_of", "Pierre",  "Rousseau",  "pierre.rousseau","p.rousseau@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "Research", "officer", "Clara",   "Simon",     "clara.simon",    "c.simon@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "Research", "intern",  "Antoine", "Leroy",     "ant.leroy",      "a.leroy@heroics.lu"),
    # Technology
    ("heroics", ("heroics","Luxembourg"), "Technology", "head_of", "Julien",  "Martin",   "jul.martin",    "j.martin@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "Technology", "senior",  "Laura",   "Thomas",   "laura.thomas",  "l.thomas@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "Technology", "intern",  "Kevin",   "Robert",   "kevin.robert",  "k.robert@heroics.lu"),
    # Compliance Luxembourg
    ("heroics", ("heroics","Luxembourg"), "Compliance", "head_of", "Isabelle","Durand",   "isa.durand",    "i.durand@heroics.lu"),
    ("heroics", ("heroics","Luxembourg"), "Compliance", "officer", "Mathieu", "Blanc",    "math.blanc",    "m.blanc@heroics.lu"),
    # Board / Direction Générale (can see both offices)
    ("heroics", ("heroics","Luxembourg"), "Board", "board_director", "François","Dupont",  "francois.dupont","f.dupont@heroics.lu"),  # DG / Co-founder
    ("heroics", ("heroics","Luxembourg"), "Board", "board_member",   "Marie",   "Leconte", "marie.leconte", "m.leconte@heroics.lu"),  # Co-founder
    # Admin Heroics (god mode)
    ("heroics", ("heroics","Luxembourg"), "Admin", "head_of", "David",    "Admin",    "david.admin",    "d.admin@heroics.lu"),

    # ── HEROICS MONACO ──────────────────────────────────────────
    # Compliance Monaco
    ("heroics", ("heroics","Monaco"), "Compliance", "officer", "Chloé",   "Ferrari",  "chloe.ferrari",  "c.ferrari@heroics.mc"),
    # Sales
    ("heroics", ("heroics","Monaco"), "Sales", "head_of", "Raphael",  "Morel",    "raph.morel",     "r.morel@heroics.mc"),
    ("heroics", ("heroics","Monaco"), "Sales", "officer", "Amélie",   "Gauthier", "ame.gauthier",   "a.gauthier@heroics.mc"),
    ("heroics", ("heroics","Monaco"), "Sales", "intern",  "Lucas",    "Bonnet",   "lucas.bonnet",   "l.bonnet@heroics.mc"),
    # Advisory
    ("heroics", ("heroics","Monaco"), "Advisory", "head_of", "Élodie", "Chevalier","elo.chevalier",  "e.chevalier@heroics.mc"),
    ("heroics", ("heroics","Monaco"), "Advisory", "senior",  "Maxime",  "Faure",    "max.faure",      "m.faure@heroics.mc"),
    ("heroics", ("heroics","Monaco"), "Advisory", "intern",  "Inès",    "Roux",     "ines.roux",      "i.roux@heroics.mc"),

    # ── CLIENT ALPHA (Paris) ─────────────────────────────────────
    ("client_alpha", ("client_alpha","Paris"), "Admin",      "head_of", "Jean",    "Dupuis",   "jean.dupuis",    "j.dupuis@alpha.fr"),
    ("client_alpha", ("client_alpha","Paris"), "PM",         "head_of", "Claire",  "Mercier",  "claire.mercier", "c.mercier@alpha.fr"),
    ("client_alpha", ("client_alpha","Paris"), "RM",         "officer", "Paul",    "Garnier",  "paul.garnier",   "p.garnier@alpha.fr"),
    ("client_alpha", ("client_alpha","Paris"), "Compliance", "officer", "Anne",    "Fournier", "anne.fournier",  "a.fournier@alpha.fr"),

    # ── CLIENT BETA (London) ─────────────────────────────────────
    ("client_beta",  ("client_beta","London"),  "Admin",     "head_of", "James",   "Wilson",   "james.wilson",   "j.wilson@beta.co.uk"),
    ("client_beta",  ("client_beta","London"),  "PM",        "head_of", "Sarah",   "Johnson",  "sarah.johnson",  "s.johnson@beta.co.uk"),
    ("client_beta",  ("client_beta","London"),  "RM",        "officer", "Oliver",  "Brown",    "oliver.brown",   "o.brown@beta.co.uk"),
]

def seed_users(cur):
    for org_slug, office_ref, dept, pos, first, last, uname, email in USERS:
        org_id = fk(cur, "organisations", "slug", org_slug)
        dept_id = fk(cur, "departments", "name", dept)
        pos_id  = fk(cur, "positions",   "name", pos)

        office_id = None
        if office_ref:
            o_org_id = fk(cur, "organisations", "slug", office_ref[0])
            row = cur.execute(
                "SELECT id FROM offices WHERE org_id=? AND name=?", (o_org_id, office_ref[1])
            ).fetchone()
            if row:
                office_id = row[0]

        cur.execute("""
            INSERT OR IGNORE INTO users
              (org_id, office_id, department_id, position_id,
               first_name, last_name, username, email, hashed_password)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (org_id, office_id, dept_id, pos_id, first, last, uname, email, fake_hash(uname)))

    print(f"  [+] users: {len(USERS)}")


# ════════════════════════════════════════════════════════════════════
# 7. USER FUND ACCESS  (explicit grants for provider staff on client funds)
# ════════════════════════════════════════════════════════════════════

# (user_username, fund: (org_slug, slug), access_level, notes)
USER_FUND_ACCESS = [
    # Heroics RM team → Client Alpha AGF
    ("nat.dubois",   ("client_alpha","AGF"), "read_write", "Head of RM — full CSSF monitoring mandate"),
    ("marc.lefevre", ("client_alpha","AGF"), "read_write", "Deputy RM — backup validator"),
    ("soph.laurent", ("client_alpha","AGF"), "read",       "RM Officer — monitoring only"),
    # Heroics PM → Client Alpha AGF
    ("alex.fontaine",("client_alpha","AGF"), "read_write", "Head of Trading — risk oversight"),
    # Heroics Compliance → Client Alpha AGF
    ("isa.durand",   ("client_alpha","AGF"), "read_write", "Head of Compliance — CSSF reporting"),
    ("math.blanc",   ("client_alpha","AGF"), "read",       "Compliance Officer — monitoring"),
    # Advisory Monaco → Client Alpha AGF (advisory mandate)
    ("elo.chevalier",("client_alpha","AGF"), "read",       "Advisory mandate — portfolio review"),
    # Heroics RM → Client Beta BFI
    ("nat.dubois",   ("client_beta","BFI"),  "read_write", "Head of RM — multi-client mandate"),
    ("marc.lefevre", ("client_beta","BFI"),  "read",       "Deputy RM — monitoring"),
    ("isa.durand",   ("client_beta","BFI"),  "read_write", "Head of Compliance — CSSF"),
    # Head of Technology → both clients (maintenance access)
    ("jul.martin",   ("client_alpha","AGF"), "read",       "Tech access — system maintenance"),
    ("jul.martin",   ("client_beta","BFI"),  "read",       "Tech access — system maintenance"),
]

def seed_user_fund_access(cur):
    # Use david.admin as the granter (Provider Admin)
    admin_id = cur.execute("SELECT id FROM users WHERE username='david.admin'").fetchone()[0]

    for uname, (org_slug, fund_slug), level, notes in USER_FUND_ACCESS:
        user_id = cur.execute("SELECT id FROM users WHERE username=?", (uname,)).fetchone()[0]
        org_id  = fk(cur, "organisations", "slug", org_slug)
        fund_id = cur.execute("SELECT id FROM funds WHERE org_id=? AND slug=?", (org_id, fund_slug)).fetchone()[0]
        cur.execute("""
            INSERT OR IGNORE INTO user_fund_access
              (user_id, fund_id, access_level, granted_by, notes)
            VALUES (?,?,?,?,?)
        """, (user_id, fund_id, level, admin_id, notes))

    print(f"  [+] user_fund_access: {len(USER_FUND_ACCESS)} grants")


# ════════════════════════════════════════════════════════════════════
# 8. SIMULATED — NAV HISTORY
# ════════════════════════════════════════════════════════════════════

PORTFOLIOS_BY_FUND = {
    "HV":  ["EQ_BOOK", "FX_BOOK", "RATES_BOOK", "TOTAL"],
    "WR":  ["EQUITY_EU", "EQUITY_US", "CREDIT", "TOTAL"],
    "AGF": ["GROWTH", "VALUE", "TOTAL"],
    "BFI": ["IG_BONDS", "HY_BONDS", "TOTAL"],
}

def seed_nav_history(cur):
    rows = 0
    start = date(2023, 1, 2)
    end   = date(2025, 2, 28)
    days  = business_days(start, end)

    for org_slug, _, fund_slug, _, _ in FUNDS:
        org_id  = fk(cur, "organisations", "slug", org_slug)
        fund_id = cur.execute("SELECT id FROM funds WHERE org_id=? AND slug=?", (org_id, fund_slug)).fetchone()[0]
        portfolios = PORTFOLIOS_BY_FUND.get(fund_slug, ["TOTAL"])

        nav_base = {p: random.uniform(5e6, 20e6) for p in portfolios if p != "TOTAL"}

        for d in days:
            total_mv = 0.0
            for ptf in portfolios:
                if ptf == "TOTAL":
                    continue
                drift = random.gauss(0.0002, 0.007)
                nav_base[ptf] *= (1 + drift)
                mv  = round(nav_base[ptf], 2)
                total_nav_ref = sum(nav_base.values())
                pct = round((mv / total_nav_ref) * 100, 4) if total_nav_ref else 0
                total_mv += mv
                cur.execute(
                    "INSERT OR IGNORE INTO nav_history (fund_id,portfolio_name,mv,mv_nav_pct,date) VALUES (?,?,?,?,?)",
                    (fund_id, ptf, mv, pct, isodt(d)))
                rows += 1

            # TOTAL row
            total_nav_ref = sum(nav_base.values()) or 1
            pct = round((total_mv / total_nav_ref) * 100, 4)
            cur.execute(
                "INSERT OR IGNORE INTO nav_history (fund_id,portfolio_name,mv,mv_nav_pct,date) VALUES (?,?,?,?,?)",
                (fund_id, "TOTAL", round(total_mv, 2), pct, isodt(d)))
            rows += 1

    print(f"  [+] nav_history: {rows:,} rows  ({len(days)} trading days × {len(FUNDS)} funds)")


# ════════════════════════════════════════════════════════════════════
# 9. SIMULATED — SUBRED AUM
# ════════════════════════════════════════════════════════════════════

def seed_subred_aum(cur):
    rows = 0
    d = date(2023, 1, 31)
    end = date(2025, 2, 28)
    while d <= end:
        for org_slug, _, fund_slug, currency, _ in FUNDS:
            org_id  = fk(cur, "organisations", "slug", org_slug)
            fund_id = cur.execute("SELECT id FROM funds WHERE org_id=? AND slug=?", (org_id, fund_slug)).fetchone()[0]
            base_aum = {"HV": 85_000_000, "WR": 42_000_000, "AGF": 120_000_000, "BFI": 200_000_000}
            aum = int(base_aum.get(fund_slug, 50_000_000) * random.uniform(0.95, 1.05))
            cur.execute(
                "INSERT OR IGNORE INTO subred_aum (fund_id,date,amount,currency) VALUES (?,?,?,?)",
                (fund_id, isodt(d), aum, currency))
            rows += 1
        # Next month end
        if d.month == 12:
            d = date(d.year + 1, 1, 31)
        else:
            import calendar
            last_day = calendar.monthrange(d.year, d.month + 1)[1]
            d = date(d.year, d.month + 1, last_day)
    print(f"  [+] subred_aum: {rows} rows")


# ════════════════════════════════════════════════════════════════════
# 10. SIMULATED — CONTROL BREACHES + COMMENTS + ATTACHMENTS
# ════════════════════════════════════════════════════════════════════

BREACH_SCENARIOS = [
    # (fund_slug, control_code, zone_order, metric, value, level, status, days_ago)
    ("HV", "L01", 4, "Gross Leverage",    "305.2%", "300%", "resolved",      45),
    ("HV", "L01", 3, "Gross Leverage",    "294.1%", "290%", "resolved",      30),
    ("HV", "L01", 2, "Gross Leverage",    "277.8%", "275%", "resolved",      15),
    ("HV", "L01", 4, "Commitment Leverage","312.5%","300%", "cssf_notified",  5),
    ("HV", "L02", 3, "Delta/NAV%",        "31.2%",  "30%",  "under_review",   3),
    ("HV", "L02", 2, "Delta/NAV%",        "26.8%",  "25%",  "resolved",      20),
    ("HV", "S01", 3, "SIMM/NAV%",         "21.4%",  "20%",  "escalated",      7),
    ("HV", "S01", 2, "SIMM/NAV%",         "18.9%",  "18%",  "resolved",      25),
    ("HV", "D01", 3, "Delta/NAV%",        "27.5%",  "25%",  "resolved",      10),
    ("HV", "PL01",4, "1D Change (GAV)",   "2.3%",   "2.0%", "resolved",      60),
    ("HV", "PL01",3, "1D Change (GAV)",   "1.4%",   "1.0%", "under_review",   1),
    ("HV", "CR01",3, "MV/NAV%",           "28.9%",  "28%",  "open",           0),
    ("HV", "V01", 3, "Vega/NAV% Equity",  "2.7%",   "2.5%", "under_review",   2),
    ("WR", "L01", 3, "Gross Leverage",    "291.3%", "290%", "resolved",      18),
    ("WR", "L01", 4, "Gross Leverage",    "301.0%", "300%", "resolved",      40),
    ("WR", "L03", 3, "Exposure % NAV",    "31.5%",  "30%",  "resolved",      12),
    ("WR", "S02", 3, "Initial Margin",    "10.2M",  "10M",  "resolved",      22),
    ("WR", "PL02",3, "1D Change (Book)",  "0.61%",  "0.50%","under_review",   4),
    ("WR", "CR01",2, "MV/NAV%",           "26.1%",  "25%",  "resolved",      35),
    ("WR", "V02", 3, "Vega/NAV%",         "2.6%",   "2.5%", "open",           0),
    ("AGF","L01", 3, "Gross Leverage",    "293.7%", "290%", "resolved",      28),
    ("AGF","L01", 4, "Gross Leverage",    "307.2%", "300%", "cssf_notified",  8),
    ("AGF","S01", 2, "SIMM/NAV%",         "19.1%",  "18%",  "resolved",      15),
    ("BFI","L01", 2, "Gross Leverage",    "278.4%", "275%", "resolved",      50),
    ("BFI","PL01",3, "1D Change (GAV)",   "1.1%",   "1.0%", "resolved",      14),
]

def seed_breaches(cur):
    # Look up RM users for comments
    rm_officer  = cur.execute("SELECT id FROM users WHERE username='soph.laurent'").fetchone()[0]
    rm_deputy   = cur.execute("SELECT id FROM users WHERE username='marc.lefevre'").fetchone()[0]
    rm_head     = cur.execute("SELECT id FROM users WHERE username='nat.dubois'").fetchone()[0]
    pm_officer  = cur.execute("SELECT id FROM users WHERE username='hugo.marceau'").fetchone()[0]
    pm_head     = cur.execute("SELECT id FROM users WHERE username='alex.fontaine'").fetchone()[0]

    dept_rm     = fk(cur, "departments", "name", "RM")
    dept_pm     = fk(cur, "departments", "name", "PM")
    pos_officer = fk(cur, "positions",   "name", "officer")
    pos_deputy  = fk(cur, "positions",   "name", "deputy")
    pos_head    = fk(cur, "positions",   "name", "head_of")

    breach_ids = []
    for fund_slug, ctrl_code, zone_ord, metric, value, level, status, days_ago in BREACH_SCENARIOS:
        # Find fund
        fund_row = cur.execute(
            "SELECT f.id, f.org_id FROM funds f WHERE f.slug=?", (fund_slug,)
        ).fetchone()
        if not fund_row:
            continue
        fund_id, org_id = fund_row

        # Find control + zone
        ctrl_id = cur.execute(
            "SELECT id FROM control_definitions WHERE code=? AND org_id IS NULL", (ctrl_code,)
        ).fetchone()
        if not ctrl_id:
            continue
        ctrl_id = ctrl_id[0]
        zone_row = cur.execute(
            "SELECT id, cssf_notify_hours FROM control_zones WHERE control_id=? AND zone_order=?",
            (ctrl_id, zone_ord)
        ).fetchone()
        zone_id = zone_row[0] if zone_row else None
        cssf_h  = zone_row[1] if zone_row else None

        run_dt   = date.today() - timedelta(days=days_ago)
        run_str  = run_dt.strftime("%Y/%m/%d (%Hh%M)")
        cssf_dl  = isodt(datetime.combine(run_dt, datetime.min.time()) + timedelta(hours=cssf_h)) if cssf_h and days_ago <= 2 else None

        # Resolver info
        resolver = rm_head if status in ("resolved","cssf_notified","escalated") else None
        resolved_at = isodt(run_dt + timedelta(hours=random.randint(2,48))) if resolver else None

        cur.execute("""
            INSERT OR IGNORE INTO control_breaches
              (org_id, fund_id, control_id, zone_id, metric_name,
               run_date, breach_value, breach_level, status,
               resolved_by, resolved_at, cssf_deadline, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (org_id, fund_id, ctrl_id, zone_id, metric,
              run_str, value, level, status,
              resolver, resolved_at, cssf_dl, isodt(run_dt)))

        breach_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        breach_ids.append((breach_id, fund_slug, ctrl_code, status, run_dt))

    # ── Breach comments ───────────────────────────────────────────
    comment_templates_rm = [
        "Position reviewed — exposure driven by {metric} strategy. Within risk appetite on stress-adjusted basis.",
        "Leverage spike caused by FX revaluation on {date}. Positions partially unwound intraday.",
        "Reviewed with PM team. Breach attributable to market move, not new position-taking. Monitoring daily.",
        "AIFM notified. Deleveraging plan submitted to investment committee.",
        "{metric} breach investigated. Temporary — positions matured by close. No regulatory impact.",
        "Cross-checked against SIMM limits. Isolated position. RM validates no systemic risk.",
    ]
    comment_templates_pm = [
        "Market dislocation on {date}. Delta hedge executed — position normalized by next session.",
        "Strategy rationale: overweight maintained within Board-approved risk limits. No action required.",
        "Position unwound. Confirms RM assessment. Normal operations resumed.",
        "Approved hedging instrument added. Net exposure within limits post-hedge.",
    ]

    comments_added = 0
    for breach_id, fund_slug, ctrl_code, status, run_dt in breach_ids:
        if status == "open":
            continue   # no comments yet on fresh breaches

        # RM comment (always)
        rm_commenter = random.choice([rm_officer, rm_deputy, rm_head])
        rm_pos = {rm_officer: pos_officer, rm_deputy: pos_deputy, rm_head: pos_head}[rm_commenter]
        rm_text = random.choice(comment_templates_rm).format(
            metric=ctrl_code, date=run_dt.strftime("%d/%m/%Y"))
        comment_dt = isodt(run_dt + timedelta(hours=random.randint(1, 6)))
        cur.execute("""
            INSERT INTO breach_comments
              (breach_id, user_id, department_id, position_id, comment, created_at)
            VALUES (?,?,?,?,?,?)
        """, (breach_id, rm_commenter, dept_rm, rm_pos, rm_text, comment_dt))
        comments_added += 1

        # Second RM comment for resolved/cssf_notified
        if status in ("resolved","cssf_notified","escalated"):
            rm_text2 = "Confirmed resolved. Deleveraging confirmed at close. Reporting updated."
            cur.execute("""
                INSERT INTO breach_comments
                  (breach_id, user_id, department_id, position_id, comment, created_at)
                VALUES (?,?,?,?,?,?)
            """, (breach_id, rm_head, dept_rm, pos_head, rm_text2,
                  isodt(run_dt + timedelta(hours=random.randint(6,24)))))
            comments_added += 1

        # PM comment (for some breaches)
        if status in ("resolved","cssf_notified") and random.random() > 0.35:
            pm_commenter = random.choice([pm_officer, pm_head])
            pm_pos = {pm_officer: pos_officer, pm_head: pos_head}[pm_commenter]
            pm_text = random.choice(comment_templates_pm).format(date=run_dt.strftime("%d/%m/%Y"))
            cur.execute("""
                INSERT INTO breach_comments
                  (breach_id, user_id, department_id, position_id, comment, created_at)
                VALUES (?,?,?,?,?,?)
            """, (breach_id, pm_commenter, dept_pm, pm_pos, pm_text,
                  isodt(run_dt + timedelta(hours=random.randint(2,12)))))
            comments_added += 1

    # ── Breach attachments ────────────────────────────────────────
    attach_count = 0
    cssf_breaches = [(bid, fs, cc, st, rd) for (bid, fs, cc, st, rd) in breach_ids
                     if st in ("cssf_notified","escalated")]
    for breach_id, fund_slug, ctrl_code, status, run_dt in cssf_breaches[:6]:
        filename = f"justification_{ctrl_code}_{fund_slug}_{run_dt.strftime('%Y%m%d')}.pdf"
        stored_path = rf"N:\AEGIS\ATTACHMENTS\breaches\{breach_id}\{filename}"
        uploader = rm_head
        cur.execute("""
            INSERT OR IGNORE INTO breach_attachments
              (breach_id, comment_id, uploaded_by, original_name, stored_path, mime_type, file_size_bytes)
            VALUES (?,NULL,?,?,?,'application/pdf',?)
        """, (breach_id, uploader, filename, stored_path, random.randint(80_000, 500_000)))
        attach_count += 1

    print(f"  [+] control_breaches: {len(breach_ids)}  ·  comments: {comments_added}  ·  attachments: {attach_count}")


# ════════════════════════════════════════════════════════════════════
# 11. SIMULATED — CHAT MESSAGES
# ════════════════════════════════════════════════════════════════════

CHAT_MSGS = [
    ("compliance_general", "heroics",  "nat.dubois",    "Reminder: L01 quarterly review due next Friday. All RM officers please prepare your reports."),
    ("compliance_general", "heroics",  "isa.durand",    "CSSF circular 23/847 update — new AIFMD reporting requirements from Q1 2025. Will circulate summary."),
    ("compliance_general", "heroics",  "math.blanc",    "AGF breach notification sent to CSSF this morning. Reference: CSSF-2025-0142."),
    ("compliance_general", "heroics",  "nat.dubois",    "HV leverage back within limits after yesterday's unwind. Breach closed."),
    ("compliance_general", "heroics",  "francois.dupont","DG note: board reviewed Q4 risk report. Leverage limits confirmed at current levels for 2025."),
    ("risk_hv",            "heroics",  "soph.laurent",  "HV Delta spike this morning — equity book moved +2.1% vs index. Monitoring closely."),
    ("risk_hv",            "heroics",  "hugo.marceau",  "FX hedge executed. Net delta back within limits as of 14h30."),
    ("risk_hv",            "heroics",  "marc.lefevre",  "Confirmed — HV L01 zone 2 alert. Reviewing positions with PM team now."),
    ("risk_wr",            "heroics",  "soph.laurent",  "WR SIMM ratio at 19.1% — approaching pre-breach zone. Flagging now."),
    ("risk_wr",            "heroics",  "marc.lefevre",  "IM increased due to rate vol. Reviewing counterparty exposure with PM."),
]

def seed_chat(cur):
    for channel, org_slug, uname, msg in CHAT_MSGS:
        org_id  = fk(cur, "organisations", "slug", org_slug)
        user_row = cur.execute("SELECT id, username FROM users WHERE username=?", (uname,)).fetchone()
        if not user_row:
            continue
        user_id, username = user_row
        d = date.today() - timedelta(days=random.randint(0, 30))
        cur.execute("""
            INSERT INTO chat_messages (channel, org_id, user_id, username, message, created_at)
            VALUES (?,?,?,?,?,?)
        """, (channel, org_id, user_id, username, msg, isodt(d)))
    print(f"  [+] chat_messages: {len(CHAT_MSGS)}")


# ════════════════════════════════════════════════════════════════════
# 12. SIMULATED — AUDIT LOG
# ════════════════════════════════════════════════════════════════════

AUDIT_EVENTS = [
    ("nat.dubois",    "heroics", "breach.status.update",  "control_breaches:1",  {"from":"open","to":"under_review"}),
    ("marc.lefevre",  "heroics", "breach.validate",        "control_breaches:1",  {"status":"resolved"}),
    ("nat.dubois",    "heroics", "analysis.breach.run",    "control_breaches",    {"fund":"HV","controls_checked":21,"breaches_found":3}),
    ("nat.dubois",    "heroics", "analysis.breach.run",    "control_breaches",    {"fund":"WR","controls_checked":21,"breaches_found":2}),
    ("isa.durand",    "heroics", "report.cssf.export",     "control_breaches:4",  {"format":"PDF","reference":"CSSF-2025-0142"}),
    ("david.admin",   "heroics", "user.create",            "users:28",            {"username":"chloe.ferrari","dept":"Compliance"}),
    ("david.admin",   "heroics", "user.fund_access.grant", "user_fund_access",    {"user":"soph.laurent","fund":"AGF","level":"read"}),
    ("jul.martin",    "heroics", "fund.config.edit",       "fund_data_paths",     {"fund":"HV","data_type":"NAV","path_updated":True}),
    ("david.admin",   "heroics", "org.config.edit",        "organisations:2",     {"field":"name","old":"Client Alpha SA","new":"Client Alpha"}),
    ("jean.dupuis",   "client_alpha","user.create",        "users",               {"username":"anne.fournier"}),
    ("nat.dubois",    "heroics", "page.compliance.export", "pages:breach_validation",{"fund":"AGF","rows":12}),
    ("alex.fontaine", "heroics", "analysis.breach.run",    "control_breaches",    {"fund":"HV","trigger":"manual"}),
    ("nat.dubois",    "heroics", "breach.status.update",   "control_breaches:22", {"from":"open","to":"cssf_notified"}),
    ("isa.durand",    "heroics", "breach.escalate.board",  "control_breaches:22", {"note":"DG informed per CSSF procedure"}),
]

def seed_audit(cur):
    for uname, org_slug, action, resource, detail in AUDIT_EVENTS:
        org_id = fk(cur, "organisations", "slug", org_slug)
        user_row = cur.execute("SELECT id FROM users WHERE username=?", (uname,)).fetchone()
        if not user_row:
            continue
        d = date.today() - timedelta(days=random.randint(0, 60))
        cur.execute("""
            INSERT INTO audit_log (ts, org_id, user_id, action, resource, detail)
            VALUES (?,?,?,?,?,?)
        """, (isodt(d), org_id, user_row[0], action, resource, json.dumps(detail)))
    print(f"  [+] audit_log: {len(AUDIT_EVENTS)} entries")


# ════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════

def populate(db_path: str):
    if not Path(db_path).exists():
        print(f"[!] Database not found: {db_path}")
        print("    Run create_db.py first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")

    print(f"\n[→] Populating: {db_path}\n")

    seed_orgs(cur);             conn.commit()
    seed_offices(cur);          conn.commit()
    seed_dept_office_map(cur);  conn.commit()
    seed_dept_position_map(cur);conn.commit()
    seed_funds(cur);            conn.commit()
    seed_users(cur);            conn.commit()
    seed_user_fund_access(cur); conn.commit()
    seed_nav_history(cur);      conn.commit()
    seed_subred_aum(cur);       conn.commit()
    seed_breaches(cur);         conn.commit()
    seed_chat(cur);             conn.commit()
    seed_audit(cur);            conn.commit()

    # ── Summary ───────────────────────────────────────────────────
    tables = [
        "organisations","offices","dept_office_map","dept_position_map",
        "funds","fund_data_paths","users","user_fund_access",
        "nav_history","subred_aum","control_breaches","breach_comments",
        "breach_attachments","chat_messages","audit_log",
    ]
    print(f"\n{'─'*45}")
    print(f"  {'Table':<30}  {'Rows':>8}")
    print(f"{'─'*45}")
    for t in tables:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<30}  {n:>8,}")
    print(f"{'─'*45}")

    conn.close()
    print(f"\n[✓] Done. Database ready: {db_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis demo data population")
    parser.add_argument("--db-path", default="aegis.db")
    args = parser.parse_args()
    populate(args.db_path)