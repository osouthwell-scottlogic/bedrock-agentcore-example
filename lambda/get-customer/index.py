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
    """Get full customer profile by customer ID."""
    try:
        customer_id = event.get('customer_id')
        
        logger.info(f"Fetching customer profile: {customer_id}")
        
        if not customer_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'customer_id is required'})
            }
        
        lambda_client = boto3.client('lambda', config=boto_config)
        
        # Read customer file
        response = lambda_client.invoke(
            FunctionName=READ_FILE_FUNCTION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'filename': 'bank-x-customers.json'})
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        
        if result.get('statusCode') != 200:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Customer database not found'})
            }
        
        customers = body.get('content', [])
        
        # Find customer
        for customer in customers:
            if customer.get("customerId") == customer_id:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'customer': customer})
                }
        
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'Customer {customer_id} not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
