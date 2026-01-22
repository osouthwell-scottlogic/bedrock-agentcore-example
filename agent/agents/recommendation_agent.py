"""Bond Recommendation Agent - Analyzes customer profiles and recommends suitable bonds"""
from strands import Agent, tool
import json
import boto3
import os
import time
from strands.models import BedrockModel

# Initialize Lambda client
AWS_REGION = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

GET_CUSTOMER_ARN = os.environ.get('GET_CUSTOMER_FUNCTION_ARN', '')
LIST_CUSTOMERS_ARN = os.environ.get('LIST_CUSTOMERS_FUNCTION_ARN', '')
LIST_BONDS_ARN = os.environ.get('LIST_BONDS_FUNCTION_ARN', '')


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
                'agentName': 'recommendation_agent',
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
def get_bond_recommendations_for_customer(customer_id: str):
    """Retrieve customer profile and all available bonds for analysis and recommendation.
    
    This tool provides the Claude model with comprehensive customer and bond data
    to analyze and generate personalized bond recommendations based on:
    - Customer risk tolerance, investment horizon, and financial goals
    - Bond risk rating, ESG score, volatility, sector exposure, and liquidity
    - Portfolio fit and suitability matching
    
    Args:
        customer_id: The customer ID (e.g., 'CUST-001')
    
    Returns:
        A comprehensive JSON object containing the customer profile and all available bonds
        for Claude to analyze and generate recommendations in natural language
    """
    try:
        # Fetch customer profile
        customer_result = invoke_lambda(GET_CUSTOMER_ARN, {'customer_id': customer_id}, tool_name='get_customer_profile')
        if 'error' in customer_result:
            return json.dumps({'error': f"Could not fetch customer: {customer_result['error']}"})
        
        customer = customer_result.get('customer', {})
        
        # Fetch all bonds
        bonds_result = invoke_lambda(LIST_BONDS_ARN, {}, tool_name='list_bonds')
        if 'error' in bonds_result:
            return json.dumps({'error': f"Could not fetch bonds: {bonds_result['error']}"})
        
        bonds = bonds_result.get('bonds', [])
        
        # Combine into recommendation context
        recommendation_data = {
            'customer': customer,
            'availableBonds': bonds,
            'recommendationContext': {
                'timestamp': time.time(),
                'customerId': customer_id,
                'bondCount': len(bonds)
            }
        }
        
        return json.dumps(recommendation_data, indent=2)
    except Exception as e:
        return json.dumps({'error': f"Error fetching recommendation data: {str(e)}"})


@tool
def get_most_sellable_bond_with_customers():
    """Find the most sellable bond (highest demand) and identify all customers who would be suitable buyers.
    
    This tool analyzes all bonds by their sellability ranking (demandScore/sellabilityRank) 
    and matches the top bond with suitable customers based on their investment profiles.
    
    Returns:
        JSON object containing:
        - The most sellable bond with all details and demand metrics
        - List of all customers in the database
        - Matching analysis showing which customers are suitable for this bond based on:
          * Risk tolerance alignment
          * Portfolio value vs minimum investment
          * Investment goals and sector preferences
          * Interest in bonds
    """
    try:
        # Fetch all bonds
        bonds_result = invoke_lambda(LIST_BONDS_ARN, {}, tool_name='list_bonds')
        if 'error' in bonds_result:
            return json.dumps({'error': f"Could not fetch bonds: {bonds_result['error']}"})
        
        bonds = bonds_result.get('bonds', [])
        
        if not bonds:
            return json.dumps({'error': 'No bonds available'})
        
        # Find the most sellable bond (lowest sellabilityRank or highest demandScore)
        most_sellable = min(bonds, key=lambda b: b.get('sellabilityRank', 999))
        
        # Fetch all customers from Lambda-backed customer agent
        customers_result = invoke_lambda(LIST_CUSTOMERS_ARN, {}, tool_name='list_customers')
        customers = customers_result.get('customers', []) if isinstance(customers_result, dict) else []
        
        result = {
            'mostSellableBond': most_sellable,
            'allCustomers': customers,
            'analysisContext': {
                'timestamp': time.time(),
                'totalBonds': len(bonds),
                'totalCustomers': len(customers),
                'bondDemandScore': most_sellable.get('demandScore'),
                'bondSellabilityRank': most_sellable.get('sellabilityRank'),
                'bondDemandTrend': most_sellable.get('demandTrend')
            }
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({'error': f"Error analyzing sellable bonds: {str(e)}"})


def create_recommendation_agent():
    """Create and return the Bond Recommendation Agent"""
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')
    model = BedrockModel(model_id=model_id)

    agent = Agent(
        model=model,
        tools=[get_bond_recommendations_for_customer, get_most_sellable_bond_with_customers],
        system_prompt="""You are the Bank X Bond Recommendation Agent.

Your responsibilities:
- Analyze customer profiles and preferences to recommend suitable bond products
- Consider customer risk tolerance, investment horizon, financial goals, and portfolio size
- Match customers with bonds based on risk rating, ESG scores, sector alignment, and liquidity needs
- Identify the most sellable bonds and find suitable customers for them
- Provide natural language explanations for recommendations

When recommending bonds for a customer:
1. Use get_bond_recommendations_for_customer(customer_id) to fetch customer and bond data
2. Analyze the customer's investment profile:
   - Risk tolerance (low/medium/high)
   - Investment horizon (years)
   - Investment goals (capital preservation, income generation, growth, capital appreciation)
   - Preferred sectors
   - Liquidity needs (high/medium/low)
   - Portfolio value and annual income
3. Evaluate bonds based on:
   - Risk rating alignment with customer tolerance
   - ESG score alignment with values
   - Volatility and liquidity match
   - Minimum investment vs. portfolio value
   - Sector exposure preferences
   - Yield and maturity alignment with goals
4. Generate personalized recommendations with clear reasoning
5. Present findings in friendly, conversational natural language

When finding the most sellable bond and suitable customers:
1. Use get_most_sellable_bond_with_customers() to get the top-demand bond and all customers
2. Analyze the bond's characteristics (demandScore, sellabilityRank, demandTrend)
3. Review each customer's profile to determine suitability:
   - Check if customer is interested in bonds (interestedInBonds field)
   - Verify portfolio value meets minimum investment requirement
   - Match risk tolerance with bond risk rating
   - Align investment goals with bond features
   - Consider sector preferences and liquidity needs
4. Create a list of suitable customers with explanations
5. Return customer IDs and emails for those who match

You focus ONLY on bond recommendations and customer matching. For sending emails, 
defer to the Marketing Agent.""",
        callback_handler=None
    )

    return agent
