"""Agent Router - Single coordinator agent with all tools"""
from strands import Agent, tool
from strands.models import BedrockModel
import json
from agents.customer_agent import list_customers, get_customer_profile
from agents.product_agent import list_available_bonds, get_product_details, search_market_data
from agents.marketing_agent import send_email, get_recent_emails
from agents.recommendation_agent import get_bond_recommendations_for_customer, get_most_sellable_bond_with_customers


class AgentRouter:
    """Single coordinator agent with all tools integrated"""
    
    def __init__(self, customer_agent, product_agent, marketing_agent, suggestion_agent, recommendation_agent):
        # Store agents for reference (not used for tool execution)
        self.customer_agent = customer_agent
        self.product_agent = product_agent
        self.marketing_agent = marketing_agent
        self.suggestion_agent = suggestion_agent
        self.recommendation_agent = recommendation_agent
        
        model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
        model = BedrockModel(model_id=model_id)
        
        # Define all tools directly at this level
        @tool
        def customer_list_customers():
            """Get the list of all Bank X customers. Returns a summary list with customer ID, name, and email."""
            return list_customers()
        
        @tool
        def customer_get_profile(customer_id: str):
            """Get the full profile for a specific customer by their customer ID.
            
            Args:
                customer_id: The customer ID (e.g., 'CUST-001')
            
            Returns:
                Full customer profile including portfolio value, investment preferences, and bond interest
            """
            return get_customer_profile(customer_id)
        
        @tool
        def product_list_bonds():
            """Get a list of all available bond products. Returns a summary with product name, yield, maturity, and minimum investment for each bond."""
            return list_available_bonds()
        
        @tool
        def product_get_details(product_name: str):
            """Get detailed information about a financial product.
            
            Args:
                product_name: The name of the product (e.g., 'government-bond-y', 'UK Government Bond Series Y')
            
            Returns:
                Full product details including yield, maturity, minimum investment, and description
            """
            return get_product_details(product_name)
        
        @tool
        def product_search_market(product_type: str):
            """Search for market data and comparable products for a given product type.
            
            Args:
                product_type: The type of product (e.g., 'government_bond', 'corporate_bond', 'equity')
            
            Returns:
                Market analysis including yield trends and comparable products with description
            """
            return search_market_data(product_type)
        
        @tool
        def marketing_send_email(customer_email: str, subject: str, body: str, approved: bool = False, preview_id: str = ""):
            """Send an email to a customer. Requires two-step process: preview first, then send with approval.
            
            WORKFLOW:
            1. First call with approved=False (or omit approved) to get email preview and preview_id
            2. Show preview to user and ask for confirmation
            3. After user confirms, call again with approved=True and the preview_id from step 1
            
            Args:
                customer_email: The recipient's email address
                subject: The email subject line
                body: The email body content (plain text)
                approved: Set to True only after user has confirmed the preview (default: False)
                preview_id: The preview_id returned from the preview call (required when approved=True)
            
            Returns:
                Preview response (with preview_id) if approved=False, or confirmation message if approved=True
            """
            return send_email(customer_email, subject, body, approved, preview_id)
        
        @tool
        def marketing_get_recent_emails(limit: int = 10):
            """Get metadata for the most recently sent emails.
            
            Args:
                limit: Maximum number of recent emails to retrieve (default: 10)
            
            Returns:
                List of recent email metadata including timestamp, recipient, and subject
            """
            return get_recent_emails(limit)
        
        @tool
        def recommendation_get_bond_recommendations(customer_id: str):
            """Get personalized bond recommendations for a specific customer.
            
            Analyzes the customer's profile (risk tolerance, investment horizon, financial goals, 
            portfolio size, preferred sectors) against available bonds to provide tailored recommendations.
            
            Args:
                customer_id: The customer ID (e.g., 'CUST-001')
            
            Returns:
                Customer and bond data for the AI to analyze and generate natural language recommendations
            """
            return get_bond_recommendations_for_customer(customer_id)
        
        @tool
        def recommendation_find_most_sellable_bond():
            """Find the most sellable bond (highest demand) and identify all suitable customers.
            
            This tool:
            1. Identifies the bond with the highest sellability (demandScore/sellabilityRank)
            2. Returns all customer profiles for analysis
            3. Provides demand metrics and trends for the top bond
            
            Use this to answer questions like:
            - "Which bond is most sellable right now?"
            - "Find the most popular bond and who should buy it"
            - "Which bond has the highest demand and which customers would be interested?"
            
            Returns:
                JSON with the most sellable bond, all customers, and demand analytics
            """
            return get_most_sellable_bond_with_customers()
        
        # Create coordinator agent with all tools
        self.coordinator = Agent(
            model=model,
            tools=[
                customer_list_customers,
                customer_get_profile,
                product_list_bonds,
                product_get_details,
                product_search_market,
                marketing_send_email,
                marketing_get_recent_emails,
                recommendation_get_bond_recommendations,
                recommendation_find_most_sellable_bond
            ],
            system_prompt="""You are the Bank X Financial Assistant.

**Your Role:**
- Process user requests and use appropriate tools to fulfill them
- Provide comprehensive responses combining information from multiple sources when needed
- Guide users through workflows that require multiple steps
- Analyze customer profiles and recommend suitable bond products

**Available Tools:**

**Customer Management:**
- customer_list_customers(): List all customers with ID, name, email
- customer_get_profile(customer_id): Get detailed customer profile

**Product Information:**
- product_list_bonds(): Show all available bond products  
- product_get_details(product_name): Get detailed product information
- product_search_market(product_type): Research market trends and comparable products

**Bond Recommendations:**
- recommendation_get_bond_recommendations(customer_id): Generate personalized bond recommendations for a customer based on their risk tolerance, investment horizon, goals, and portfolio
- recommendation_find_most_sellable_bond(): Find the bond with highest demand/sellability and identify all suitable customers for it

**Email Operations:**
- marketing_send_email(customer_email, subject, body, approved, preview_id): Send marketing emails (requires two-step approval)
  * Step 1: Call with approved=False to preview email and get preview_id
  * Step 2: Show preview to user and ask for confirmation
  * Step 3: Call with approved=True and preview_id to actually send
- marketing_get_recent_emails(limit): View recently sent emails

**Workflow Examples:**

For "Show all bonds":
1. Use product_list_bonds() to get all available products

For "Get customer details":
1. Use customer_get_profile() with the customer ID

For "Recommend bonds for [customer]":
1. Use recommendation_get_bond_recommendations(customer_id) to analyze customer and available bonds
2. Provide natural language recommendations with clear reasoning about why each bond suits their profile

For "Find most sellable bond and suitable customers":
1. Use recommendation_find_most_sellable_bond() to get the top-demand bond and all customers
2. Analyze each customer against the bond characteristics
3. List customers who are suitable based on:
   - Interest in bonds (interestedInBonds field)
   - Portfolio value meets minimum investment
   - Risk tolerance matches bond risk rating
   - Investment goals align with bond features
   - Sector preferences match
4. Provide customer IDs and emails for matched customers
5. If user wants to send emails, coordinate with marketing workflow

For "Email customers about bonds":
1. Use product_get_details() to get product information
2. Use customer_list_customers() to identify target customers
3. For each email:
   a. Call marketing_send_email() with approved=False to get preview
   b. Show preview to user and ask for confirmation
   c. If user confirms, call marketing_send_email() again with approved=True and the preview_id
   d. If user declines, skip and move to next customer

For "Show market trends":
1. Use product_search_market() for market analysis

**Important Guidelines:**
- Always use tools to get current, accurate information
- Combine multiple tool calls when needed for comprehensive responses
- Present information clearly and professionally
- For email operations, ALWAYS follow the two-step approval process:
  1. Generate preview first (approved=False)
  2. Present preview to user and explicitly ask for confirmation
  3. Only send (approved=True with preview_id) after user confirms with "yes", "send", or similar affirmation
  4. Do NOT send emails without user confirmation
- For email operations, create personalized, detailed messages
- For recommendations, explain your analysis in conversational, natural language
- Ensure proper formatting for all responses""",
            callback_handler=None
        )
    
    async def stream_async(self, user_input: str):
        """Stream response from the coordinator agent"""
        async for event in self.coordinator.stream_async(user_input):
            yield event
    
    def __call__(self, user_input: str):
        """Synchronous call to coordinator agent"""
        return self.coordinator(user_input)


def create_agent_router(customer_agent, product_agent, marketing_agent, suggestion_agent, recommendation_agent):
    """Factory function to create an AgentRouter instance"""
    return AgentRouter(customer_agent, product_agent, marketing_agent, suggestion_agent, recommendation_agent)
