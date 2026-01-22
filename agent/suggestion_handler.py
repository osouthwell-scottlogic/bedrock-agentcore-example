"""Suggestion prompt handler - bypasses multi-agent router for suggestion meta-prompts"""
import re
from utils.id_sanitizer import sanitize_text_and_collect_metadata


def is_suggestion_prompt(prompt: str) -> bool:
    """
    Detect if a prompt is a meta-prompt asking for suggestions.
    
    These prompts should bypass the multi-agent router and go directly 
    to the coordinator without agent specialization.
    """
    suggestion_keywords = [
        'suggest',
        'suggestions',
        'prompts they might',
        'actionable prompts',
        'follow-up prompts',
        'json array',
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in suggestion_keywords)


def clean_suggestion_response(response: str) -> str:
    """Clean suggestion response to extract just the JSON array."""
    # Remove surrounding quotes if present
    cleaned = response.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1]
    
    # Replace escaped newlines
    cleaned = cleaned.replace('\\n', '\n')
    cleaned = cleaned.replace('\\t', '\t')
    
    # Remove IDs from suggestion text
    cleaned, _ = sanitize_text_and_collect_metadata(cleaned)
    
    return cleaned
