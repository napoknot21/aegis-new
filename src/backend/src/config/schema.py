from __future__ import annotations

"""
schema.py
---------
All column schemas, dtype maps, and regex patterns used when reading
Excel/file sources. These are UNIFORM across all tenants — they describe
the format of the data, not where it lives.

This is your existing parameters.py with the env-var values removed.
Env-var values (fund names, paths, credentials) all live in TenantConfig.
"""

import re
import polars as pl


# ================================================================
# SIMM
# ================================================================

SIMM_COLUMNS = {
    "group":                {"name": "Counterparty",                "type": pl.Utf8},
    "postIm":               {"name": "IM",                          "type": pl.Float64},
    "post.price":           {"name": "MV",                          "type": pl.Float64},
    "post.priceCapped":     {"name": "MV Capped",                   "type": pl.Float64},
    "post.priceCappedMode": {"name": "MV Capped Type",              "type": pl.Utf8},
    "post.shortfall":       {"name": "Available / Shortfall Amount","type": pl.Float64},
    "post.clientMarginRatio":{"name": "Client Margin Rate",         "type": pl.Float64},
}

SIMM_RENAME_COLUMNS: dict[str, str] = {k: v["name"] for k, v in SIMM_COLUMNS.items()}


# ================================================================
# Expiries
# ================================================================

EXPIRIES_FILENAME_REGEX = re.compile(r"^expiries_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})")

EXPIRIES_COLUMNS = {
    "Trade Type":        pl.Utf8,
    "Underlying Asset":  pl.Utf8,
    "Termination Date":  pl.Date,
    "Buy/Sell":          pl.Utf8,
    "Notional":          pl.Float64,
    "Asset Class":       pl.Utf8,
    "Call/Put":          pl.Utf8,
    "Strike":            pl.Float64,
    "Trigger":           pl.Float64,
    "Reference Spot":    pl.Float64,
    "Counterparty":      pl.Utf8,
    "MV":                pl.Float64,
    "Total Premium":     pl.Float64,
    "Trigger 2":         pl.Float64,
    "Days Remaining":    pl.UInt64,
    "As Of":             pl.Utf8,
}

EXPIRIES_COLUMNS_HV = {
    **EXPIRIES_COLUMNS,
    "Portfolio Name": pl.Utf8,
    "Strike 1":       pl.Float64,
    "Strike 2":       pl.Float64,
}

EXPIRIES_COLUMNS_SPECIFIC = {
    "Trade Type":       pl.Utf8,
    "Underlying Asset": pl.Utf8,
    "Asset Class":      pl.Utf8,
    "Buy/Sell":         pl.Utf8,
    "Call/Put":         pl.Utf8,
    "Strike":           pl.Float64,
    "Termination Date": pl.Date,
}


# ================================================================
# NAV
# ================================================================

NAV_HISTORY_COLUMNS = {
    "Portfolio Name": pl.Utf8,
    "MV":             pl.Float64,
    "MV/NAV%":        pl.Float64,
    "Comment":        pl.Utf8,
    "Date":           pl.Date,
}

NAV_PORTFOLIO_COLUMNS = dict(list(NAV_HISTORY_COLUMNS.items())[:3])


# ================================================================
# NAV Estimate
# ================================================================

NAV_ESTIMATE_COLUMNS = {
    "NAV Estimate":                    pl.Float64,
    "NAV Estimate Weighted by Time":   pl.Float64,
    "date":                            pl.Date,
}

NAV_ESTIMATE_RENAME_COLUMNS = {
    "NAV Estimate":                  "GAV",
    "NAV Estimate Weighted by Time": "Weighted Performance",
}


# ================================================================
# SubRed
# ================================================================

SUBRED_STRUCT_COLUMNS = {
    "deliveryDate": pl.Utf8,
    "notional":     pl.Float64,
    "currency":     pl.Utf8,
}

SUBRED_COLS_NEEDED = {
    "tradeLegCode":     pl.Utf8,
    "tradeDescription": pl.Utf8,
    "tradeName":        pl.Utf8,
    "bookName":         pl.Utf8,
    "tradeType":        pl.Utf8,
    "instrument":       pl.Struct(SUBRED_STRUCT_COLUMNS),
}

SUBRED_COLUMNS_READ = {
    "tradeLegCode":     pl.Utf8,
    "tradeDescription": pl.Utf8,
    "tradeName":        pl.Utf8,
    "bookName":         pl.Utf8,
    "tradeType":        pl.Utf8,
}


# ================================================================
# Cash / Collateral
# ================================================================

