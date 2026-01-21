"""Customer Service Agent - Local Version"""
from strands import Agent, tool
import json
import os
from strands.models import BedrockModel

# Local data directory for development
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'local_data')


@tool
def list_customers():
    """Get the list of all Bank X customers. Returns a summary list with customer ID, name, and email."""
    try:
        filepath = os.path.join(LOCAL_DATA_DIR, 'customers', 'bank-x-customers.json')
        
        if not os.path.exists(filepath):
            return "Error: Customer database not found"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        
        summary = []
        for customer in customers:
            summary.append({
                "customerId": customer.get("customerId"),
                "name": customer.get("name"),
                "email": customer.get("email")
            })
        
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error listing customers: {str(e)}"


@tool
def get_customer_profile(customer_id: str):
    """Get the full profile for a specific customer by their customer ID.
    
    Args:
        customer_id: The customer ID (e.g., 'CUST-001')
    
    Returns:
        Full customer profile including portfolio value, investment preferences, and bond interest
    """
    try:
        filepath = os.path.join(LOCAL_DATA_DIR, 'customers', 'bank-x-customers.json')
        
        if not os.path.exists(filepath):
            return f"Error: Customer database not found"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        
        for customer in customers:
            if customer.get("customerId") == customer_id:
                return json.dumps(customer, indent=2)
        
        return f"Customer '{customer_id}' not found"
    except Exception as e:
        return f"Error reading customer profile: {str(e)}"


def create_customer_agent():
    """Create and return the Customer Service Agent (Local)"""
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')
    model = BedrockModel(model_id=model_id)

    # Note: No tools are provided here - this agent processes customer queries
    # through its system prompt and context, with tools managed at the coordinator level
    agent = Agent(
        model=model,
        tools=[],
        system_prompt="""You are the Bank X Customer Service Agent.

Your responsibilities:
- Answer questions about customer profiles and information
- Help identify customers based on their characteristics
- Provide analysis of customer data

Process customer-related requests using the information available in the context.
Focus ONLY on customer-related queries.""",
        callback_handler=None
    )

    return agent
