import enum

from models.base import Base, TimestampMixin

from sqlalchemy import (UUID, Column, DateTime, Float, Index, Integer, String,
                        func, text)
from sqlalchemy.dialects.postgresql import ENUM

class InteractionResultType(enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    edited = "edited"
    unspecified = "unspecified"


class UserInteraction(Base, TimestampMixin):
    __tablename__ = "user_interactions"

    interaction_id = Column(
        UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
    )
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_query = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    llm_response = Column(String)
    edited_response = Column(String)
    interaction_result = Column(
        ENUM(InteractionResultType, name="interaction_result_type", create_type=False),
        nullable=False,
        server_default=text("'unspecified'"),
    )
    feedback_reason = Column(String)
    rating = Column(Integer)
    interaction_time = Column(Float)
    clicks = Column(Integer)
    scroll_depth = Column(Float)

    __table_args__ = (Index("idx_user_interactions_session_id", "session_id"),)
