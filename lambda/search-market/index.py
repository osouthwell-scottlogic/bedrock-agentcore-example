import json
import boto3
import os
from datetime import datetime

# AWS clients
s3_client = boto3.client('s3')

# Environment variables
S3_DATA_BUCKET = os.environ.get('S3_DATA_BUCKET')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

def log(level, message, **meta):
    """Emit structured JSON log."""
    log_entry = {
        'level': level,
        'message': message,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        **meta
    }
    print(json.dumps(log_entry))

def build_response(status_code, request_id, payload):
    """Build uniform response structure."""
    return {
        'statusCode': status_code,
        'body': json.dumps(payload if status_code == 200 else {
            'errorCode': payload.get('errorCode', 'InternalError'),
            'message': payload.get('message', 'An error occurred'),
            'requestId': request_id,
            'details': payload.get('details', {})
        })
    }

def lambda_handler(event, context):
    """Search for market data and comparable products from S3."""
    request_id = context.request_id
    
    log('INFO', 'Search market invoked', requestId=request_id, functionName=context.function_name)
    
    # Validate configuration
    if not S3_DATA_BUCKET:
        log('ERROR', 'Missing S3_DATA_BUCKET environment variable', requestId=request_id)
        return build_response(500, request_id, {
            'errorCode': 'ConfigurationError',
            'message': 'S3_DATA_BUCKET not configured'
        })
    
    try:
        # Extract and validate product_type
        product_type = event.get('product_type', '').strip()
        if not product_type:
            log('WARN', 'Missing product_type parameter', requestId=request_id)
            return build_response(400, request_id, {
                'errorCode': 'ValidationError',
                'message': 'product_type is required',
                'details': {'parameter': 'product_type'}
            })
        
        log('INFO', 'Searching market data', requestId=request_id, productType=product_type)
        
        # Determine market data file based on product type
        if 'bond' in product_type.lower():
            market_data_key = 'client-details/market-data/bond-market-data.json'
        else:
            # No market data available for this product type
            log('INFO', 'No market data available for product type', requestId=request_id, productType=product_type)
            return build_response(200, request_id, {
                'marketData': {
                    'productType': product_type,
                    'description': f'Market data for {product_type} is currently unavailable. Please contact your financial advisor.',
                    'comparableProducts': []
                }
            })
        
        # Read market data from S3
        try:
            response = s3_client.get_object(Bucket=S3_DATA_BUCKET, Key=market_data_key)
            market_data_raw = json.loads(response['Body'].read().decode('utf-8'))
        except s3_client.exceptions.NoSuchKey:
            log('ERROR', 'Market data file not found in S3', requestId=request_id, key=market_data_key)
            return build_response(404, request_id, {
                'errorCode': 'NotFoundError',
                'message': 'Market data not found',
                'details': {'key': market_data_key}
            })
        except Exception as s3_err:
            log('ERROR', 'Failed to read market data from S3', requestId=request_id, error=str(s3_err))
            return build_response(500, request_id, {
                'errorCode': 'InternalError',
                'message': 'Failed to retrieve market data',
                'details': {'error': str(s3_err)}
            })
        
        # Extract bond market data and add product type
        bond_data = market_data_raw.get('bonds', {})
        market_data = {
            'productType': product_type,
            **bond_data
        }
        
        log('INFO', 'Successfully retrieved market data', requestId=request_id, productType=product_type, eventType='search_market')
        
        return build_response(200, request_id, {'marketData': market_data})
        
    except Exception as e:
        log('ERROR', 'Unexpected error in search market', requestId=request_id, error=str(e), eventType='search_market_error')
        return build_response(500, request_id, {
            'errorCode': 'InternalError',
            'message': 'An unexpected error occurred',
            'details': {'error': str(e)}
        })