CASH_COLUMNS = {
    "Fundation":       pl.Utf8,
    "Account":         pl.Utf8,
    "Date":            pl.Date,
    "Bank":            pl.Utf8,
    "Currency":        pl.Utf8,
    "Type":            pl.Utf8,
    "Amount in CCY":   pl.Float64,
    "Exchange":        pl.Float64,
    "Amount in EUR":   pl.Float64,
}

COLLATERAL_COLUMNS = {
    "Fundation":            pl.Utf8,
    "Account":              pl.Utf8,
    "Date":                 pl.Date,
    "Bank":                 pl.Utf8,
    "Currency":             pl.Utf8,
    "Total":                pl.Float64,
    "IM":                   pl.Float64,
    "VM":                   pl.Float64,
    "Requirement":          pl.Float64,
    "Net Excess/Deficit":   pl.Float64,
}


# ================================================================
# Payments
# ================================================================

PAYMENTS_COLUMNS = {
    "Fondsname":        pl.Utf8,
    "KONTONR":          pl.Int64,
    "DEVISE":           pl.Utf8,
    "BETRAG":           pl.Float64,
    "VALUTA":           pl.Datetime,
    "AUFTRAGGEBER":     pl.Utf8,
    "SPESENDETAIL":     pl.Utf8,
    "BEGUENSTIGTER":    pl.Utf8,
    "ZAHLUNGSTEXT":     pl.Utf8,
    "IBAN":             pl.Utf8,
    "MIT BANK":         pl.Utf8,
    "MIT BANK.1":       pl.Utf8,
    "KORRESPONDENT":    pl.Utf8,
    "TEXT KONTOAUSZUG": pl.Utf8,
}

SECURITIES_COLUMNS = {
    "Transref. AM":     pl.Int64,
    "fund":             pl.Utf8,
    "NEWM/CANC":        pl.Utf8,
    "Portfolio ID  AM": pl.Int64,
    "BUY/SELL":         pl.Utf8,
    "Quantity":         pl.Int64,
    "Sec. ID":          pl.Utf8,
    "Sec. name":        pl.Utf8,
    "Price":            pl.Float64,
    "Trade CCY":        pl.Utf8,
    "Interest":         pl.Float64,
    "Trade date":       pl.Datetime,
    "Settlement date":  pl.Datetime,
    "Sett. CCY":        pl.Utf8,
    "Broker ID":        pl.Utf8,
    "Settl. amount":    pl.Float64,
}

PAYMENTS_BENEFICIARY_COLUMNS = {
    "Counterparty":            pl.Utf8,
    "Type Payment":            pl.Utf8,
    "Currency":                pl.Utf8,
    "Bank":                    pl.Utf8,
    "Beneficiary Bank":        pl.Utf8,
    "Swift-Code":              pl.Utf8,
    "Swift-Code Beneficiary":  pl.Utf8,
    "IBAN":                    pl.Utf8,
}

PAYMENTS_EXCEL_COLUMNS = ["A", "C", "D", "E", "F", "H", "I", "M", "Q", "R", "S", "X", "Z"]

PAYMENTS_DIRECTIONS = ["Receive", "Pay"]

PAYMENTS_TYPES_MARKET = {
    "Margin Call":      ["Margin Call"],
    "Option Premium":   ["FX", "Equity", "Margin Call"],
    "Option Exercise":  ["FX", "Equity", "Margin Call"],
}


# ================================================================
# UBS Settlement
# ================================================================

UBS_PAYMENTS_EXCEL_COLUMNS = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "M", "N", "O"]
UBS_PAYMENTS_TYPES    = ["Option Premium", "Option Exercice"]
UBS_PAYMENTS_MARKET   = ["FX", "Equity"]
UBS_PAYMENTS_DIRECTIONS = ["Buy", "Sell"]

UBS_FX_PAYMENT_COLUMNS = {
    "Fund Number (LUX)":  pl.Int64,
    "Reference":          pl.Utf8,
    "Buy/Sell":           pl.Utf8,
    "Currency":           pl.Utf8,
    "Nominal":            pl.Float64,
    "Counter Currency":   pl.Utf8,
    "Rate":               pl.Float64,
    "Settlement Amount":  pl.Float64,
    "Trade Date":         pl.Date,
    "Maturity":           pl.Date,
    "BIC Code CP":        pl.Utf8,
}


# ================================================================
# Leverages
# ================================================================

LEVERAGES_COLUMNS = {
    "Gross Leverage":       pl.Float64,
    "Commitment Leverage":  pl.Float64,
    "Date":                 pl.Datetime,
    "File":                 pl.Utf8,
}

