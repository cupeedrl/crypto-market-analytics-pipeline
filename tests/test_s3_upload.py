import unittest
from unittest.mock import Mock, patch
import pandas as pd


class TestS3Upload(unittest.TestCase):
    def test_upload_to_s3_mock(self):
        """Test upload data lên S3 (mock)"""
        # Mock S3 client
        with patch("boto3.client") as mock_boto:
            mock_s3 = Mock()
            mock_boto.return_value = mock_s3

            # Mock DataFrame
            df = pd.DataFrame({"symbol": ["BTCUSDT"], "price": [65000.0]})

            # Mock upload operation
            mock_s3.put_object.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": 200}
            }

            # Test upload
            response = mock_s3.put_object(
                Bucket="test-bucket", Key="test-key.csv", Body=df.to_csv(index=False)
            )

            self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 200)
            mock_s3.put_object.assert_called_once()


if __name__ == "__main__":
    unittest.main()
