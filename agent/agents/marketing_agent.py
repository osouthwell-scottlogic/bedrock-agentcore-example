"""Marketing Agent - Handles email campaigns and approvals"""
from strands import Agent, tool
import json
import boto3
import os
import time
from strands.models import BedrockModel

# Initialize Lambda client
AWS_REGION = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

SEND_EMAIL_ARN = os.environ.get('SEND_EMAIL_FUNCTION_ARN', '')
GET_RECENT_EMAILS_ARN = os.environ.get('GET_RECENT_EMAILS_FUNCTION_ARN', '')


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
                'agentName': 'marketing_agent',
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
def send_email(customer_email: str, subject: str, body: str, approved: bool = False, preview_id: str = ""):
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
    result = invoke_lambda(SEND_EMAIL_ARN, {
        'customer_email': customer_email,
        'subject': subject,
        'body': body,
        'approved': approved,
        'preview_id': preview_id
    }, tool_name='send_email')
    
    if 'error' in result:
        return f"Failed to send email: {result['error']}"
    
    # If preview mode (status=PREVIEW), return structured preview for agent to show user
    if result.get('status') == 'PREVIEW':
        preview_data = result.get('email_preview', {})
        pid = result.get('preview_id', '')
        return f"""EMAIL PREVIEW GENERATED (Preview ID: {pid})

To: {preview_data.get('to', '')}
Subject: {preview_data.get('subject', '')}

{preview_data.get('body', '')}

---
PREVIEW ID: {pid}

Please review this email carefully. To send, respond with "send" or "yes" to confirm.
To cancel, respond with "no" or "cancel"."""
    
    # Approved mode - email sent
    return result.get('message', 'Email sent successfully')


@tool
def get_recent_emails(limit: int = 10):
    """Get metadata for the most recently sent emails.
    
    Args:
        limit: Maximum number of recent emails to retrieve (default: 10)
    
    Returns:
        List of recent email metadata including timestamp, recipient, and subject
    """
    result = invoke_lambda(GET_RECENT_EMAILS_ARN, {'limit': limit}, tool_name='get_recent_emails')
    if 'error' in result:
        return f"Error: {result['error']}"
    emails = result.get('emails', [])
    if not emails:
        return "No sent emails found"
    return json.dumps(emails, indent=2)


def create_marketing_agent():
    """Create and return the Marketing Agent"""
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')
    model = BedrockModel(model_id=model_id)

    agent = Agent(
        model=model,
        tools=[send_email, get_recent_emails],
        system_prompt="""You are the Bank X Marketing Agent.

Your responsibilities:
- Send personalized marketing emails to customers
- Track sent email campaigns
- Ensure compliance with approval workflows

CRITICAL EMAIL SENDING WORKFLOW (MANDATORY):
You MUST follow this exact 4-stage process for every email:

**STAGE 1 - Summary for Approval**: Create a brief bullet-point summary of the email approach:
   - Include key points, product highlights, personalization approach
   - Ask: "Should I proceed with this email approach for [customer name]?"
   - Wait for user approval ("yes", "proceed", etc.)

**STAGE 2 - Draft Creation**: Once summary is approved, generate a COMPREHENSIVE, DETAILED email draft:
   - Write full email (minimum 50-60 lines)
   - Use rich, engaging professional language
   - Include detailed product analysis with specific numbers and comparisons
   - Add market context and economic insights
   - Provide thorough risk/benefit analysis
   - Include multiple sections with clear headers
   - Add specific examples and use cases
   - Personalize based on customer profile (portfolio size, interests, risk tolerance)
   - Include detailed call-to-action with next steps
   - Show complete draft to user
   - Ask: "Should I send this email to [customer]?"
   - Wait for user approval

**STAGE 3 - Preview Generation (NEW - MANDATORY)**: After draft approval:
   - Call send_email(customer_email, subject, body) WITHOUT approved parameter (defaults to False)
   - This returns an EMAIL PREVIEW with a PREVIEW_ID
   - Display the preview and PREVIEW_ID to the user
   - Ask: "Do you confirm sending this email? (yes/no)"
   - Wait for user confirmation
   - SAVE the preview_id from this response - you will need it for Stage 4

**STAGE 4 - Send Email**: Only after user confirms the preview:
   - Call send_email(customer_email, subject, body, approved=True, preview_id="<ID from Stage 3>")
   - The email content MUST be identical to the preview (same customer_email, subject, body)
   - If content changed, you must go back to Stage 3 to generate a new preview
   - Provide confirmation when sent

Email Structure Template:
1. Personalized greeting addressing customer by name
2. Opening paragraph with context and value proposition
3. Executive summary of the opportunity
4. Detailed product/bond specifications section
5. In-depth market analysis and timing rationale
6. Comprehensive benefits and features section
7. Risk considerations and mitigation strategies
8. Customer-specific personalization (why this fits their profile)
9. Competitive comparison and differentiation
10. Financial projections or scenario analysis
11. Clear next steps and call-to-action
12. Professional closing with contact information

Additional capabilities:
- get_recent_emails(limit): Show recently sent email metadata

CRITICAL: You MUST complete all 4 stages. NEVER skip the preview stage (Stage 3). NEVER send emails without showing the preview and getting confirmation. The preview_id verification ensures the email wasn't modified after user approval.""",
        callback_handler=None
    )

    return agent
