import asyncio
import time
import uuid

import faiss
import numpy as np
from application.assistance.chains.assistant_chain import AssistantChain
from application.assistance.helper import load_documents
from application.user_session.user_session import UserSession
from context import AppContext
from infrastructure.embeddings_manager.embeddings_manager import EmbeddingsManager
from infrastructure.llm_manager.llm_manager import LlmManager
from langchain_core.messages import AIMessage, HumanMessage


class AssistantService:

    _chain: AssistantChain = None

    def __init__(self, app_context: AppContext) -> None:
        """
        Initialize the Assistant Service
        """
        self.app_context = app_context
        self.user_session = UserSession(
            redis_session=app_context.redis_session,
            postgres_session=app_context.postgres_session,
            logger=app_context.logger,
        )
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

        faiss_db, embeddings_vector = self._setup_faiss(embeddings)

        self._chain = AssistantChain(
            app_context=self.app_context,
            faiss=faiss_db,
            llm=llm,
            model=embeddings,
            embeddings=embeddings_vector,
        )

    def _setup_faiss(self, embedding_instance):
        """
        Sets up a FAISS (Facebook AI Similarity Search) index for document retrieval.
        This method loads documents, generates embeddings, normalizes them, and builds a FAISS index.
        """

        start_time = time.perf_counter()
        documents = load_documents(self.app_context.env_vars.SAMPLE_DATA_PATH)
        documents = [str(d) for d in documents]
        load_time = time.perf_counter() - start_time

        embedding_size = self.app_context.configurations.embeddings.size
        index = faiss.IndexIDMap(faiss.IndexFlatIP(embedding_size))
        index.nprobe = self.app_context.configurations.embeddings.nprobe
        start_time = time.perf_counter()
        embeddings = []

        for d in documents:
            embed = embedding_instance.encode(d)
            embeddings.append(embed)

        embeddings = np.array(embeddings)
        index.train(embeddings)
        embedding_time = time.perf_counter() - start_time
        uuids = [id for id in range(len(documents))]
        index.add_with_ids(embeddings, uuids)
        self.app_context.logger.debug(
            {
                "message": "FAISS setup completed",
                "data": {
                    "load_time": load_time,
                    "embedding_time": embedding_time,
                    "document_count": len(documents),
                },
                "event": "FAISS_SETUP",
            }
        )
        return index, embeddings

    async def chat_completion(
        self,
        query: str,
        session_id: str,
    ):
        """
        Chat completion using Assistant Chain, with metrics logging to DB
        """
        chat_history = await self.user_session.get_chat_history(uuid.UUID(session_id))

        self.app_context.logger.info(
            {
                "message": "Rag generation starting",
                "data": query,
                "request_payload_size": query,
                "event": "REQUEST_RECEIVED",
            }
        )

        chat_history.append(HumanMessage(content=query))

        rag_start: float = time.perf_counter()
        response, retrieved_docs, invoke_time, retrieval_time = self._chain._invoke(
            query=query, chat_history_messages=[msg for msg in chat_history]
        )
        rag_time: float = time.perf_counter() - rag_start

        chat_history.append(AIMessage(content=response.content))
        interaction_id = await self.user_session.store_chat_message(
            uuid.UUID(session_id), chat_history[-2:], invoke_time
        )

        # Log the metrics for the retrieval process
        retrieved_document_ids = []
        retrieved_docs_count = len(retrieved_docs)
        similarity_scores = []
        document_sources = []
        document_lengths = []

        for doc, score in retrieved_docs:
            retrieved_document_ids.append(doc.id if doc.id is not None else None)
            similarity_scores.append(score)
            document_sources.append(doc.metadata.get("Name", "Unknown Title"))
            document_lengths.append(len(doc.page_content))

        asyncio.create_task(  # Rag retrieval metrics
            self.app_context.postgres_session.record_rag_retrieval_metrics(
                rag_time,
                retrieved_document_ids,
                retrieved_docs_count,
                similarity_scores,
                retrieval_time,
                document_sources,
                document_lengths,
                interaction_id,
            )
        )

        self.app_context.logger.info(
            {
                "message": "Rag model finished response",
                "data": response.content,
                "response_payload_size": response.content,
                "event": "RESPONSE_RECEIVED",
                "token_usage": response.response_metadata.get("token_usage", {}),
                "model_name": response.response_metadata.get("model_name", "unknown"),
                "finish_reason": response.response_metadata.get(
                    "finish_reason", "unknown"
                ),
                "usage_metadata": response.usage_metadata,
                "rag_time": rag_time,  # log the total rag time.
            }
        )

        return response, retrieved_docs, interaction_id
