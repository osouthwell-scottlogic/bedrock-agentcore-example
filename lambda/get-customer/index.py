import json
import boto3
import os
import logging
import re
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


def is_valid_customer_id(customer_id: str) -> bool:
    return bool(customer_id) and re.match(r'^CUST-[0-9]{3,}$', customer_id)


def lambda_handler(event, context):
    request_id = getattr(context, 'aws_request_id', 'unknown')
    customer_id = event.get('customer_id')

    if not READ_FILE_FUNCTION_ARN:
        return build_response(500, request_id, {
            'errorCode': 'CONFIG_ERROR',
            'message': 'READ_FILE_FUNCTION_ARN is not configured',
            'details': {},
        })

    if not is_valid_customer_id(customer_id):
        return build_response(400, request_id, {
            'errorCode': 'VALIDATION_ERROR',
            'message': 'customer_id is required and must match ^CUST-[0-9]{3,}$',
            'details': {'customer_id': customer_id},
        })

    log('info', 'get-customer start', requestId=request_id, customerId=customer_id)

    try:
        lambda_client = boto3.client('lambda', config=boto_config)

        response = lambda_client.invoke(
            FunctionName=READ_FILE_FUNCTION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': 'customers/bank-x-customers.json'})
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

        for customer in customers:
            if customer.get("customerId") == customer_id:
                log('info', 'get-customer success', requestId=request_id, customerId=customer_id)
                return build_response(200, request_id, {'customer': customer})

        return build_response(404, request_id, {
            'errorCode': 'NOT_FOUND',
            'message': f'Customer {customer_id} not found',
            'details': {'customer_id': customer_id},
        })
    except Exception as e:  # noqa: BLE001
        log('error', 'get-customer failed', requestId=request_id, customerId=customer_id, error=str(e))
        return build_response(500, request_id, {
            'errorCode': 'GET_CUSTOMER_ERROR',
            'message': 'Failed to get customer profile',
            'details': {'error': str(e)},
        })
