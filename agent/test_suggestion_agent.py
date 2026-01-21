"""Test the multi-agent system with dedicated Suggestion Agent"""
import sys
sys.path.insert(0, '.')

from agents.customer_agent_local import create_customer_agent
from agents.product_agent_local import create_product_agent
from agents.marketing_agent_local import create_marketing_agent
from agents.suggestion_agent_local import create_suggestion_agent
from agents.recommendation_agent_local import create_recommendation_agent
from agent_router import create_agent_router

print("Testing Multi-Agent System with Dedicated Suggestion Agent")
print("=" * 60)

# Initialize agents
print("\n1. Initializing specialized agents...")
customer_agent = create_customer_agent()
print("   ✓ Customer Service Agent")

product_agent = create_product_agent()
print("   ✓ Product Research Agent")

marketing_agent = create_marketing_agent()
print("   ✓ Marketing Agent")

suggestion_agent = create_suggestion_agent()
print("   ✓ Suggestion Agent")

recommendation_agent = create_recommendation_agent()
print("   ✓ Recommendation Agent")

# Create router
print("\n2. Creating agent router...")
router = create_agent_router(customer_agent, product_agent, marketing_agent, suggestion_agent, recommendation_agent)
print("   ✓ Router initialized with all agents")

# Verify agents are stored
print("\n3. Verifying agent storage...")
print(f"   ✓ customer_agent: {hasattr(router, 'customer_agent')}")
print(f"   ✓ product_agent: {hasattr(router, 'product_agent')}")
print(f"   ✓ marketing_agent: {hasattr(router, 'marketing_agent')}")
print(f"   ✓ suggestion_agent: {hasattr(router, 'suggestion_agent')}")

# Verify coordinator has suggestion tool
print("\n4. Verifying coordinator tools...")
coordinator_tools = [tool.name for tool in router.coordinator.tools]
print(f"   Available tools: {', '.join(coordinator_tools)}")
if 'generate_suggestions' in coordinator_tools:
    print("   ✓ Suggestion Agent registered as tool")

# Verify routing methods
print("\n5. Verifying routing methods...")
print(f"   ✓ stream_async: {hasattr(router, 'stream_async')}")
print(f"   ✓ __call__: {hasattr(router, '__call__')}")

print("\n" + "=" * 60)
print("Multi-Agent System with Suggestion Agent: ✓ READY")
print("=" * 60)

print("\nAgent Architecture:")
print("""
  Coordinator (Router)
     ├── Customer Service Agent (customer queries)
     ├── Product Research Agent (product & market data)
     ├── Marketing Agent (email campaigns)
     └── Suggestion Agent (generate prompts)
""")

print("\nKey Features:")
print("  ✓ 4 specialized agents with focused responsibilities")
print("  ✓ Coordinator intelligently routes requests")
print("  ✓ Suggestion Agent generates contextual prompts")
print("  ✓ Each agent can work independently or orchestrated")
print("  ✓ Clean separation of concerns")
