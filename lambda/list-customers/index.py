import json
import boto3
import os
import logging
import time
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

READ_FILE_FUNCTION_ARN = os.environ.get('READ_FILE_FUNCTION_ARN', '')

boto_config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=10,
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
    log('info', 'list-customers start', requestId=request_id)

    if not READ_FILE_FUNCTION_ARN:
        return build_response(500, request_id, {
            'errorCode': 'CONFIG_ERROR',
            'message': 'READ_FILE_FUNCTION_ARN is not configured',
            'details': {},
        })

    try:
        lambda_client = boto3.client('lambda', config=boto_config)
        
        # Dynamically discover customer files
        list_response = lambda_client.invoke(
            FunctionName=READ_FILE_FUNCTION_ARN.replace('read-file', 'list-files'),
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': 'customers'})
        )
        
        list_result = json.loads(list_response['Payload'].read())
        list_body = json.loads(list_result.get('body', '{}'))
        
        if list_result.get('statusCode') != 200:
            log('warning', 'list-files failed for customers directory', requestId=request_id)
            return build_response(404, request_id, {
                'errorCode': 'CUSTOMER_DB_NOT_FOUND',
                'message': 'Customer database not found',
                'details': {},
            })
        
        # Get the first .json file (customer database)
        files = list_body.get('files', [])
        customer_file = next((f for f in files if f.endswith('.json')), None)
        
        if not customer_file:
            return build_response(404, request_id, {
                'errorCode': 'CUSTOMER_DB_NOT_FOUND',
                'message': 'No customer database file found',
                'details': {},
            })
        
        response = lambda_client.invoke(
            FunctionName=READ_FILE_FUNCTION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': f'customers/{customer_file}'})
        )

        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))

        if result.get('statusCode') != 200:
            return build_response(404, request_id, {
                'errorCode': 'CUSTOMER_DB_NOT_FOUND',
                'message': 'Customer database not found',
                'details': {},
            })

        customers = body.get('content', [])

        summary = []
        for customer in customers:
            summary.append({
                "customerId": customer.get("customerId"),
                "name": customer.get("name"),
                "email": customer.get("email"),
            })

        log('info', 'list-customers success', requestId=request_id, count=len(summary))
        return build_response(200, request_id, {'customers': summary})
    except Exception as e:  # noqa: BLE001
        log('error', 'list-customers failed', requestId=request_id, error=str(e))
        return build_response(500, request_id, {
            'errorCode': 'LIST_CUSTOMERS_ERROR',
            'message': 'Failed to list customers',
            'details': {'error': str(e)},
        })
