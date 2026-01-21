"""Product Research Agent - Handles bond products and market data"""
from strands import Agent, tool
import json
import boto3
import os
import time
from strands.models import BedrockModel

# Initialize Lambda client
AWS_REGION = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

LIST_BONDS_ARN = os.environ.get('LIST_BONDS_FUNCTION_ARN', '')
GET_PRODUCT_ARN = os.environ.get('GET_PRODUCT_FUNCTION_ARN', '')
SEARCH_MARKET_ARN = os.environ.get('SEARCH_MARKET_FUNCTION_ARN', '')


def log_event(event: dict):
    print(json.dumps(event))


def invoke_lambda(function_arn: str, payload: dict = None, tool_name: str = None):
    """Helper to invoke Lambda and return parsed response."""
    start = time.perf_counter()
    try:
        if not function_arn:
            return {'error': 'Lambda function ARN not configured'}

        response = lambda_client.invoke(
            FunctionName=function_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload or {})
        )

        lambda_request_id = response.get('ResponseMetadata', {}).get('RequestId')
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        status_code = result.get('statusCode')
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        if status_code == 200:
            log_event({
                'eventType': 'agent.tool.success',
                'agentName': 'product_agent',
                'toolName': tool_name,
                'functionArn': function_arn,
                'lambdaInvokeRequestId': lambda_request_id,
                'requestId': body.get('requestId'),
                'durationMs': duration_ms,
                'timestamp': time.time(),
            })
            return body

        error_msg = body.get('error') or body.get('message') or 'Unknown error'
        return {'error': error_msg, 'requestId': body.get('requestId'), 'statusCode': status_code}
    except Exception as e:
        error_msg = f"Lambda invocation failed: {str(e)}"
        return {'error': error_msg}


@tool
def list_available_bonds():
    """Get a list of all available bond products. Returns a summary with product name, yield, maturity, and minimum investment for each bond."""
    result = invoke_lambda(LIST_BONDS_ARN, tool_name='list_available_bonds')
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('bonds', []), indent=2)


@tool
def get_product_details(product_name: str):
    """Get detailed information about a financial product.
    
    Args:
        product_name: The name of the product (e.g., 'government-bond-y', 'UK Government Bond Series Y')
    
    Returns:
        Full product details including yield, maturity, minimum investment, and description
    """
    result = invoke_lambda(GET_PRODUCT_ARN, {'product_name': product_name}, tool_name='get_product_details')
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('product', {}), indent=2)


@tool
def search_market_data(product_type: str):
    """Search for market data and comparable products for a given product type.
    
    Args:
        product_type: The type of product (e.g., 'government_bond', 'corporate_bond', 'equity')
    
    Returns:
        Market analysis including yield trends and comparable products with description
    """
    result = invoke_lambda(SEARCH_MARKET_ARN, {'product_type': product_type}, tool_name='search_market_data')
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('marketData', {}), indent=2)


def create_product_agent():
    """Create and return the Product Research Agent"""
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')
    model = BedrockModel(model_id=model_id)

    agent = Agent(
        model=model,
        tools=[list_available_bonds, get_product_details, search_market_data],
        system_prompt="""You are the Bank X Product Research Agent.

Your responsibilities:
- Provide information about bond products and financial instruments
- Research market data and trends
- Compare products and analyze market conditions

When asked about products:
1. Use list_available_bonds() to see all available bond products
2. Use get_product_details(product_name) for detailed product information
3. Use search_market_data(product_type) for market analysis and comparable products

You focus ONLY on product and market research. For customer information or marketing campaigns,
you will defer to the appropriate specialized agent.""",
        callback_handler=None
    )

    return agent
