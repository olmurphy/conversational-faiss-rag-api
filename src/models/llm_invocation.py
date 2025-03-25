import uuid

from models.base import Base, TimestampMixin
from sqlalchemy import (JSON, UUID, Boolean, Column, Float, ForeignKey, Index,
                        Integer, String)


class LLMInvocations(Base, TimestampMixin):
    __tablename__ = "llm_invocations"

    llm_invocation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_interactions.interaction_id"),
        nullable=False,
    )
    model_name = Column(String(255), nullable=False)
    confidence_score = Column(Float)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    llm_latency = Column(Float)
    llm_api_errors = Column(Integer)
    llm_temperature = Column(Float)
    llm_top_p = Column(Float)
    guardrails_triggered = Column(Boolean)
    guardrail_violations = Column(JSON)

    system_fingerprint = Column(String(255))
    finish_reason = Column(String(255))

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)

    __table_args__ = (Index("idx_llm_interaction_id", "interaction_id"),)
