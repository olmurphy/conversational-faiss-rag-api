from models.base import Base, TimestampMixin

from sqlalchemy import (ARRAY, UUID, Column, Float, ForeignKey,
                        Index, Integer, String)


class RagRetrievals(Base, TimestampMixin):
    __tablename__ = "rag_retrievals"

    retrieval_id = Column(UUID(as_uuid=True), primary_key=True)
    interaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_interactions.interaction_id"),
        nullable=False,
    )
    rag_invocation_time = Column(Float)
    retrieved_document_ids = Column(ARRAY(String))
    retrieved_document_count = Column(Integer)
    similarity_scores = Column(ARRAY(Float))
    retrieval_latency = Column(Float)
    document_sources = Column(ARRAY(String))
    document_lengths = Column(ARRAY(Integer))

    __table_args__ = (Index("idx_rag_interaction_id", "interaction_id"),)
