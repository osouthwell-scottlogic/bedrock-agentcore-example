"""Multi-agent system for Bank X Financial Assistant"""
from .customer_agent import create_customer_agent
from .product_agent import create_product_agent
from .marketing_agent import create_marketing_agent
from .suggestion_agent import create_suggestion_agent
from .recommendation_agent import create_recommendation_agent

__all__ = ['create_customer_agent', 'create_product_agent', 'create_marketing_agent', 'create_suggestion_agent', 'create_recommendation_agent']