LEVERAGES_UNDERL_COLUMNS = {
    "Asset Class":      pl.Utf8,
    "Underlying Asset": pl.Utf8,
    "Gross Leverage":   pl.Float64,
    "Exposure % NAV":   pl.Float64,
}

LEVERAGES_TRADE_COLUMNS = {
    "Trade ID":         pl.Int64,
    "Asset Class":      pl.Utf8,
    "Trade Type":       pl.Utf8,
    "Underlying Asset": pl.Utf8,
    "Termination Date": pl.Date,
    "Buy/Sell":         pl.Utf8,
    "Notional":         pl.Float64,
    "Call/Put":         pl.Utf8,
    "Strike":           pl.Float64,
    "Trigger":          pl.Float64,
    "Reference Spot":   pl.Float64,
    "Counterparty":     pl.Utf8,
    "Gross Leverage":   pl.Float64,
    "Exposure % NAV":   pl.Float64,
}


# ================================================================
# Greeks
# ================================================================

GREEKS_COLUMNS = {
    "Underlying": pl.Utf8,
    "Delta":      pl.Float64,
    "Gamma":      pl.Float64,
    "Vega":       pl.Float64,
    "Theta":      pl.Float64,
    "Date":       pl.Utf8,
}

GREEKS_OVERVIEW_COLUMNS = {
    "Underlying": pl.Utf8,
    "Delta":      pl.Float64,
    "Gamma":      pl.Float64,
    "Vega":       pl.Float64,
    "Theta":      pl.Float64,
}

GREEKS_RISKS_EQUITY_COLUMNS = {
    "Underlying":    pl.Utf8,
    "Delta":         pl.Float64,
    "Gamma":         pl.Float64,
    "Vega":          pl.Float64,
    "Theta":         pl.Float64,
    "Delta % NAV":   pl.Float64,
    "Gamma % NAV":   pl.Float64,
    "Vega % NAV":    pl.Float64,
    "Theta % NAV":   pl.Float64,
}

GREEKS_ASSET_CLASS_RULES = {
    "FX":     ["Curncy"],
    "EQUITY": ["Equity", "Index"],
}

GREEKS_CONCENTRATION_COLUMNS = {
    "Counterparty": pl.Utf8,
    "MV":           pl.Float64,
    "MV/NAV%":      pl.Float64,
    "Compliance":   pl.Utf8,
}

GREEKS_DELTA_PNL_STRESS_COLUMNS = {
    "Underlying":        pl.Utf8,
    "-3 x Sigma - P&L":  pl.Float64,
    "-2 x Sigma - P&L":  pl.Float64,
    "-1 x Sigma - P&L":  pl.Float64,
    "0 x Sigma - P&L":   pl.Float64,
    "1 x Sigma - P&L":   pl.Float64,
    "2 x Sigma - P&L":   pl.Float64,
    "3 x Sigma - P&L":   pl.Float64,
}

GREEKS_LONG_SHORT_DELTA_COLUMNS = {
    "Underlying Asset":         pl.Utf8,
    "Long Delta(%)":            pl.Float64,
    "Average Strike Long":      pl.Float64,
    "Average Maturities Long":  pl.Float64,
    "Short Delta(%)":           pl.Float64,
    "Average Strike Short":     pl.Float64,
    "Average Maturities Short": pl.Float64,
    "Net Delta (%)":            pl.Float64,
}

GREEKS_GAMMA_PNL_COLUMNS = {
    "Underlying":      pl.Utf8,
    "Gamma":           pl.Float64,
    "Theta":           pl.Float64,
    "P&L / 1 sigma":   pl.Float64,
    "P&L / 3 sigma":   pl.Float64,
    "STD":             pl.Float64,
}

GREEKS_RISK_CREDIT_COLUMNS = {
    "Underlying":  pl.Utf8,
    "CS01":        pl.Float64,
    "CS01 % NAV":  pl.Float64,
}

GREEKS_VEGA_BUCKET_COLUMNS = {
    "Underlying Asset": pl.Utf8,
    "1w":       pl.Float64,
    "1w-1m":    pl.Float64,
    "1m-3m":    pl.Float64,
    "3m-6m":    pl.Float64,
    "6m-1y":    pl.Float64,
    ">1y":      pl.Float64,
    "Total":    pl.Float64,
}

