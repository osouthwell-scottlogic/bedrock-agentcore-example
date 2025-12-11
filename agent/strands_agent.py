from strands import Agent, tool
from strands_tools import calculator # Import the calculator tool
import json
import boto3
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Get AWS region from environment or default to the region where the agent is running
AWS_REGION = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))

# Initialize Lambda client for MCP tool invocations with explicit region
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

# Get Lambda function ARNs from environment
LIST_BONDS_ARN = os.environ.get('LIST_BONDS_FUNCTION_ARN', '')
LIST_CUSTOMERS_ARN = os.environ.get('LIST_CUSTOMERS_FUNCTION_ARN', '')
GET_CUSTOMER_ARN = os.environ.get('GET_CUSTOMER_FUNCTION_ARN', '')
GET_PRODUCT_ARN = os.environ.get('GET_PRODUCT_FUNCTION_ARN', '')
SEARCH_MARKET_ARN = os.environ.get('SEARCH_MARKET_FUNCTION_ARN', '')
SEND_EMAIL_ARN = os.environ.get('SEND_EMAIL_FUNCTION_ARN', '')
GET_RECENT_EMAILS_ARN = os.environ.get('GET_RECENT_EMAILS_FUNCTION_ARN', '')

def invoke_lambda(function_arn: str, payload: dict = None):
    """Helper to invoke Lambda and return parsed response."""
    try:
        if not function_arn:
            return {'error': 'Lambda function ARN not configured'}
        
        print(f"Invoking Lambda: {function_arn}")
        response = lambda_client.invoke(
            FunctionName=function_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload or {})
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Lambda response status: {result.get('statusCode')}")
        
        body = json.loads(result.get('body', '{}'))
        
        if result.get('statusCode') == 200:
            return body
        else:
            error_msg = body.get('error', 'Unknown error')
            print(f"Lambda returned error: {error_msg}")
            return {'error': error_msg}
    except Exception as e:
        error_msg = f"Lambda invocation failed: {str(e)}"
        print(error_msg)
        return {'error': error_msg}

@tool
def list_available_bonds():
    """Get a list of all available bond products. Returns a summary with product name, yield, maturity, and minimum investment for each bond."""
    result = invoke_lambda(LIST_BONDS_ARN)
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('bonds', []), indent=2)

@tool
def list_customers():
    """Get the list of all Bank X customers. Returns a summary list with customer ID, name, and email."""
    result = invoke_lambda(LIST_CUSTOMERS_ARN)
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
    result = invoke_lambda(GET_CUSTOMER_ARN, {'customer_id': customer_id})
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('customer', {}), indent=2)

@tool
def get_product_details(product_name: str):
    """Get detailed information about a financial product.
    
    Args:
        product_name: The name of the product (e.g., 'government-bond-y', 'UK Government Bond Series Y')
    
    Returns:
        Full product details including yield, maturity, minimum investment, and description
    """
    result = invoke_lambda(GET_PRODUCT_ARN, {'product_name': product_name})
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
    result = invoke_lambda(SEARCH_MARKET_ARN, {'product_type': product_type})
    if 'error' in result:
        return f"Error: {result['error']}"
    return json.dumps(result.get('marketData', {}), indent=2)

@tool
def send_email(customer_email: str, subject: str, body: str):
    """Send an email to a customer. Writes the email to S3 in the sent-emails folder organized by date.
    
    Args:
        customer_email: The recipient's email address
        subject: The email subject line
        body: The email body content (plain text)
    
    Returns:
        Confirmation message indicating success or failure
    """
    result = invoke_lambda(SEND_EMAIL_ARN, {
        'customer_email': customer_email,
        'subject': subject,
        'body': body
    })
    if 'error' in result:
        return f"Failed to send email: {result['error']}"
    return result.get('message', 'Email sent successfully')

