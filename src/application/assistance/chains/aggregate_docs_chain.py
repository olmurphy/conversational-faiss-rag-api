import time
from typing import List, Tuple, Union

import tiktoken
from context import AppContext
from langchain_core.documents import Document


class AggregateDocsChain:
    """
    Aggregates documents into a combined text, respecting a maximum token limit.

    This class iterates through a list of documents, concatenating their
    `page_content` into a single string until the combined text reaches or
    exceeds the configured maximum token limit. It uses a specified
    tokenizer to accurately count tokens.
    """

    def __init__(self, context: AppContext):
        self.context = context
        self.aggreate_max_token_number: int = (
            self.context.configurations.llm.max_context_tokens
        )
        self.tokenizer_model_name: str = self.context.configurations.llm.tokenizer
        self.tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model(
            self.tokenizer_model_name
        )

    def combine_docs(self, docs: List[Tuple[Document, float]]) -> Tuple[Union[str, dict]]:
        """
        Combines a list of documents into a single text, respecting token limits.
re
        Args:
            docs: A list of tuples, where each tuple contains a Document and an integer (unused in this implementation).

        Returns:
            A tuple containing:
              - combined_text: The combined text string or "No context provided" if no documents were processed.
              - metadata: A dictionary containing metadata about the combined text.
              - combine_docs_time: The time taken to combine the documents, in seconds.
        """
        start_time = time.perf_counter()
        combined_text, token_count, limit_exceeded = (
            self._aggregate_docs_until_token_limit(docs)
        )
        combine_docs_time = time.perf_counter() - start_time
        if limit_exceeded:
            self.context.logger.warning(
                f"Combined text length exceeded {self.aggreate_max_token_number} tokens"
            )
        metadata = {
            "combined_text_size": len(combined_text),
            "token_count": token_count,
            "limit_exceeded": limit_exceeded
        }
        return combined_text, metadata, combine_docs_time

    def _aggregate_docs_until_token_limit(self, docs: List[Tuple[Document, int]]):
        """
        Aggregates documents until the token limit is reached.

        Args:
            docs: A list of tuples, where each tuple contains a Document and an integer.

        Returns:
            A tuple containing:
              - combined_text: The combined text string.
              - token_count: The total number of tokens in the combined text.
              - limit_exceeded: A boolean indicating if the token limit was exceeded.
        """
        combined_text = ""
        token_count = 0
        limit_exceeded = False
        for doc, score in docs:
            metadata_str = ", ".join(f"{key}: {value}" for key, value in doc.metadata.items())
            metadata_tokens = self.tokenizer.encode(metadata_str)
            content_tokens = self.tokenizer.encode(doc.page_content)
            new_tokens = len(metadata_tokens) + len(content_tokens)
            if token_count + new_tokens > self.aggreate_max_token_number:
                limit_exceeded = True
                break
            combined_text += f"\n\n[Metadata: {metadata_str}]\n[Content: {doc.page_content}]\n[Score: {float(score)}]"
            token_count += new_tokens

        if combined_text != "":
            return combined_text, token_count, limit_exceeded
        return "No context provided", token_count, limit_exceeded
