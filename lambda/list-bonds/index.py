import json
import boto3
import os
import logging
from botocore.config import Config

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Environment variables
S3_BUCKET = os.environ.get('S3_DATA_BUCKET', '')
READ_FILE_FUNCTION_ARN = os.environ.get('READ_FILE_FUNCTION_ARN', '')

# Boto3 config with retries
boto_config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=10
)

def get_lambda_client():
    """Get Lambda client with connection pooling."""
    return boto3.client('lambda', config=boto_config)

def get_file_content(lambda_client, filename):
    """Read file content from S3 via Lambda."""
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
        logger.warning(f"Failed to read {filename}: {body.get('error')}")
        return None
    except Exception as e:
        logger.error(f"Error reading {filename}: {str(e)}")
        return None

def lambda_handler(event, context):
    """List all available bond products."""
    logger.info("Listing available bonds")
    
    try:
        lambda_client = get_lambda_client()
        
        bond_files = [
            'government-bond-y.json',
            'corporate-bond-a.json',
            'municipal-bond-m.json',
            'green-bond-g.json'
        ]
        
        bonds_summary = []
        for filename in bond_files:
            try:
                content = get_file_content(lambda_client, filename)
                if content:
                    bond = content if isinstance(content, dict) else json.loads(content)
                    bonds_summary.append({
                        "productId": bond.get("productId"),
                        "name": bond.get("name"),
                        "type": bond.get("type"),
                        "yield": bond.get("yield"),
                        "maturity": bond.get("maturity"),
                        "minInvestment": bond.get("minInvestment"),
                        "creditRating": bond.get("creditRating")
                    })
            except Exception:
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({'bonds': bonds_summary})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
