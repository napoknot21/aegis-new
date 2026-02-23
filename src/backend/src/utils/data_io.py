from __future__ import annotations

import os
import time
import hashlib
import openpyxl
import polars as pl
import datetime as dt

from typing import Dict, Optional, List, Tuple

from src.utils.logger import log
from src.utils.formatters import numeric_cast_expr_from_utf8, date_cast_expr_from_utf8


def load_excel_to_dataframe (
        
        excel_file_abs_path : str,
        sheet_name : str = "Sheet1",

        specific_cols : Optional[List] = None,
        schema_overrides: Optional[Dict] = None,

        cast_num : bool = True,
        allow_us_mdy: bool = False,
        date_formats: Optional[List[str]] = None,
    
    ) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
    """
    Load an Excel file into a Polars DataFrame with smart type casting.
    Returns (DataFrame, md5_hash) or (None, None) on failure.
    """
    if not os.path.isfile(excel_file_abs_path):
        log(f"[-] File not found: {excel_file_abs_path}", "error")
        return None, None

    if not sheet_name:
        sheet_name = 0

    try:
        start = time.time()

        df = pl.read_excel(
            source=excel_file_abs_path,
            sheet_name=sheet_name,
            columns=specific_cols,
            schema_overrides=None if cast_num else schema_overrides,
        )

        if not cast_num or schema_overrides is None:
            md5 = hashlib.md5(df.write_csv().encode()).hexdigest()
            log(f"[*] Read in {time.time() - start:.2f}s from {excel_file_abs_path}")
            return df, md5

        actual = dict(zip(df.columns, df.dtypes))
        exprs: list[pl.Expr] = []

        for col, target_dtype in schema_overrides.items():
            if col not in actual:
                continue
            actual_dtype = actual[col]
            if actual_dtype == target_dtype:
                continue

            is_target_date = target_dtype in (pl.Date, pl.Datetime)
            is_target_float = target_dtype in (pl.Float32, pl.Float64)
            is_target_int = target_dtype in (
                pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64
            )

            if is_target_date and actual_dtype == pl.Utf8:
                exprs.append(date_cast_expr_from_utf8(
                    col,
                    to_datetime=(target_dtype == pl.Datetime),
                    formats=date_formats,
                    allow_us_mdy=allow_us_mdy,
                ))
            elif (is_target_float or is_target_int) and actual_dtype == pl.Utf8:
                exprs.append(numeric_cast_expr_from_utf8(col, target_dtype))
            else:
                exprs.append(pl.col(col).cast(target_dtype, strict=False).alias(col))

        if exprs:
            df = df.with_columns(exprs)

        md5 = hashlib.md5(df.write_csv().encode()).hexdigest()
        log(f"[*] Read in {time.time() - start:.2f}s from {excel_file_abs_path}")
        return df, md5

    except Exception as e:
        log(f"[-] Error reading Excel {excel_file_abs_path}: {e}", "error")
        return None, None


def load_csv_to_dataframe (
        
        csv_abs_path: str,
        specific_cols: Optional[List] = None,
        schema_overrides: Optional[Dict] = None,
    
    ) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
    """
    Load a CSV into a Polars DataFrame. Returns (DataFrame, md5) or (None, None).
    """
    if not os.path.isfile(csv_abs_path):
    
        log(f"[-] File not found: {csv_abs_path}", "error")
        return None, None

    try:
        start = time.time()
        df = pl.read_csv(
            source=csv_abs_path,
            columns=specific_cols,
            schema_overrides=schema_overrides,
            low_memory=False,
            n_threads=4,
        )
        md5 = hashlib.md5(df.write_csv().encode()).hexdigest()
        log(f"[*] Read CSV in {time.time() - start:.2f}s from {csv_abs_path}")
        return df, md5

    except Exception as e:
        log(f"[-] Error reading CSV {csv_abs_path}: {e}", "error")
        return None, None


def load_json_to_dataframe(
    json_abs_path: str,
    schema_overrides: Optional[Dict] = None,
) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
    """Load a JSON file into a Polars DataFrame. Returns (DataFrame, md5) or (None, None)."""
    if not os.path.isfile(json_abs_path):
        log(f"[-] File not found: {json_abs_path}", "error")
        return None, None

    try:
        start = time.time()
        df = pl.read_json(source=json_abs_path, schema_overrides=schema_overrides)
        md5 = hashlib.md5(df.write_csv().encode()).hexdigest()
        log(f"[*] Read JSON in {time.time() - start:.2f}s from {json_abs_path}")
        return df, md5

    except Exception as e:
        log(f"[-] Error reading JSON {json_abs_path}: {e}", "error")
        return None, None


