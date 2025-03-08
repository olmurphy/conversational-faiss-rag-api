from typing import List, Tuple

from langchain.schema import Document


def format_sources(retrieved_docs: List[Tuple[Document, int]]):
    """Filters and formats sources based on a relevancy threshold.

    This function processes retrieved documents, filters out those with a 
    relevance score above the given threshold, and formats them into a structured 
    dictionary.

    Args:
        retrieved_docs: A list of tuples, where each tuple contains a `Document` 
                        object and its corresponding relevance score (distance).
        threshold: A float representing the maximum allowed relevance score.

    Returns:
        A list of dictionaries, where each dictionary contains:
            - "title": The source title (default: "Unknown Title").
            - "url": The source URL (default: "Unknown URL").
            - "type": The source type (default: "Unknown Type").
            - "relevance_score": The document's relevance score as a string.
    """

    sources = []

    for doc, distance in retrieved_docs:
        source = {
            "title": doc.metadata.get(
                "Name", "Unknown Title"
            ),  # Use .get() to handle missing keys
            "url": doc.metadata.get("Link", "Unknown URL"),  # Provide default values
            "type": doc.metadata.get("Type", "Unknown Type"),
            "relevance_score": str(distance),
        }

        sources.append(source)
    return sources
