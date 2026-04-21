from __future__ import annotations

import logging
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SERVICE_ACCOUNT_FILE = Path(__file__).resolve().parent / "service_account.json"

# ── Set these once, then forget ─────────────────────────────────────
# Paste the full URL of your Google Sheet here (between the quotes).
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yyRbTRqreXmbeyAjf237BQ9W86HST-Ee5hQsFd2WqCI/edit"
# ────────────────────────────────────────────────────────────────────


def _get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=_SCOPES
    )
    return gspread.authorize(creds)


def _ensure_worksheet(
    spreadsheet: gspread.Spreadsheet, title: str, cols: int = 10
) -> gspread.Worksheet:
    """Return an existing worksheet by *title*, or create one."""
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=cols)


def _push_dataframe(worksheet: gspread.Worksheet, df: pd.DataFrame) -> None:
    """Overwrite a worksheet with the contents of a DataFrame."""
    worksheet.clear()
    if df.empty:
        worksheet.update([df.columns.tolist()], value_input_option="RAW")
        return
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    worksheet.update(data, value_input_option="RAW")


def sync_to_sheets() -> None:
    """Push current items and transactions tables to Google Sheets."""
    if not SPREADSHEET_URL:
        logger.warning("SPREADSHEET_URL is not set in sync_sheets.py — skipping sync.")
        return

    if not SERVICE_ACCOUNT_FILE.exists():
        logger.warning("service_account.json not found — skipping sync.")
        return

    try:
        from database import get_all_items, get_transactions

        client = _get_client()
        spreadsheet = client.open_by_url(SPREADSHEET_URL)

        items_df = get_all_items()
        items_ws = _ensure_worksheet(spreadsheet, "Inventory", cols=len(items_df.columns) or 5)
        _push_dataframe(items_ws, items_df)

        tx_df = get_transactions()
        tx_ws = _ensure_worksheet(spreadsheet, "Transactions", cols=len(tx_df.columns) or 8)
        _push_dataframe(tx_ws, tx_df)

        logger.info("Google Sheets sync complete.")
    except Exception:
        logger.exception("Google Sheets sync failed — the app will continue normally.")
