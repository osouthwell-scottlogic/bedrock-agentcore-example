"""Product Research Agent - Local Version"""
from strands import Agent, tool
import json
import os
from strands.models import BedrockModel

# Local data directory for development
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'local_data')


@tool
def list_available_bonds():
    """Get a list of all available bond products. Returns a summary with product name, yield, maturity, and minimum investment for each bond."""
    try:
        bonds_dir = os.path.join(LOCAL_DATA_DIR, 'bonds')
        
        # Dynamically discover all .json files in the bonds directory
        bond_files = [f for f in os.listdir(bonds_dir) if f.endswith('.json')]
        
        if not bond_files:
            return "No bond products available"
        
        bonds_summary = []
        for filename in bond_files:
            filepath = os.path.join(LOCAL_DATA_DIR, 'bonds', filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    bond = json.load(f)
                    bonds_summary.append({
                        "productId": bond.get("productId"),
                        "name": bond.get("name"),
                        "type": bond.get("type"),
                        "yield": bond.get("yield"),
                        "maturity": bond.get("maturity"),
                        "minInvestment": bond.get("minInvestment"),
                        "creditRating": bond.get("creditRating")
                    })
        
        return json.dumps(bonds_summary, indent=2)
    except Exception as e:
        return f"Error listing bonds: {str(e)}"


@tool
def get_product_details(product_name: str):
    """Get detailed information about a financial product.
    
    Args:
        product_name: The name of the product (e.g., 'government-bond-y', 'UK Government Bond Series Y')
    
    Returns:
        Full product details including yield, maturity, minimum investment, and description
    """
    try:
        # Normalize product name to filename
        filename = product_name.lower().replace(' ', '-').replace('uk-', '').replace('series-', '')
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(LOCAL_DATA_DIR, 'bonds', filename)
        
        if not os.path.exists(filepath):
            return f"Product '{product_name}' not found. Available products: government-bond-y.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            product = json.load(f)
        
        return json.dumps(product, indent=2)
    except Exception as e:
        return f"Error reading product details: {str(e)}"


@tool
def search_market_data(product_type: str):
    """Search for market data and comparable products for a given product type.
    
    Args:
        product_type: The type of product (e.g., 'government_bond', 'corporate_bond', 'equity')
    
    Returns:
        Market analysis including yield trends and comparable products with description
    """
    try:
        # Determine market data file based on product type
        if 'bond' in product_type.lower():
            filepath = os.path.join(LOCAL_DATA_DIR, 'market-data', 'bond-market-data.json')
        else:
            # No market data available for this product type
            return json.dumps({
                "productType": product_type,
                "description": f"Market data for {product_type} is currently unavailable. Please contact your financial advisor.",
                "comparableProducts": []
            }, indent=2)
        
        if not os.path.exists(filepath):
            return f"Market data not found for {product_type}"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            market_data_raw = json.load(f)
        
        # Extract bond market data and add product type
        bond_data = market_data_raw.get('bonds', {})
        market_data = {
            'productType': product_type,
            **bond_data
        }
        
        return json.dumps(market_data, indent=2)
    except Exception as e:
        return f"Error searching market data: {str(e)}"


def create_product_agent():
    """Create and return the Product Research Agent (Local)"""
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')
    model = BedrockModel(model_id=model_id)

    # Note: No tools are provided here - this agent processes product queries
    # through its system prompt and context, with tools managed at the coordinator level
    agent = Agent(
        model=model,
        tools=[],
        system_prompt="""You are the Bank X Product Research Agent.

Your responsibilities:
- Provide information about bond products and financial instruments
- Research market data and trends
- Compare products and analyze market conditions

Process product and market-related requests using available information.
Focus ONLY on product and market research.""",
        callback_handler=None
    )

    return agent
