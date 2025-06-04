import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

class S3StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('BACKBLAZE_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('BACKBLAZE_SECRET_ACCESS_KEY'),
            region_name=os.getenv('BACKBLAZE_REGION'),
            endpoint_url=os.getenv('BACKBLAZE_ENDPOINT_URL')
        )
        self.bucket_name = os.getenv('BACKBLAZE_BUCKET_NAME')
    
    def upload_text(self, content: str, text: str = None) -> str:
        """Upload text and return S3 location"""
        if not text:
            text = content
            
        try:
            
            # Generate a unique file name
            file_name = f"{uuid.uuid4()}.txt"
            
            # Upload text directly to S3
            self.s3_client.put_object(
                Body=text,
                Bucket=self.bucket_name,
                Key=file_name,
                ContentType='text/plain'
            )
            
            location = f"s3://{self.bucket_name}/{file_name}"
            return location

        except ClientError as e:
            raise Exception(f"Failed to upload text to S3: {str(e)}")
    
    def get_text_content(self, file_key: str) -> str:
        """Get text content from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            raise Exception(f"Failed to retrieve text from S3: {str(e)}")
    
    def parse_s3_location(self, location: str) -> str:
        """Parse S3 location to get file key"""
        parts = location.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 location format: {location}")
        
        bucket_name, file_key = parts
        if bucket_name != self.bucket_name:
            raise ValueError(f"Unexpected bucket name: {bucket_name}")
        
        return file_key 
    
    def delete_text(self, file_key: str):
        """Delete text from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
        except ClientError as e:
            raise Exception(f"Failed to delete text from S3: {str(e)}")
