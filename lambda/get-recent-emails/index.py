import json
import boto3
import os
import logging
import time
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


def lambda_handler(event, context):
    request_id = getattr(context, 'aws_request_id', 'unknown')
    raw_limit = event.get('limit', 10)

    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'limit must be an integer',
            'details': {'limit': raw_limit},
        })

    if limit < 1 or limit > 100:
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'limit must be between 1 and 100',
            'details': {'limit': raw_limit},
        })

    if not S3_BUCKET:
        return build_response(500, request_id, {
            'errorCode': 'CONFIG_ERROR',
            'message': 'S3 bucket not configured',
            'details': {},
        })

    log('info', 'get-recent-emails start', requestId=request_id, limit=limit)

    try:
        s3_client = boto3.client('s3', config=boto_config)
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='sent-emails/',
            MaxKeys=100
        )

        email_files = []

        for obj in response.get('Contents', []):
            key = obj.get('Key', '')
            parts = key.split('/')
            if len(parts) < 3 or not parts[-1].endswith('.txt'):
                continue
            filename = parts[-1][:-4]
            file_parts = filename.split('_', 2)
            if len(file_parts) < 3:
                continue
            timestamp_str, email, subject_slug = file_parts
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
                email_files.append({
                    'timestamp': timestamp,
                    'recipient': email,
                    'subject': subject_slug.replace('-', ' ').title(),
                })
            except ValueError:
                continue

        email_files.sort(key=lambda x: x['timestamp'], reverse=True)
        recent = email_files[:limit]

        result = [
            {
                'timestamp': item['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'recipient': item['recipient'],
                'subject': item['subject'],
            }
            for item in recent
        ]

        log('info', 'get-recent-emails success', requestId=request_id, count=len(result))
        return build_response(200, request_id, {'emails': result})
    except Exception as e:  # noqa: BLE001
        log('error', 'get-recent-emails failed', requestId=request_id, error=str(e))
        return build_response(500, request_id, {
            'errorCode': 'GET_RECENT_EMAILS_ERROR',
            'message': 'Failed to retrieve recent emails',
            'details': {'error': str(e)},
        })
