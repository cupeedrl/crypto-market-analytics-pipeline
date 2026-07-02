import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import boto3
from src.utils.config import Config

print(f"Testing S3 access with:")
print(f"  Region: {Config.AWS_REGION}")
print(f"  Bucket: {Config.S3_BUCKET_NAME}")

try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        region_name=Config.AWS_REGION
    )
    
    # Test upload
    test_key = 'test/hello.txt'
    s3_client.put_object(
        Bucket=Config.S3_BUCKET_NAME,
        Key=test_key,
        Body=b'Test from host'
    )
    print(f"✅ Upload from HOST success!")
    
except Exception as e:
    print(f"❌ Error: {e}")
