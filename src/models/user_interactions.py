from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, UUID, text
from models.base import Base

class UserInteraction(Base):
    __tablename__ = 'user_interactions'

    interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()"))
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_query = Column(String)
    created_at = Column(DateTime, server_default=text("TIMEZONE('utc', now())"))
    llm_response = Column(String)
    edited_response = Column(String)
    positive_feedback = Column(Boolean)
    negative_feedback = Column(Boolean)
    feedback_reason = Column(String)
    rating = Column(Integer)
    interaction_time = Column(Integer)
    clicks = Column(Integer)
    scroll_depth = Column(Float)
    number_of_turns = Column(Integer)
    chat_history = Column(JSON)