import json
import boto3
import os
import logging
import time
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

READ_FILE_FUNCTION_ARN = os.environ.get('READ_FILE_FUNCTION_ARN', '')
LIST_FILES_FUNCTION_ARN = os.environ.get('LIST_FILES_FUNCTION_ARN', '')

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


def get_lambda_client():
    return boto3.client('lambda', config=boto_config)


def get_file_content(lambda_client, filename, request_id: str):
    try:
        response = lambda_client.invoke(
            FunctionName=READ_FILE_FUNCTION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': filename})
        )

        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))

        if result.get('statusCode') == 200:
            return body.get('content', {})

        log('warning', 'read-file returned non-200', requestId=request_id, filename=filename, statusCode=result.get('statusCode'), error=body.get('error'))
        return None
    except Exception as e:  # noqa: BLE001
        log('error', 'read-file invocation failed', requestId=request_id, filename=filename, error=str(e))
        return None


def lambda_handler(event, context):
    request_id = getattr(context, 'aws_request_id', 'unknown')

    if not READ_FILE_FUNCTION_ARN:
        return build_response(500, request_id, {
            'errorCode': 'CONFIG_ERROR',
            'message': 'READ_FILE_FUNCTION_ARN is not configured',
            'details': {},
        })

    if not LIST_FILES_FUNCTION_ARN:
        return build_response(500, request_id, {
            'errorCode': 'CONFIG_ERROR',
            'message': 'LIST_FILES_FUNCTION_ARN is not configured',
            'details': {},
        })

    log('info', 'list-bonds start', requestId=request_id)

    try:
        lambda_client = get_lambda_client()

        # Dynamically discover all bond files in the bonds/ directory
        list_response = lambda_client.invoke(
            FunctionName=LIST_FILES_FUNCTION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': 'bonds'})
        )
        
        list_result = json.loads(list_response['Payload'].read())
        list_body = json.loads(list_result.get('body', '{}'))
        
        if list_result.get('statusCode') != 200:
            log('warning', 'list-files failed for bonds directory', requestId=request_id)
            bond_files = []
        else:
            # Extract .json files from the directory listing
            files = list_body.get('files', [])
            bond_files = [f'bonds/{f}' for f in files if f.endswith('.json')]
        
        if not bond_files:
            log('warning', 'no bond files found', requestId=request_id)
            return build_response(200, request_id, {'bonds': []})

        bonds_summary = []
        for filename in bond_files:
            content = get_file_content(lambda_client, filename, request_id)
            if not content:
                continue
            try:
                bond = content if isinstance(content, dict) else json.loads(content)
                bonds_summary.append({
                    "productId": bond.get("productId"),
                    "name": bond.get("name"),
                    "type": bond.get("type"),
                    "yield": bond.get("yield"),
                    "maturity": bond.get("maturity"),
                    "minInvestment": bond.get("minInvestment"),
                    "creditRating": bond.get("creditRating"),
                })
            except Exception as parse_err:  # noqa: BLE001
                log('warning', 'bond parse failed', requestId=request_id, filename=filename, error=str(parse_err))
                continue

        log('info', 'list-bonds success', requestId=request_id, count=len(bonds_summary))
        return build_response(200, request_id, {'bonds': bonds_summary})
    except Exception as e:  # noqa: BLE001
        log('error', 'list-bonds failed', requestId=request_id, error=str(e))
        return build_response(500, request_id, {
            'errorCode': 'LIST_BONDS_ERROR',
            'message': 'Failed to list bonds',
            'details': {'error': str(e)},
        })
