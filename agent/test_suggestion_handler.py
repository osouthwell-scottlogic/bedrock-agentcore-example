"""Test the suggestion handler"""
from suggestion_handler import is_suggestion_prompt

print("Testing suggestion detection:")
print("="*50)

tests = [
    ("Suggest 4 prompts", True),
    ("List all customers", False),
    ("actionable prompts", True),
    ("what is the market", False),
    ("suggest follow-up prompts", True),
    ("JSON array of suggestions", True),
    ("Email customers", False),
]

for prompt, expected in tests:
    result = is_suggestion_prompt(prompt)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{prompt}' -> {result} (expected {expected})")

print("="*50)
print("All tests completed!")
