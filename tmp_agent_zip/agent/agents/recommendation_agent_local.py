"""Bond Recommendation Agent - Local Version"""
from strands import Agent, tool
import json
import os
import time
from strands.models import BedrockModel

# Local data directory for development
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'local_data')


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
        # Load customer data
        customer_filepath = os.path.join(LOCAL_DATA_DIR, 'customers', 'bank-x-customers.json')
        if not os.path.exists(customer_filepath):
            return json.dumps({'error': 'Customer database not found'})
        
        with open(customer_filepath, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        
        customer = None
        for cust in customers:
            if cust.get('customerId') == customer_id:
                customer = cust
                break
        
        if not customer:
            return json.dumps({'error': f"Customer '{customer_id}' not found"})
        
        # Dynamically load all bond data
        bonds_dir = os.path.join(LOCAL_DATA_DIR, 'bonds')
        bond_files = [f for f in os.listdir(bonds_dir) if f.endswith('.json')] if os.path.exists(bonds_dir) else []
        
        bonds = []
        for filename in bond_files:
            filepath = os.path.join(bonds_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    bond = json.load(f)
                    bonds.append(bond)
        
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
        # Dynamically load all bond data
        bonds_dir = os.path.join(LOCAL_DATA_DIR, 'bonds')
        bond_files = [f for f in os.listdir(bonds_dir) if f.endswith('.json')] if os.path.exists(bonds_dir) else []
        
        bonds = []
        for filename in bond_files:
            filepath = os.path.join(bonds_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    bond = json.load(f)
                    bonds.append(bond)
        
        if not bonds:
            return json.dumps({'error': 'No bonds available'})
        
        # Find the most sellable bond (lowest sellabilityRank or highest demandScore)
        most_sellable = min(bonds, key=lambda b: b.get('sellabilityRank', 999))
        
        # Load all customers
        customer_filepath = os.path.join(LOCAL_DATA_DIR, 'customers', 'bank-x-customers.json')
        if not os.path.exists(customer_filepath):
            return json.dumps({'error': 'Customer database not found'})
        
        with open(customer_filepath, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        
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
    """Create and return the Bond Recommendation Agent (Local)"""
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
