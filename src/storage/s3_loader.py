import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class S3Loader:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        self.bucket_name = Config.S3_BUCKET_NAME

    def upload_dataframe_as_json(self, df, prefix: str):
        """
        Upload DataFrame dưới dạng JSON lines, partition theo ngày
        Idempotent: Ghi đè file cùng tên trong cùng ngày để tránh duplicate khi retry
        """
        if df.empty:
            logger.warning("DataFrame is empty. Skipping S3 upload.")
            return None
            
        date_str = datetime.utcnow().strftime('%Y/%m/%d')
        # Bỏ timestamp để file name cố định trong ngày → overwrite khi retry
        s3_key = f"{prefix}/date={date_str}/data.json"
        
        json_data = df.to_json(orient='records', lines=True, date_format='iso')
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data,
                ContentType='application/json'
            )
            logger.info(f"Successfully uploaded to s3://{self.bucket_name}/{s3_key}")
            return f"s3://{self.bucket_name}/{s3_key}"
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise