from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Name of the event (e.g. "Football Match: Team A vs Team B")
    sport_type = Column(String, nullable=False)  # Sport discipline (e.g. "football", "basketball", "tennis")
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)  # When the event starts
    is_active = Column(Boolean, default=True)  # Whether betting is still allowed
    is_finished = Column(Boolean, default=False)  # Whether the event has finished
    result = Column(String)  # Result of the event (e.g. "team_a_won", "team_b_won", "draw")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', sport_type='{self.sport_type}', is_active={self.is_active})>"