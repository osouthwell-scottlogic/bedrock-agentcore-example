import json
import boto3
import os
import logging
import re
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

def validate_email(email):
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def lambda_handler(event, context):
    """Send an email to a customer (writes to S3)."""
    try:
        customer_email = event.get('customer_email')
        subject = event.get('subject')
        body = event.get('body')
        
        # Input validation
        if not all([customer_email, subject, body]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'customer_email, subject, and body are required'})
            }
        
        if not validate_email(customer_email):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid email address format'})
            }
        
        if not S3_BUCKET:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'S3 bucket not configured'})
            }
        
        logger.info(f"Sending email to {customer_email}")
        s3_client = boto3.client('s3', config=boto_config)
        
        # Create date-based prefix
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create filename with timestamp, email, and subject
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        subject_slug = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in subject.lower())[:50]
        key = f"sent-emails/{today}/{timestamp}_{customer_email}_{subject_slug}.txt"
        
        # Create email content
        email_content = f"""To: {customer_email}
Subject: {subject}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}
"""
        
        # Write to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=email_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        logger.info(f"Email successfully written to S3: {key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Email sent successfully to {customer_email}'})
        }
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
