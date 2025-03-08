import time
import uuid
from typing import Any

import tiktoken
from application.assistance.chains.aggregate_docs_chain import AggregateDocsChain
from application.assistance.chains.assistant_prompt import AssistantPromptBuilder
from context import AppContext
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from application.assistance.chains.process_history import ChatHistoryProcessor


class AssistantChain:
    faiss_retriever = None
    llm: Any
    prompt_template = None

    def __init__(self, app_context: AppContext, faiss: FAISS, llm):
        self.app_context = app_context
        self.faiss_retriever = faiss
        self.llm = llm

    def _build_default_prompt(self, context) -> PromptTemplate:
        return AssistantPromptBuilder().build(context)

    def _create_chain(self, context):
        if not self.prompt_template:
            self.prompt_template = self._build_default_prompt(context)

        return self.prompt_template | self.llm

    def _invoke(self, query, chat_history_messages):
        """
        Invokes the chain with error handling.

        Args:
            query: The user's query.
            chat_history_messages: The chat history.

        Returns:
            A tuple containing the response and retrieved documents.
        """
        request_id = str(uuid.uuid4())  # create a request id.

        try:
            start_time = time.perf_counter()
            retrieved_docs = self.faiss_retriever.similarity_search_with_score(
                query,
                k=self.app_context.configurations.vectorStore.maxDocumentsToRetrieve,
            )
            retrieval_time = time.perf_counter() - start_time
        except Exception as e:
            self.app_context.logger.error(
                {
                    "message": "Error during document retrieval",
                    "error": str(e),
                    "request_id": request_id,
                    "event": "DOCUMENT_RETRIEVAL_ERROR",
                }
            )
            return (
                "Error retrieving documents.",
                [],
            )  # Return error message and empty list

        retrieved_docs = [
            (doc, score)
            for doc, score in retrieved_docs
            if score > self.app_context.configurations.vectorStore.minScoreDistance
        ]

        context, context_metadata, combine_docs_time = (
            AggregateDocsChain(self.app_context).combine_docs(retrieved_docs)
        )

        chain = self._create_chain(context)

        (
            processed_chat_history,
            process_chat_history_time,
            processed_chat_token_count,
            limit_exceeded
        ) = ChatHistoryProcessor(self.app_context)._process_chat_history(
            chat_history=chat_history_messages
        )

        try:
            start_time = time.perf_counter()
            response = chain.invoke(processed_chat_history)
            invoke_time = time.perf_counter() - start_time
        except Exception as e:
            self.app_context.logger.error(
                {
                    "message": "Error invoking chain",
                    "error": str(e),
                    "request_id": request_id,
                    "event": "CHAIN_INVOCATION_ERROR",
                    "data": {
                        "context": f"Context provided: {context[:25]}",
                        "chat_history": f"Chat history used:\n{processed_chat_history}",
                    },
                }
            )
            return {
                "content": "Error Invoking the chain"
            }, retrieved_docs  # Return the retrieved docs even if the chain fails.

        self.app_context.logger.debug(
            {
                "message": "Chain Invocation Successfull",
                "data": {
                    "context": f"Context provided: {context[:25]}...",
                    "chat_history": f"Last three messages:\n\n{processed_chat_history}",
                    "metrics": {
                        "retrieval_time": retrieval_time,
                        "combine_docs_time": combine_docs_time,
                        "invoke_time": invoke_time,
                        "process_chat_time": process_chat_history_time,
                    },
                    "documents_metadata": {
                        "retrieved_docs_count": len(retrieved_docs),
                        **context_metadata,
                    },
                    "chat_history_metadata": {
                        "token_count": processed_chat_token_count,
                        "limit_exceeded": limit_exceeded
                    },
                    "request_id": request_id,
                },
                "event": "REQUEST_PROCESSING",
            }
        )
        return response, retrieved_docs
