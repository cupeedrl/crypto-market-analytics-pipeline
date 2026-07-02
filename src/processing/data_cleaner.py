import pandas as pd
import numpy as np
from typing import Dict, List


class DataCleaner:
    """Xử lý làm sạch dữ liệu crypto"""

    @staticmethod
    def clean_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Làm sạch dữ liệu giá từ Binance API

        Args:
            df: DataFrame chứa dữ liệu raw từ Binance

        Returns:
            DataFrame đã được làm sạch
        """
        # Loại bỏ duplicates
        df = df.drop_duplicates(subset=["symbol", "timestamp"], keep="last")

        # Xử lý missing values - Fix deprecated method
        df["current_price"] = df["current_price"].ffill()
        df["volume"] = df["volume"].fillna(0)

        # Loại bỏ outliers (giá = 0 hoặc âm)
        df = df[df["current_price"] > 0]
        df = df[df["volume"] >= 0]

        # Convert data types
        df["current_price"] = df["current_price"].astype(float)
        df["volume"] = df["volume"].astype(float)

        return df

    @staticmethod
    def normalize_symbols(df: pd.DataFrame) -> pd.DataFrame:
        """
        Chuẩn hóa tên symbols (BTC -> BTCUSDT)

        Args:
            df: DataFrame chứa cột symbol

        Returns:
            DataFrame với symbols đã chuẩn hóa
        """
        symbol_mapping = {
            "BTC": "BTCUSDT",
            "ETH": "ETHUSDT",
            "BNB": "BNBUSDT",
            "SOL": "SOLUSDT",
            "XRP": "XRPUSDT",
            "USDC": "USDCUSDT",
            "USDT": "USDTUSD",
            "WLD": "WLDUSDT",
            "XAUT": "XAUTUSD",
            "ZEC": "ZECUSDT",
            "TAO": "TAOUSDT",
            "USD1": "USD1USD",
        }

        df["symbol"] = df["symbol"].str.upper()
        df["symbol"] = df["symbol"].map(symbol_mapping).fillna(df["symbol"])

        return df

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """
        Tính toán các metrics cơ bản

        Args:
            df: DataFrame chứa price data

        Returns:
            DataFrame với các metrics bổ sung
        """
        df = df.sort_values(["symbol", "timestamp"])

        # Price change
        df["price_change"] = df.groupby("symbol")["current_price"].diff()
        df["price_change_percent"] = (
            df["price_change"] / df.groupby("symbol")["current_price"].shift(1)
        ) * 100

        # Volume change
        df["volume_change"] = df.groupby("symbol")["volume"].diff()

        return df