GREEKS_VEGA_STRESS_PNL_COLUMNS = {
    "Asset Class":          pl.Utf8,
    "Underlying":           pl.Utf8,
    "Vega":                 pl.Float64,
    "Vega P&L - moderate":  pl.Float64,
    "Vega P&L - stress":    pl.Float64,
    "Vega P&L - extreme":   pl.Float64,
}


# ================================================================
# Screeners
# ================================================================

SCREENERS_COLUMNS_FX = {
    "Trade Code":       pl.Utf8,
    "Trade Description":pl.Utf8,
    "Portfolio Name":   pl.Utf8,
    "Underlying Asset": pl.Utf8,
    "Instrument Type":  pl.Utf8,
    "Buy/Sell":         pl.Utf8,
    "Reference Spot":   pl.Float64,
    "Original Spot":    pl.Float64,
    "FX ForwardRate":   pl.Float64,
    "Forward":          pl.Float64,
    "Forward Points":   pl.Float64,
    "Strike":           pl.Float64,
    "MV":               pl.Float64,
    "Base Notional":    pl.Float64,
    "FX Delta Base":    pl.Float64,
    "Trade Date":       pl.Date,
    "Termination Date": pl.Date,
}

SCREENERS_COLUMNS_TARF = {
    "Trade Code":                           pl.Utf8,
    "Trade Description":                    pl.Utf8,
    "Portfolio Name":                       pl.Utf8,
    "Instrument Type":                      pl.Utf8,
    "Underlying Asset":                     pl.Utf8,
    "Trade Date":                           pl.Date,
    "FX Next Fixing Date":                  pl.Date,
    "FX Remaining Target Term Per Base":    pl.Float64,
    "Expiry Date":                          pl.Date,
    "Call/Put 1":                           pl.Utf8,
    "Remaining Notional":                   pl.Float64,
    "Notional 1 Base":                      pl.Float64,
    "Total Premium":                        pl.Float64,
    "MV":                                   pl.Float64,
    "Original Spot":                        pl.Float64,
    "Reference Spot":                       pl.Float64,
    "Strike 1":                             pl.Float64,
    "Trigger":                              pl.Float64,
    "FX Delta Base":                        pl.Float64,
    "FX Gamma Base":                        pl.Float64,
    "FX Theta Base":                        pl.Float64,
    "FX Remaining Number of Fixings":       pl.Int64,
    "FX Projected Number of Expiries Remaining": pl.Int64,
    "FX Projected Payout at Next Fixing":   pl.Float64,
    "FX Accrued Target Term Per Base":      pl.Float64,
    "FX Total Accumulated Profit":          pl.Float64,
    "FX Remaining Notional":                pl.Float64,
}

SCREENERS_COLUMNS_TAIL = {
    "Trade Code":       pl.Utf8,
    "Trade Description":pl.Utf8,
    "Instrument Type":  pl.Utf8,
    "Underlying Asset": pl.Utf8,
    "Expiry Date":      pl.Date,
    "Portfolio Name":   pl.Utf8,
    "MV":               pl.Float64,
}


# ================================================================
# Concentration
# ================================================================

CONCENTRATION_COLUMNS = {
    "Counterparty": pl.Utf8,
    "MV":           pl.Float64,
    "MV/NAV%":      pl.Float64,
}


# ================================================================
# Trade Recap
# ================================================================

TRADE_RECAP_MIN_COLUMNS = {
    "tradeLegId":               pl.Int64,
    "tradeId":                  pl.Int64,
    "assetClass":               pl.Utf8,
    "tradeType":                pl.Utf8,
    "tradeDescription":         pl.Utf8,
    "tradeLegCode":             pl.Utf8,
    "tradeName":                pl.Utf8,
    "bookId":                   pl.Int64,
    "bookName":                 pl.Utf8,
    "counterparty":             pl.Utf8,
    "creationTime":             pl.Utf8,
    "instrument.instrumentType":pl.Utf8,
    "originatingAction":        pl.Utf8,
}


# ================================================================
# Aggregated Positions
# ================================================================

AGGREGATED_POSITIONS_COLUMNS = {
    "Asset Class":        pl.Utf8,
    "Counterparty":       pl.Utf8,
    "Portfolio Name":     pl.Utf8,
    "Underlying Asset":   pl.Utf8,
    "Trade Type":         pl.Utf8,
    "Product Name":       pl.Utf8,
    "Instrument Type":    pl.Utf8,
    "Product Code":       pl.Utf8,
    "Trade Date":         pl.Datetime,
    "Trade Code":         pl.Utf8,
    "Remaining Notional": pl.Float64,
    "Termination Date":   pl.Datetime,
    "MV":                 pl.Float64,
}