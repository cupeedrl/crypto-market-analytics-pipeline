import unittest
from unittest.mock import Mock, patch
import pandas as pd
from src.storage.s3_loader import S3Loader


class TestS3Upload(unittest.TestCase):
    def test_upload_to_s3(self):
        """Test upload data lên S3"""
        loader = S3Loader()

        df = pd.DataFrame({"symbol": ["BTCUSDT"], "price": [65000.0]})

        with patch("boto3.client") as mock_boto:
            mock_s3 = Mock()
            mock_boto.return_value = mock_s3

            loader.upload_to_s3(df, "test-bucket", "test-key.csv")
            mock_s3.put_object.assert_called_once()


if __name__ == "__main__":
    unittest.main()
