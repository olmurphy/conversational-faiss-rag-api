import time
from typing import List, Tuple

import tiktoken
from context import AppContext
from langchain_core.messages.base import BaseMessage


class ChatHistoryProcessor:
    """Processes chat history to fit within a token limit."""

    def __init__(
        self, app_context: AppContext
    ):
        self.context = app_context
        self.chat_history_max_token_limit: int = self.context.configurations.llm.max_chat_history_tokens
        tokenizer_model_name: str = self.context.configurations.llm.tokenizer
        self.tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model(tokenizer_model_name)

    def _process_chat_history(
        self, chat_history: List[BaseMessage]
    ) -> Tuple[List[BaseMessage], float]:
        """
        Processes chat history, keeping only up to max_token_limit tokens.

        Args:
            chat_history: A list of Langchain AIMessage and HumanMessage objects.
            llm: The Langchain LLM used for token counting.
            max_token_limit: The maximum number of tokens to keep.

        Returns:
            A tuple containing:
                - A list of BaseMessage objects (AIMessage, HumanMessage) within the token limit.
                - The processing time in seconds.
        """

        start_time = time.perf_counter()
        current_token_count = 0
        included_messages: List[BaseMessage] = []
        limit_exceeded = False

        for message in reversed(
            chat_history
        ):  # work backwards to keep the most recent messages.
            included_messages.insert(0, message)
            temp_token_count = len(self.tokenizer.encode(message.content))
            if (
                current_token_count + temp_token_count
                <= self.chat_history_max_token_limit
            ):
                included_messages.insert(
                    0, message
                )  # insert at the beginning to maintain order
                current_token_count += temp_token_count
            else:
                limit_exceeded = True
                break
        process_chat_history_time = time.perf_counter() - start_time

        return included_messages, process_chat_history_time, current_token_count, limit_exceeded
