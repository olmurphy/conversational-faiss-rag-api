import time
import numpy as np
from typing import Any
from application.assistance.chains.aggregate_docs_chain import AggregateDocsChain
from application.assistance.chains.assistant_prompt import AssistantPromptBuilder
from application.assistance.helper import load_documents
from context import AppContext
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from application.assistance.chains.process_history import ChatHistoryProcessor

class AssistantChain:
    faiss_retriever = None
    llm: Any
    prompt_template = None
    

    def __init__(self, app_context: AppContext, faiss: FAISS, llm, model,  embeddings):
        self.app_context = app_context
        self.faiss_retriever = faiss
        self.llm = llm
        self.model = model
        self.embeddings = embeddings
        self.response = dict()

    def _build_default_prompt(self, context, query) -> PromptTemplate:
        return AssistantPromptBuilder().build(context, query)

    def _create_chain(self, context, query):
        if not self.prompt_template:
            self.prompt_template = self._build_default_prompt(context, query)
            
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

        try:
            start_time = time.perf_counter()
            
            query_embed = self.model.encode(query)
            query_embed = np.expand_dims(query_embed, axis=0)
            score, doc = self.faiss_retriever.search(
                query_embed,
                self.app_context.configurations.vectorStore.maxDocumentsToRetrieve
            )

            
            
        except Exception as e:
            self.app_context.logger.error(
                {
                    "message": "Error during document retrieval",
                    "error": str(e),
                    "event": "DOCUMENT_RETRIEVAL_ERROR",
                }
            )
            return (
                "Error retrieving documents.",
                [],
            )  # Return error message and empty list
        

        retrieval_scores_norm = score[0] / np.sum(score[0])
        retrieval_scores_sorted = np.sort(retrieval_scores_norm)[::-1]
        cdf = np.cumsum(retrieval_scores_sorted)
        retrieval_scores_sorted = np.sort(score[0])[::-1]
        cutoff = self.app_context.configurations.vectorStore.cutOffDistance
        index = np.where(cdf <= cutoff)[0][-1] if np.any(cdf <= cutoff) else None
        retrieval_scores_norm = score[0] / np.sum(score[0])
        retrieval_scores_sorted = np.sort(retrieval_scores_norm)[::-1]
        cdf = np.cumsum(retrieval_scores_sorted)
        cutoff = self.app_context.configurations.vectorStore.cutOffDistance
        documents = load_documents(self.app_context.env_vars.SAMPLE_DATA_PATH)
        index = np.where(cdf <= cutoff)[0][-1] if np.any(cdf <= cutoff) else None
        selected_doc_indexes = doc[0][:index+1]
        selected_docs = [documents[i] for i in selected_doc_indexes]
        selected_scores = score[0][:index+1]
        retrieval_time = time.perf_counter() - start_time
        retrieved_docs = []
        if np.max(score[0]) >= self.app_context.configurations.vectorStore.minScoreDistance:
            retrieved_docs = [(selected_docs[i], selected_scores[i]) for i in range(index)]
        context, context_metadata, combine_docs_time = (
            AggregateDocsChain(self.app_context).combine_docs(retrieved_docs)
        )
        
        chain = self._create_chain(context, query)

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
            self.response = chain.invoke(processed_chat_history)
            invoke_time = time.perf_counter() - start_time
        except Exception as e:
            self.app_context.logger.error(
                {
                    "message": "Error invoking chain",
                    "error": str(e),
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
                },
                "event": "REQUEST_PROCESSING",
            }
        )
        return self.response, retrieved_docs, invoke_time, retrieval_time
