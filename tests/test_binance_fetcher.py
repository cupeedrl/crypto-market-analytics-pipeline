import unittest
from unittest.mock import Mock, patch
import pandas as pd
from src.ingestion.binance_fetcher import BinanceFetcher


class TestBinanceFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = BinanceFetcher()

    def test_fetch_daily_data(self):
        """Test fetch daily data từ Binance"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = [
                {"symbol": "BTCUSDT", "price": "65000.00"}
            ]
            mock_get.return_value = mock_response

            result = self.fetcher.fetch_daily_data("BTCUSDT")
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)

    def test_normalize_symbols(self):
        """Test chuẩn hóa symbols"""
        df = pd.DataFrame({"symbol": ["btc", "eth", "bnb"]})
        result = self.fetcher.normalize_symbols(df)
        self.assertEqual(result["symbol"].iloc[0], "BTCUSDT")


if __name__ == "__main__":
    unittest.main()
