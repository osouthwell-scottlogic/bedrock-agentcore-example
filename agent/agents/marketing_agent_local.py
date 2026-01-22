"""Marketing Agent - Local Version"""
from strands import Agent, tool
import json
import os
import hashlib
from datetime import datetime
from strands.models import BedrockModel

# Local data directory for development
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'local_data')
SENT_EMAILS_DIR = os.path.join(LOCAL_DATA_DIR, 'sent_emails')

# Ensure sent_emails directory exists
os.makedirs(SENT_EMAILS_DIR, exist_ok=True)


def generate_preview_id(customer_email: str, subject: str, body: str) -> str:
    """Generate a unique preview ID based on email content"""
    content = f"{customer_email}|{subject}|{body}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


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
    # PREVIEW MODE: Generate and return preview
    if not approved:
        generated_preview_id = generate_preview_id(customer_email, subject, body)
        # Do not surface preview IDs in user-visible text; keep them only in metadata/backend state
        return f"""EMAIL PREVIEW GENERATED

To: {customer_email}
Subject: {subject}

--- EMAIL BODY START ---

{body}

--- EMAIL BODY END ---

Preview ID available in system metadata. Confirm sending? Reply yes/no."""
    
    # SEND MODE: Verify preview_id matches
    expected_preview_id = generate_preview_id(customer_email, subject, body)
    if preview_id != expected_preview_id:
        return f"Error: Preview ID mismatch. Email content may have changed after preview. Please generate a new preview."
    
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


def create_marketing_agent():
    """Create and return the Marketing Agent (Local)"""
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
You MUST follow this exact 3-stage process for every email. Skip the summary step and start with the full draft when the user asks to create an email.

**STAGE 1 - Draft Creation**: Immediately generate a COMPREHENSIVE, DETAILED email draft when asked to create an email:
    - Write full email (minimum 20 lines, maximum 50 lines)
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

**STAGE 2 - Preview Generation (MANDATORY)**: After draft approval:
    - Call send_email(customer_email, subject, body) WITHOUT approved parameter (defaults to False)
    - This returns an EMAIL PREVIEW with a PREVIEW_ID
    - Do NOT rewrite or restate the full draft. Show a concise confirmation that uses the existing draft: include recipient, subject, preview_id, and note that the body is unchanged from the draft. Only re-display the full body if the user explicitly asks to see it again.
    - Ask: "Do you confirm sending this email? (yes/no)"
    - Wait for user confirmation
    - SAVE the preview_id from this response - you will need it for Stage 3

**STAGE 3 - Send Email**: Only after user confirms the preview:
    - Call send_email(customer_email, subject, body, approved=True, preview_id="<ID from Stage 2>")
   - The email content MUST be identical to the preview (same customer_email, subject, body)
   - If content changed, you must go back to Stage 3 to generate a new preview
   - Provide confirmation when sent

Stage Advancement Rules (prevent re-drafting loops):
- After showing the draft, if the user says any approval intent ("yes", "send", "approve", "go ahead", "continue", "looks good"), DO NOT write another draft. Immediately proceed to Stage 2 by calling send_email(customer_email, subject, body) with approved=False to generate the preview.
- Only create a new draft if the user explicitly asks for changes or revisions (keywords like "edit", "change", "revise", "rewrite").
- When showing the preview, surface the preview_id and ask for confirmation. If the user confirms ("yes", "send", "approve"), call send_email with approved=True and the SAME subject/body plus the preview_id. Do not regenerate the draft or preview unless the content changed.

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

CRITICAL: You MUST complete all 3 stages. NEVER skip the preview stage (Stage 2). NEVER send emails without showing the preview and getting confirmation. The preview_id verification ensures the email wasn't modified after user approval.""",
        callback_handler=None
    )

    return agent
