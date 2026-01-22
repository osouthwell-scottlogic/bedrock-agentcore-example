"""Multi-agent Bank X Financial Assistant - Production Version"""
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agents import create_customer_agent, create_product_agent, create_marketing_agent, create_suggestion_agent, create_recommendation_agent
from agent_router import create_agent_router
from suggestion_handler import is_suggestion_prompt, clean_suggestion_response
from utils.id_sanitizer import sanitize_text_and_collect_metadata

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Initialize specialized agents
customer_agent = create_customer_agent()
product_agent = create_product_agent()
marketing_agent = create_marketing_agent()
suggestion_agent = create_suggestion_agent()
recommendation_agent = create_recommendation_agent()

# Create the agent router that orchestrates the specialized agents
agent_router = create_agent_router(customer_agent, product_agent, marketing_agent, suggestion_agent, recommendation_agent)


def extract_text_response(response):
    """Safely extract text from agent response, handling various response formats."""
    try:
        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            if 'message' in response:
                content = response['message'].get('content', [])
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get('text', str(response))
            if 'text' in response:
                return response['text']
            if 'response' in response:
                return response['response']

        return str(response)
    except Exception:
        return str(response)



@app.entrypoint
async def agent_invocation(payload):
    """
    Invoke the multi-agent system with a payload

    IMPORTANT: Payload structure varies depending on invocation method:
    - Direct invocation (Python SDK, Console, agentcore CLI): {"prompt": "...", "conversationHistory": [...]}
    - AWS SDK invocation (JS/Java/etc via InvokeAgentRuntimeCommand): {"input": {"prompt": "...", "conversationHistory": [...]}}

    The AWS SDK automatically wraps payloads in an "input" field as part of the API contract.
    This function handles both formats for maximum compatibility.
    """
    # Handle both dict and string payloads
    if isinstance(payload, str):
        payload = json.loads(payload)

    # Extract the prompt and conversation history from the payload
    # Try AWS SDK format first (most common for production): {"input": {"prompt": "...", "conversationHistory": [...]}}
    # Fall back to direct format: {"prompt": "...", "conversationHistory": [...]}
    user_input = None
    conversation_history = []
    
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
            conversation_history = payload["input"].get("conversationHistory", [])
        else:
            user_input = payload.get("prompt")
            conversation_history = payload.get("conversationHistory", [])

    if not user_input:
        raise ValueError(f"No prompt found in payload. Expected {{'prompt': '...'}} or {{'input': {{'prompt': '...'}}}}. Received: {payload}")

    # Build context string from conversation history
    context_str = ""
    if conversation_history:
        context_lines = []
        for msg in conversation_history:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            context_lines.append(f"{role}: {content}")
        context_str = "Previous conversation:\n" + "\n".join(context_lines) + "\n\n"

    # Prepend conversation context to the user input for the agent
    enriched_input = context_str + user_input if context_str else user_input

    # Short-circuit suggestion prompts to the suggestion agent instead of the router
    if is_suggestion_prompt(user_input):
        response = suggestion_agent(enriched_input)
        text = extract_text_response(response)
        cleaned = clean_suggestion_response(text)
        sanitized_text, _ = sanitize_text_and_collect_metadata(cleaned)
        yield sanitized_text
        return

    # Stream response from the agent router (coordinator)
    stream = agent_router.stream_async(enriched_input)
    collected_metadata = {"previewIds": [], "customerIds": [], "requestIds": []}

    async for event in stream:
        if (event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text')):
            text = event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text')
            sanitized_text, meta = sanitize_text_and_collect_metadata(text)

            # Merge metadata incrementally without duplicating values
            for key in collected_metadata:
                for value in meta.get(key, []):
                    if value not in collected_metadata[key]:
                        collected_metadata[key].append(value)

            print(sanitized_text)
            yield sanitized_text


if __name__ == "__main__":
    app.run()