def export_dataframe_to_excel(
    df: pl.DataFrame,
    output_abs_path: str,
    sheet_name: str = "Sheet1",
) -> Dict:
    """Export a Polars DataFrame to Excel. Returns {success, message, path}."""
    response = {"success": False, "message": None, "path": None}

    if not output_abs_path:
        response["message"] = "Output path not specified."
        return response

    try:
        start = time.time()
        df.write_excel(workbook=output_abs_path, worksheet=sheet_name)
        log(f"[+] Excel written in {time.time() - start:.2f}s to {output_abs_path}")
        response.update({"success": True, "message": "Export successful", "path": output_abs_path})

    except Exception as e:
        log(f"[-] Failed to export to Excel: {e}", "error")
        response["message"] = f"Export failed: {e}"

    return response


def export_dataframe_to_json(df: pl.DataFrame, output_abs_path: str) -> Dict:
    """Export a Polars DataFrame to JSON. Returns {success, message, path}."""
    response = {"success": False, "message": None, "path": None}

    if not output_abs_path:
        response["message"] = "Output path not specified."
        return response

    try:
        start = time.time()
        df.write_json(file=output_abs_path)
        log(f"[+] JSON written in {time.time() - start:.2f}s to {output_abs_path}")
        response.update({"success": True, "message": "Export successful", "path": output_abs_path})

    except Exception as e:
        log(f"[-] Failed to export to JSON: {e}", "error")
        response["message"] = f"Export failed: {e}"

    return response


def export_dataframe_to_csv(
    df: pl.DataFrame,
    output_abs_path: str,
    separator: str = ",",
) -> Dict:
    """Export a Polars DataFrame to CSV. Returns {success, message, path}."""
    response = {"success": False, "message": None, "path": None}

    if not output_abs_path:
        response["message"] = "Output path not specified."
        return response

    try:
        start = time.time()
        df.write_csv(file=output_abs_path, separator=separator)
        log(f"[+] CSV written in {time.time() - start:.2f}s to {output_abs_path}")
        response.update({"success": True, "message": "Export successful", "path": output_abs_path})

    except Exception as e:
        log(f"[-] Failed to export to CSV: {e}", "error")
        response["message"] = f"Export failed: {e}"

    return response


def convert_payment_to_excel(
    payment: Optional[tuple],
    template_abs_path: str,
    dir_abs_path: str,
    columns_index: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Fill a payment Excel template with values and save it.
    Returns the saved file path or None on failure.
    """
    if not payment:
        return None

    os.makedirs(dir_abs_path, exist_ok=True)
    workbook = openpyxl.load_workbook(template_abs_path)
    sheet = workbook.active

    for value, col_letter in zip(payment, columns_index or []):
        cell = sheet[f"{col_letter}3"]
        cell.value = value
        if isinstance(value, (dt.date, dt.datetime)):
            cell.number_format = "DD/MM/YYYY"

    filename = f"Payment_instructions_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(dir_abs_path, filename)
    workbook.save(path)
    return path


def convert_ubs_instruction_payments_to_excel(
    payments: Optional[tuple],
    template_abs_path: str,
    dir_abs_path: str,
    filename: Optional[str] = None,
    columns_index: Optional[List[str]] = None,
) -> Dict:
    """Fill a UBS payment instruction Excel template. Returns {success, message, path}."""
    response = {"success": False, "message": None, "path": None}

    if not payments:
        log("[-] No payments passed.")
        return response

    os.makedirs(dir_abs_path, exist_ok=True)
    filename = filename or f"UBS_Payment_Instruction_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    workbook = openpyxl.load_workbook(template_abs_path)
    sheet = workbook.active

    row_idx = 7
    for payment in payments:
        for value, col_letter in zip(payment, columns_index or []):
            if value is None:
                continue
            cell = sheet[f"{col_letter}{row_idx}"]
            cell.value = value
            if isinstance(value, (dt.date, dt.datetime)):
                cell.number_format = "DD/MM/YYYY"
        row_idx += 2

    path = os.path.join(dir_abs_path, filename)
    try:
        workbook.save(path)
        response.update({"success": True, "path": path, "message": "UBS payment instruction saved."})
        log(f"[+] {response['message']}")
    except Exception as e:
        log(f"[-] Error saving UBS payment: {e}", "error")

    return response