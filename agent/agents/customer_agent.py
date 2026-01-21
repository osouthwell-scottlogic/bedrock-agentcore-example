"""Customer Service Agent - Handles customer queries and profiles"""
from strands import Agent, tool
import json
import boto3
import os
import time
from strands.models import BedrockModel

# Initialize Lambda client
AWS_REGION = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

LIST_CUSTOMERS_ARN = os.environ.get('LIST_CUSTOMERS_FUNCTION_ARN', '')
GET_CUSTOMER_ARN = os.environ.get('GET_CUSTOMER_FUNCTION_ARN', '')


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
                'agentName': 'customer_agent',
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
def list_customers():
    """Get the list of all Bank X customers. Returns a summary list with customer ID, name, and email."""
    result = invoke_lambda(LIST_CUSTOMERS_ARN, tool_name='list_customers')
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('customers', []), indent=2)


@tool
def get_customer_profile(customer_id: str):
    """Get the full profile for a specific customer by their customer ID.
    
    Args:
        customer_id: The customer ID (e.g., 'CUST-001')
    
    Returns:
        Full customer profile including portfolio value, investment preferences, and bond interest
    """
    result = invoke_lambda(GET_CUSTOMER_ARN, {'customer_id': customer_id}, tool_name='get_customer_profile')
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('customer', {}), indent=2)


def create_customer_agent():
    """Create and return the Customer Service Agent"""
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')
    model = BedrockModel(model_id=model_id)

    agent = Agent(
        model=model,
        tools=[list_customers, get_customer_profile],
        system_prompt="""You are the Bank X Customer Service Agent.

Your responsibilities:
- Answer questions about customer profiles and information
- Retrieve customer details and investment preferences
- Help identify customers based on their characteristics

When asked about customers:
1. Use list_customers() to get all customers
2. Use get_customer_profile(customer_id) to get detailed information
3. Filter and analyze customer data based on the query

You focus ONLY on customer-related queries. For product information or marketing campaigns, 
you will defer to the appropriate specialized agent.""",
        callback_handler=None
    )

    return agent
