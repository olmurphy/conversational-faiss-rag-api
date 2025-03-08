import time
import uuid
from typing import Any, Dict

import faiss
import numpy as np
from application.assistance.chains.assistant_chain import AssistantChain
from application.assistance.chains.assistant_prompt import \
    AssistantPromptBuilder
from application.assistance.helper import load_documents
from context import AppContext
from infrastracture.embeddings_manager.embeddings_manager import \
    EmbeddingsManager
from infrastracture.llm_manager.llm_manager import LlmManager
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage


class AssistantService:

    _chain: AssistantChain = None

    def __init__(
        self,
        app_context: AppContext,
    ) -> None:
        """
        Initialize the Assistant Service
        """
        self.app_context = app_context
        self._setup_assistant()

    def _init_embeddings(self):
        return EmbeddingsManager(self.app_context).get_embeddings_instance()

    def _init_llm(self):
        return LlmManager(self.app_context).get_llm_instance

    def _setup_assistant(self):
        # Load the embeddings model
        embeddings = self._init_embeddings()

        # Load the LLM
        llm = self._init_llm()
        
        faiss = self._setup_faiss(embeddings)

        self._chain = AssistantChain(
            app_context=self.app_context,
            faiss=faiss,
            llm=llm,
        )

    def _setup_faiss(self, embedding_instance):
        """
        Sets up a FAISS (Facebook AI Similarity Search) index for document retrieval.
        This method loads documents, generates embeddings, normalizes them, and builds a FAISS index.
        """
        start_time = time.perf_counter()
        documents = load_documents(self.app_context.env_vars.SAMPLE_DATA_PATH)
        load_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        embeddings = embedding_instance.embed_documents(
            [doc.page_content for doc in documents]
        )
        embedding_time = time.perf_counter() - start_time
        embeddings_np = np.array(embeddings).astype("float32")
        faiss.normalize_L2(embeddings_np)
        index = faiss.IndexFlatIP(
            embeddings_np.shape[1]
        )  # Inner product (cosine similarity)
        index.add(embeddings_np)

        uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
        index_to_docstore_id = {i: doc_id for i, doc_id in enumerate(uuids)}
        faiss_db = FAISS(
            embedding_function=embedding_instance,
            index=index,
            docstore=InMemoryDocstore({doc_id: doc for doc_id, doc in zip(uuids, documents)}),
            index_to_docstore_id=index_to_docstore_id,
        )

        self.app_context.logger.debug({
            "message": "FAISS setup completed",
            "data": {
                "load_time": load_time,
                "embedding_time": embedding_time,
                "document_count": len(documents),
            },
            "event": "FAISS_SETUP",
        })

        return faiss_db

    def chat_completion(
        self,
        query: str,
        chat_history: Dict[str, Any] = None,
    ):
        """
        Chat completion using Assistant Chain
        """
        request_id = str(uuid.uuid4())
        self.app_context.logger.info(
            {
                "message": "Rag generation starting",
                "data": query,
                "request_payload_size": query,
                "event": "REQUEST_RECEIVED",
                "request_id": request_id,
            }
        )

        chat_history.append(HumanMessage(content=query))

        rag_start: float = time.perf_counter()
        response, retrieved_docs = self._chain._invoke(query=query, chat_history_messages=[msg for msg in chat_history])
        rag_time: float = time.perf_counter() - rag_start #calculate the total rag time.
        
        chat_history.append(AIMessage(content=response.content))


        self.app_context.logger.info(
            {
                "message": "Rag model finished response",
                "data": response.content,
                "response_payload_size": response.content,
                "event": "RESPONSE_RECEIVED",
                "token_usage": response.response_metadata.get("token_usage", {}),
                "model_name": response.response_metadata.get("model_name", "unknown"),
                "finish_reason": response.response_metadata.get("finish_reason", "unknown"),
                "usage_metadata": response.usage_metadata,
                "rag_time": rag_time, #log the total rag time.
                "request_id": request_id,
            }
        )

        return response, retrieved_docs