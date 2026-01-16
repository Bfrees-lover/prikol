from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount of the bet
    odds = Column(Float, nullable=False)  # Odds at the time of bet placement
    predicted_outcome = Column(String, nullable=False)  # What the user bet on (e.g. "team_a_won")
    is_won = Column(Boolean, default=None)  # None = pending, True = won, False = lost
    payout = Column(Float, default=0.0)  # Amount paid out if won
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # When the bet was resolved
    
    # Relationships
    user = relationship("User", back_populates="bets")
    event = relationship("Event", back_populates="bets")

    def __repr__(self):
        return f"<Bet(id={self.id}, user_id={self.user_id}, event_id={self.event_id}, amount={self.amount}, is_won={self.is_won})>"


# Add relationships to other models
from .user import User
from .event import Event

User.bets = relationship("Bet", back_populates="user")
Event.bets = relationship("Bet", back_populates="event")