import re
from typing import Dict, List, Tuple

# Patterns for collecting IDs in metadata (but not replacing them)
_PREVIEW_PATTERN = re.compile(r"(?i)preview[_\s-]?id[: ]+([A-Za-z0-9_\-]+)")
_CUSTOMER_PATTERN = re.compile(r"\bCUST-\d+\b")
_REQUEST_PATTERN = re.compile(r"(?i)request[_\s-]?id[: ]+([A-Za-z0-9\-]+)")


def sanitize_text_and_collect_metadata(text: str) -> Tuple[str, Dict[str, List[str]]]:
    """Collect IDs in metadata without replacing them in the text.

    Returns original text plus metadata dict containing any extracted IDs.
    Per user preference, IDs are left visible in text.
    """
    metadata: Dict[str, List[str]] = {
        "previewIds": [],
        "customerIds": [],
        "requestIds": [],
    }

    # Collect preview IDs
    for match in _PREVIEW_PATTERN.finditer(text):
        value = match.group(1)
        if value and value not in metadata["previewIds"]:
            metadata["previewIds"].append(value)

    # Collect customer IDs
    for match in _CUSTOMER_PATTERN.finditer(text):
        value = match.group(0)
        if value and value not in metadata["customerIds"]:
            metadata["customerIds"].append(value)

    # Collect request IDs
    for match in _REQUEST_PATTERN.finditer(text):
        value = match.group(1)
        if value and value not in metadata["requestIds"]:
            metadata["requestIds"].append(value)

    # Return original text unchanged - IDs are visible per user preference
    return text, metadata
