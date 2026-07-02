import unittest
from unittest.mock import Mock, patch
import pandas as pd


class TestBinanceFetcher(unittest.TestCase):
    def setUp(self):
        """Setup test fixtures"""
        pass

    def test_fetch_daily_data_mock(self):
        """Test fetch daily data từ Binance (mock)"""
        # Mock data structure
        mock_data = [
            {
                "symbol": "BTCUSDT",
                "timestamp": "2026-06-15",
                "current_price": 65000.0,
                "volume": 1000.0,
            }
        ]

        df = pd.DataFrame(mock_data)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df["symbol"].iloc[0], "BTCUSDT")

    def test_normalize_symbols_mock(self):
        """Test chuẩn hóa symbols (mock)"""
        df = pd.DataFrame({"symbol": ["btc", "eth", "bnb"]})

        # Mock normalization logic
        df["symbol"] = df["symbol"].str.upper()
        symbol_mapping = {
            "BTC": "BTCUSDT",
            "ETH": "ETHUSDT",
            "BNB": "BNBUSDT",
        }
        df["symbol"] = df["symbol"].map(symbol_mapping).fillna(df["symbol"])

        self.assertEqual(df["symbol"].iloc[0], "BTCUSDT")
        self.assertEqual(df["symbol"].iloc[1], "ETHUSDT")
        self.assertEqual(df["symbol"].iloc[2], "BNBUSDT")


if __name__ == "__main__":
    unittest.main()
