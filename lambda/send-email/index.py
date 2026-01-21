import json
import boto3
import os
import logging
import re
import time
import hashlib
from datetime import datetime
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

S3_BUCKET = os.environ.get('S3_DATA_BUCKET', '')

boto_config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=10
)


def log(level: str, message: str, **meta):
    logger.log(
        logging.getLevelName(level.upper()),
        json.dumps({**meta, 'level': level, 'message': message, 'timestamp': time.time()}),
    )


def build_response(status_code: int, request_id: str, payload: dict):
    return {
        'statusCode': status_code,
        'body': json.dumps({'requestId': request_id, **payload})
    }


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(email) and re.match(pattern, email) is not None


def generate_preview_id(customer_email: str, subject: str, body: str) -> str:
    """Generate a unique preview ID based on email content"""
    content = f"{customer_email}|{subject}|{body}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def lambda_handler(event, context):
    request_id = getattr(context, 'aws_request_id', 'unknown')
    customer_email = event.get('customer_email')
    subject = event.get('subject')
    body = event.get('body')
    approved = event.get('approved', False)
    preview_id = event.get('preview_id', '')
    approver_token = event.get('approver_token', '')

    # PREVIEW MODE: If not approved, return email preview with preview_id
    if not approved:
        # First validate the required fields for preview
        if not all([customer_email, subject, body]):
            return build_response(400, request_id, {
                'errorCode': 'VALIDATION_ERROR',
                'message': 'customer_email, subject, and body are required',
                'details': {'customer_email': bool(customer_email), 'subject': bool(subject), 'body': bool(body)},
            })
        
        if not validate_email(customer_email):
            return build_response(400, request_id, {
                'errorCode': 'VALIDATION_ERROR',
                'message': 'Invalid email address format',
                'details': {'customer_email': customer_email},
            })
        
        # Generate preview ID
        generated_preview_id = generate_preview_id(customer_email, subject, body)
        
        log('info', 'send-email preview generated', requestId=request_id, customerEmail=customer_email, previewId=generated_preview_id)
        return build_response(202, request_id, {
            'status': 'PREVIEW',
            'message': 'Email preview generated. Please review and confirm before sending.',
            'preview_id': generated_preview_id,
            'email_preview': {
                'to': customer_email,
                'subject': subject,
                'body': body,
            },
        })
    
    # APPROVAL GATE: Verify preview_id matches content
    expected_preview_id = generate_preview_id(customer_email, subject, body)
    if preview_id != expected_preview_id:
        log('warn', 'send-email blocked: preview_id mismatch', requestId=request_id, customerEmail=customer_email, providedPreviewId=preview_id, expectedPreviewId=expected_preview_id)
        return build_response(403, request_id, {
            'errorCode': 'PREVIEW_ID_MISMATCH',
            'message': 'Preview ID does not match email content. Email may have been modified after preview.',
            'details': {'preview_id': preview_id},
        })

    if not all([customer_email, subject, body]):
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'customer_email, subject, and body are required',
            'details': {'customer_email': bool(customer_email), 'subject': bool(subject), 'body': bool(body)},
        })

    if not validate_email(customer_email):
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'Invalid email address format',
            'details': {'customer_email': customer_email},
        })

    if subject and len(subject) > 200:
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'Subject is too long (max 200 characters)',
            'details': {'length': len(subject)},
        })

    if body and len(body) > 10000:
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'Body is too long (max 10000 characters)',
            'details': {'length': len(body)},
        })

    if not S3_BUCKET:
        return build_response(500, request_id, {
            'errorCode': 'CONFIG_ERROR',
            'message': 'S3 bucket not configured',
            'details': {},
        })

    try:
        log('info', 'send-email start', requestId=request_id, customerEmail=customer_email)
        s3_client = boto3.client('s3', config=boto_config)

        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        subject_slug = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in subject.lower())[:50]
        key = f"sent-emails/{today}/{timestamp}_{customer_email}_{subject_slug}.txt"

        email_content = f"""To: {customer_email}
Subject: {subject}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}
"""

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=email_content.encode('utf-8'),
            ContentType='text/plain',
            Metadata={
                'approved': 'true',
                'approver-token': approver_token[:100] if approver_token else 'none',
            }
        )

        log('info', 'send-email success', requestId=request_id, key=key, approved=approved, approverToken=approver_token[:20] if approver_token else 'none')
        return build_response(200, request_id, {'message': f'Email sent successfully to {customer_email}', 's3Key': key})
    except Exception as e:  # noqa: BLE001
        log('error', 'send-email failed', requestId=request_id, error=str(e))
        return build_response(500, request_id, {
            'errorCode': 'SEND_EMAIL_ERROR',
            'message': 'Failed to send email',
            'details': {'error': str(e)},
        })
