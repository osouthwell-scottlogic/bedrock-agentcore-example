import json
import boto3
import os
import logging
from datetime import datetime
from botocore.config import Config

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Environment variables
S3_BUCKET = os.environ.get('S3_DATA_BUCKET', '')

# Boto3 config with retries
boto_config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=10
)

def lambda_handler(event, context):
    """Get metadata for recently sent emails."""
    try:
        limit = min(event.get('limit', 10), 100)  # Cap at 100
        logger.info(f"Retrieving recent emails (limit: {limit})")
        
        s3_client = boto3.client('s3', config=boto_config)
        
        if not S3_BUCKET:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'S3 bucket not configured'})
            }
        
        # List objects in sent-emails prefix
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='sent-emails/',
            MaxKeys=100
        )
        
        email_files = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                # Parse key: sent-emails/YYYY-MM-DD/{timestamp}_{email}_{subject}.txt
                parts = key.split('/')
                if len(parts) >= 3 and parts[-1].endswith('.txt'):
                    filename = parts[-1][:-4]
                    file_parts = filename.split('_', 2)
                    if len(file_parts) >= 3:
                        timestamp_str, email, subject_slug = file_parts
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
                            email_files.append({
                                'timestamp': timestamp,
                                'recipient': email,
                                'subject': subject_slug.replace('-', ' ').title()
                            })
                        except ValueError:
                            continue
        
        # Sort by timestamp descending
        email_files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take top N
        recent = email_files[:limit]
        
        # Format output
        result = []
        for email in recent:
            result.append({
                'timestamp': email['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'recipient': email['recipient'],
                'subject': email['subject']
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps({'emails': result if result else []})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
