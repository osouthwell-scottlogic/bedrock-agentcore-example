import json
import boto3
import os
import logging
from botocore.config import Config

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

READ_FILE_FUNCTION_ARN = os.environ.get('READ_FILE_FUNCTION_ARN', '')

# Boto3 config with retries
boto_config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=10
)

def lambda_handler(event, context):
    """Get detailed product information."""
    try:
        product_name = event.get('product_name')
        
        logger.info(f"Fetching product details: {product_name}")
        
        if not product_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'product_name is required'})
            }
        
        lambda_client = boto3.client('lambda', config=boto_config)
        
        # Normalize product name to filename
        filename = product_name.lower().replace(' ', '-').replace('uk-', '').replace('series-', '')
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Read product file
        response = lambda_client.invoke(
            FunctionName=READ_FILE_FUNCTION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': filename})
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        
        if result.get('statusCode') == 200:
            return {
                'statusCode': 200,
                'body': json.dumps({'product': body.get('content')})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Product {product_name} not found'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
