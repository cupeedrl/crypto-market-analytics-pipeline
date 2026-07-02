import unittest
import pandas as pd
import numpy as np
from src.processing.data_cleaner import DataCleaner


class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()

    def test_clean_price_data(self):
        """Test làm sạch dữ liệu giá"""
        df = pd.DataFrame(
            {
                "symbol": ["BTCUSDT", "BTCUSDT", "ETHUSDT"],
                "timestamp": ["2026-06-15", "2026-06-15", "2026-06-15"],
                "current_price": [65000.0, 65000.0, 3500.0],
                "volume": [1000.0, 1000.0, 500.0],
            }
        )

        result = self.cleaner.clean_price_data(df)
        self.assertEqual(len(result), 2)  # Bỏ duplicate

    def test_remove_outliers(self):
        """Test loại bỏ outliers"""
        df = pd.DataFrame(
            {
                "symbol": ["BTCUSDT"],
                "timestamp": ["2026-06-15"],
                "current_price": [0.0, 65000.0],  # 0 là outlier
                "volume": [1000.0, 500.0],
            }
        )

        result = self.cleaner.clean_price_data(df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result["current_price"].iloc[0], 65000.0)


if __name__ == "__main__":
    unittest.main()