@tool
def get_recent_emails(limit: int = 10):
    """Get metadata for the most recently sent emails.
    
    Args:
        limit: Maximum number of recent emails to retrieve (default: 10)
    
    Returns:
        List of recent email metadata including timestamp, recipient, and subject
    """
    result = invoke_lambda(GET_RECENT_EMAILS_ARN, {'limit': limit})
    if 'error' in result:
        return f"Error: {result['error']}"
    emails = result.get('emails', [])
    if not emails:
        return "No sent emails found"
    return json.dumps(emails, indent=2)

model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
model = BedrockModel(
    model_id=model_id,
)

agent = Agent(
    model=model,
    tools=[list_available_bonds, list_customers, get_customer_profile, get_product_details, search_market_data, send_email, get_recent_emails],
    system_prompt="""You are a Bank X Financial Assistant specializing in marketing financial products to qualified customers.

**ON FIRST INTERACTION**: When the user first connects, immediately call list_available_bonds() and present all 4 available bond products in a clear, formatted summary showing: product name, yield, maturity, minimum investment, and credit rating. Then ask which bond they'd like to market to customers or if they'd like more details about any specific bond.

Your workflow for "email interesting customers" requests:

1. **Research the Product**: Use get_product_details() to understand the financial product being offered (e.g., Government Bond Y)

2. **Analyze Market Context**: Use search_market_data() to gather current yield trends and comparable products

3. **Identify Qualified Customers**: 
   - Use list_customers() to see all customers
   - Filter customers where:
     * interestedInBonds == true (customer has expressed interest in bonds)
     * portfolioValue >= product's minInvestment (customer meets minimum investment threshold)
   - For matched customers, use get_customer_profile() to get full details

4. **Generate Personalized Email Drafts**:
   - Create a tailored plain-text email for each qualified customer
   - Include: Customer's name, product highlights (yield, maturity, features), market context, and call to action
   - Keep emails professional, informative, and compliant

5. **Present for Approval**:
   - Show a summary of ALL matched customers
   - Display the personalized email draft for each customer
   - Clearly ask: "Should I send these [N] emails? Please reply 'yes' to proceed."
   - Wait indefinitely for user confirmation - DO NOT re-prompt or rush the user

6. **Send Emails After Confirmation**:
   - Only proceed if user explicitly confirms with "yes", "send", "proceed", or similar affirmative response
   - Use send_email() for each customer
   - If any email fails, continue with remaining emails (skip failures)
   - Provide a final summary showing successful sends and any failures

Additional Capabilities:
- get_recent_emails(limit): Show recently sent email metadata
- You can answer questions about products, customers, and market data without sending emails

Remember: NEVER send emails without explicit user approval. The approval step is mandatory for compliance and human oversight.""",
    callback_handler=None
)

@app.entrypoint
async def agent_invocation(payload):
    """
    Invoke the agent with a payload

    IMPORTANT: Payload structure varies depending on invocation method:
    - Direct invocation (Python SDK, Console, agentcore CLI): {"prompt": "..."}
    - AWS SDK invocation (JS/Java/etc via InvokeAgentRuntimeCommand): {"input": {"prompt": "..."}}

    The AWS SDK automatically wraps payloads in an "input" field as part of the API contract.
    This function handles both formats for maximum compatibility.
    """
    # Handle both dict and string payloads
    if isinstance(payload, str):
        payload = json.loads(payload)

    # Extract the prompt from the payload
    # Try AWS SDK format first (most common for production): {"input": {"prompt": "..."}}
    # Fall back to direct format: {"prompt": "..."}
    user_input = None
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
        else:
            user_input = payload.get("prompt")

    if not user_input:
        raise ValueError(f"No prompt found in payload. Expected {{'prompt': '...'}} or {{'input': {{'prompt': '...'}}}}. Received: {payload}")

    # response = agent(user_input)
    # response_text = response.message['content'][0]['text']
    stream = agent.stream_async(user_input)
    async for event in stream:
        if (event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text')):
            print(event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text'))
            yield (event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text'))

    # return response_text

if __name__ == "__main__":
    app.run()
