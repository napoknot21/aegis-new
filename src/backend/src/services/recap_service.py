from __future__ import annotations

import pandas as pd
from typing import Optional

from src.utils.dates import resolve_trade_dates

class RecapService:
    def __init__(self):
        pass

    def get_trade_recap(self, date: Optional[str] = None, trade_date: Optional[str] = None) -> pd.DataFrame:
        """
        Returns a mock trade recap dataframe based on dates provided.
        This provides the data bridge for the frontend.
        """
        d, td = resolve_trade_dates(date, trade_date)
        
        # In a real scenario, fetch data from your databases or local files here
        data = [
            {
                "TradeId": "TRD-1001",
                "Portfolio": "ALPHA_FUND",
                "ProductType": "EQUITY",
                "Quantity": 1500,
                "Price": 125.50,
                "Currency": "USD",
                "Status": "SETTLED",
                "Date": str(d),
                "TradeDate": str(td)
            },
            {
                "TradeId": "TRD-1002",
                "Portfolio": "BETA_FUND",
                "ProductType": "FX_FWD",
                "Quantity": 500000,
                "Price": 1.0945,
                "Currency": "EUR",
                "Status": "PENDING",
                "Date": str(d),
                "TradeDate": str(td)
            },
            {
                "TradeId": "TRD-1003",
                "Portfolio": "GAMMA_FUND",
                "ProductType": "BOND",
                "Quantity": 100,
                "Price": 98.75,
                "Currency": "USD",
                "Status": "SETTLED",
                "Date": str(d),
                "TradeDate": str(td)
            }
        ]
        
        df = pd.DataFrame(data)
        return df

    def book_recap_trades(self, trades: list[dict]) -> int:
        """
        Takes edited trades and orchestrates booking them into the discretionary DB tables.
        This structured template outlines the multi-table database inserts requested.
        """
        for trade in trades:
            # Table 1: trade_disc
            # Orchestrating main discretionary trade info
            trade_disc_payload = {
                "trade_id": trade.get("TradeId"),
                "portfolio": trade.get("Portfolio"),
                "status": trade.get("Status"),
                "trade_date": trade.get("TradeDate"),
                "report_date": trade.get("Date")
            }
            # TODO: Insert or Update into your Supabase / Relational DB
            # supabase.table("trade_disc").upsert(trade_disc_payload).execute()

            # Table 2: trade_disc_legs
            # Orchestrating leg information (quantities, pricing)
            trade_disc_legs_payload = {
                "trade_id": trade.get("TradeId"),
                "quantity": trade.get("Quantity"),
                "price": trade.get("Price"),
                "currency": trade.get("Currency"),
            }
            # TODO: Insert or Update into your DB
            # supabase.table("trade_disc_legs").upsert(trade_disc_legs_payload).execute()

            # Table 3: trade_disc_instruments
            # Orchestrating product type specifics
            trade_disc_instruments_payload = {
                "trade_id": trade.get("TradeId"),
                "product_type": trade.get("ProductType"),
            }
            # TODO: Insert or Update into your DB
            # supabase.table("trade_disc_instruments").upsert(trade_disc_instruments_payload).execute()
            
            # Print to log to trace incoming updates during development
            print(f"Booked Trade {trade.get('TradeId')} across 3 discretionary tables successfully.")

        return len(trades)
