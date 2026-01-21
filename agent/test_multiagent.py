"""Test script for multi-agent system"""
import sys
sys.path.insert(0, '.')

from agents.customer_agent_local import create_customer_agent
from agents.product_agent_local import create_product_agent
from agents.marketing_agent_local import create_marketing_agent
from agents.suggestion_agent_local import create_suggestion_agent
from agents.recommendation_agent_local import create_recommendation_agent
from agent_router import create_agent_router

print("Creating specialized agents...")
customer_agent = create_customer_agent()
print("✓ Customer Agent created")

product_agent = create_product_agent()
print("✓ Product Agent created")

marketing_agent = create_marketing_agent()
print("✓ Marketing Agent created")

suggestion_agent = create_suggestion_agent()
print("✓ Suggestion Agent created")

recommendation_agent = create_recommendation_agent()
print("✓ Recommendation Agent created")

print("\nCreating agent router...")
agent_router = create_agent_router(customer_agent, product_agent, marketing_agent, suggestion_agent, recommendation_agent)
print("✓ Agent Router created")

print("\n" + "="*50)
print("Multi-Agent System Initialization: SUCCESS!")
print("="*50)
print("\nAvailable agents:")
print("  - Customer Service Agent (customer queries)")
print("  - Product Research Agent (product & market data)")
print("  - Marketing Agent (email campaigns)")
print("  - Coordinator Agent (orchestrates all agents)")
print("\nSystem is ready to handle requests!")
