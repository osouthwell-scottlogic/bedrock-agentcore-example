from strands import Agent, tool
from strands_tools import calculator # Import the calculator tool
import json
import os
from datetime import datetime
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Local data directory for development
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), 'local_data')
SENT_EMAILS_DIR = os.path.join(LOCAL_DATA_DIR, 'sent_emails')

# Ensure sent_emails directory exists
os.makedirs(SENT_EMAILS_DIR, exist_ok=True)

# MCP Tools - Bank X Financial Product Marketing
@tool
def list_available_bonds():
    """Get a list of all available bond products. Returns a summary with product name, yield, maturity, and minimum investment for each bond."""
    try:
        bond_files = [
            'government-bond-y.json',
            'corporate-bond-a.json',
            'municipal-bond-m.json',
            'green-bond-g.json'
        ]
        
        bonds_summary = []
        for filename in bond_files:
            filepath = os.path.join(LOCAL_DATA_DIR, filename)
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
def list_customers():
    """Get the list of all Bank X customers. Returns a summary list with customer ID, name, and email."""
    try:
        filepath = os.path.join(LOCAL_DATA_DIR, 'bank-x-customers.json')
        
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
        filepath = os.path.join(LOCAL_DATA_DIR, 'bank-x-customers.json')
        
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
        
        filepath = os.path.join(LOCAL_DATA_DIR, filename)
        
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
        # Mock market data based on product type
        if 'bond' in product_type.lower():
            market_data = {
                "productType": product_type,
                "marketSummary": "Government bond yields have stabilized in Q4 2025 following the Bank of England's recent policy decisions. Investor appetite for safe-haven assets remains strong amid global economic uncertainty.",
                "yieldTrends": {
                    "current": "4.75%",
                    "3MonthAvg": "4.62%",
                    "6MonthAvg": "4.55%",
                    "1YearAvg": "4.40%",
                    "trend": "Upward - yields have increased 35 basis points over the past year"
                },
                "comparableProducts": [
                    {
                        "name": "UK Government Bond Series X",
                        "yield": "4.50%",
                        "maturity": "7 years",
                        "creditRating": "AA"
                    },
                    {
                        "name": "UK Government Bond Series Z",
                        "yield": "5.00%",
                        "maturity": "15 years",
                        "creditRating": "AA"
                    },
                    {
                        "name": "German Government Bund",
                        "yield": "3.80%",
                        "maturity": "10 years",
                        "creditRating": "AAA"
                    },
                    {
                        "name": "US Treasury Bond",
                        "yield": "4.90%",
                        "maturity": "10 years",
                        "creditRating": "AA+"
                    }
                ],
                "description": "The UK government bond market shows healthy demand with competitive yields relative to European peers. Series Y's 4.75% yield positions it attractively in the 10-year maturity segment, offering a premium over German Bunds while maintaining strong credit quality. Current market conditions favor fixed-income investments as central banks signal a pause in rate adjustments."
            }
        else:
            market_data = {
                "productType": product_type,
                "description": f"Market data for {product_type} is currently unavailable. Please contact your financial advisor.",
                "comparableProducts": []
            }
        
        return json.dumps(market_data, indent=2)
    except Exception as e:
        return f"Error searching market data: {str(e)}"

@tool
def send_email(customer_email: str, subject: str, body: str):
    """Send an email to a customer. Writes the email to a file in the sent_emails folder organized by date.
    
    Args:
        customer_email: The recipient's email address
        subject: The email subject line
        body: The email body content (plain text)
    
    Returns:
        Confirmation message indicating success or failure
    """
    try:
        # Create date-based subfolder
        today = datetime.now().strftime('%Y-%m-%d')
        date_folder = os.path.join(SENT_EMAILS_DIR, today)
        os.makedirs(date_folder, exist_ok=True)
        
        # Create filename with timestamp, email, and subject
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        subject_slug = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in subject.lower())[:50]
        filename = f"{timestamp}_{customer_email}_{subject_slug}.txt"
        filepath = os.path.join(date_folder, filename)
        
        # Write email to file
        email_content = f"""To: {customer_email}
Subject: {subject}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(email_content)
        
        return f"Email sent successfully to {customer_email}"
    except Exception as e:
        # Skip individual failures as per requirements
        return f"Failed to send email to {customer_email}: {str(e)}"

@tool
def get_recent_emails(limit: int = 10):
    """Get metadata for the most recently sent emails.
    
    Args:
        limit: Maximum number of recent emails to retrieve (default: 10)
    
    Returns:
        List of recent email metadata including timestamp, recipient, and subject
    """
    try:
        email_files = []
        
        # Scan sent_emails directory and subdirectories
        for root, dirs, files in os.walk(SENT_EMAILS_DIR):
            for filename in files:
                if filename.endswith('.txt'):
                    filepath = os.path.join(root, filename)
                    # Parse filename: {timestamp}_{email}_{subject}.txt
                    parts = filename[:-4].split('_', 2)
                    if len(parts) >= 3:
                        timestamp_str, email, subject_slug = parts
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
                            email_files.append({
                                'timestamp': timestamp,
                                'recipient': email,
                                'subject': subject_slug.replace('-', ' ').title(),
                                'filepath': filepath
                            })
                        except ValueError:
                            continue
        
        # Sort by timestamp descending
        email_files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take top N
        recent = email_files[:limit]
        
        # Format output
        result = []
        for email in recent:
            result.append({
                'timestamp': email['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'recipient': email['recipient'],
                'subject': email['subject']
            })
        
        if result:
            return json.dumps(result, indent=2)
        else:
            return "No sent emails found"
    except Exception as e:
        return f"Error retrieving recent emails: {str(e)}"

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
