"""Multi-agent Bank X Financial Assistant - Local Development Version"""
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agents.customer_agent_local import create_customer_agent
from agents.product_agent_local import create_product_agent
from agents.marketing_agent_local import create_marketing_agent
from agents.suggestion_agent_local import create_suggestion_agent
from agents.recommendation_agent_local import create_recommendation_agent
from agent_router import create_agent_router
from utils.id_sanitizer import sanitize_text_and_collect_metadata

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Initialize specialized agents (local versions)
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
            # Handle bedrock_agentcore response format
            if 'message' in response:
                content = response['message'].get('content', [])
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get('text', str(response))
            # Handle other dict formats
            if 'text' in response:
                return response['text']
            if 'response' in response:
                return response['response']
        
        return str(response)
    except Exception as e:
        return str(response)


@app.entrypoint
async def agent_invocation(payload):
    """
    Invoke the multi-agent system with a payload

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

    # Stream response from the agent router (coordinator)
    stream = agent_router.stream_async(user_input)
    collected_metadata = {"previewIds": [], "customerIds": [], "requestIds": []}

    async for event in stream:
        if (event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text')):
            text = event.get('event',{}).get('contentBlockDelta',{}).get('delta',{}).get('text')
            sanitized_text, meta = sanitize_text_and_collect_metadata(text)

            for key in collected_metadata:
                for value in meta.get(key, []):
                    if value not in collected_metadata[key]:
                        collected_metadata[key].append(value)

            print(sanitized_text)
            yield sanitized_text


if __name__ == "__main__":
    app.run()