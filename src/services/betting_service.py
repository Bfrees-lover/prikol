import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models import User, Event, Bet
from ..models.database import AsyncSessionLocal


class BettingService:
    def __init__(self):
        self.locked_users = {}  # Dictionary to track locked users and their unlock times
        self.total_service_deposit = 0.0  # Total money in the system
        self.bookie_margin = 0.05  # 5% bookie margin

    async def get_session(self) -> AsyncSession:
        """Get a database session"""
        async with AsyncSessionLocal() as session:
            yield session

    async def create_random_events(self, session: AsyncSession, count: int = 10):
        """Create random events for betting"""
        sports_types = ["football", "basketball", "tennis", "hockey", "volleyball"]
        teams = [
            "Team A", "Team B", "Team C", "Team D", "Team E", "Team F", 
            "Lions", "Tigers", "Bears", "Eagles", "Wolves", "Sharks",
            "Dragons", "Phoenix", "Hawks", "Falcons", "Ravens", "Owls"
        ]
        
        for i in range(count):
            sport = random.choice(sports_types)
            team1 = random.choice(teams)
            team2 = random.choice([t for t in teams if t != team1])
            
            event = Event(
                name=f"{sport.title()} Match: {team1} vs {team2}",
                sport_type=sport,
                description=f"Upcoming {sport} match between {team1} and {team2}",
                start_time=datetime.utcnow() + timedelta(hours=random.randint(1, 24)),
                is_active=True,
                is_finished=False
            )
            session.add(event)
        
        await session.commit()

    async def calculate_odds_based_on_bets(self, session: AsyncSession, event_id: int):
        """Calculate dynamic odds based on the amount of bets placed on each outcome"""
        # Get all bets for this event
        result = await session.execute(
            select(Bet).where(Bet.event_id == event_id)
        )
        bets = result.scalars().all()
        
        if not bets:
            # Default odds if no bets yet
            return {"team_a_won": 2.0, "team_b_won": 2.0, "draw": 3.0}
        
        # Count bets and amounts for each outcome
        outcome_stats = {}
        for bet in bets:
            outcome = bet.predicted_outcome
            if outcome not in outcome_stats:
                outcome_stats[outcome] = {"count": 0, "amount": 0.0}
            outcome_stats[outcome]["count"] += 1
            outcome_stats[outcome]["amount"] += bet.amount
        
        # Calculate inverse proportion odds (more bets = lower odds)
        total_amount = sum(outcome_stats[outcome]["amount"] for outcome in outcome_stats)
        
        odds = {}
        for outcome in outcome_stats:
            bet_amount = outcome_stats[outcome]["amount"]
            if bet_amount > 0:
                # Higher odds for outcomes with less money bet on them
                base_odd = total_amount / bet_amount
                # Apply bookie margin
                adjusted_odd = base_odd * (1 - self.bookie_margin)
                # Ensure minimum odd value
                odds[outcome] = max(adjusted_odd, 1.1)
            else:
                # Default odds for outcomes with no bets yet
                odds[outcome] = 2.0
        
        # Ensure we have odds for standard outcomes even if no bets yet
        if "team_a_won" not in odds:
            odds["team_a_won"] = 2.0
        if "team_b_won" not in odds:
            odds["team_b_won"] = 2.0
        if "draw" not in odds:
            odds["draw"] = 3.0
            
        return odds

    async def place_bet(self, session: AsyncSession, user_id: int, event_id: int, amount: float, predicted_outcome: str):
        """Place a bet for a user on an event"""
        # Check if user is locked
        if user_id in self.locked_users:
            unlock_time = self.locked_users[user_id]
            if datetime.utcnow() < unlock_time:
                raise Exception("User is temporarily locked due to withdrawal action")
            else:
                # Remove user from locked list if lock expired
                del self.locked_users[user_id]
        
        # Get user
        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise Exception("User not found")
        
        # Check if user has enough balance
        if user.balance < amount:
            raise Exception("Insufficient balance")
        
        # Get event
        result = await session.execute(select(Event).filter(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event or not event.is_active or event.is_finished:
            raise Exception("Event is not active for betting")
        
        # Calculate current odds for this outcome
        current_odds = await self.calculate_odds_based_on_bets(session, event_id)
        if predicted_outcome not in current_odds:
            raise Exception(f"Invalid outcome: {predicted_outcome}")
        
        # Create the bet
        bet = Bet(
            user_id=user_id,
            event_id=event_id,
            amount=amount,
            odds=current_odds[predicted_outcome],
            predicted_outcome=predicted_outcome
        )
        
        # Deduct amount from user balance
        user.balance -= amount
        user.total_deposited += amount  # Track total deposited for analytics
        
        # Update service deposit (track money in system)
        self.total_service_deposit += amount
        
        session.add(bet)
        await session.commit()
        await session.refresh(bet)
        
        return bet

    async def resolve_event(self, session: AsyncSession, event_id: int, actual_result: str):
        """Resolve an event and calculate winnings for successful bets"""
        # Get event
        result = await session.execute(select(Event).filter(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise Exception("Event not found")
        
        # Mark event as finished
        event.is_active = False
        event.is_finished = True
        event.result = actual_result
        
        # Get all bets for this event
        result = await session.execute(
            select(Bet).options(selectinload(Bet.user)).filter(Bet.event_id == event_id)
        )
        bets = result.scalars().all()
        
        # Process each bet
        for bet in bets:
            if bet.predicted_outcome == actual_result:
                # This bet won
                bet.is_won = True
                bet.payout = bet.amount * bet.odds
                
                # Add winnings to user balance
                bet.user.balance += bet.payout
                self.total_service_deposit -= bet.payout  # Update service deposit
            else:
                # This bet lost
                bet.is_won = False
                bet.payout = 0.0
            
            bet.resolved_at = datetime.utcnow()
        
        await session.commit()

    async def withdraw_money(self, user_id: int, amount: float):
        """Withdraw money from user account with temporary lock"""
        # Check if user is locked
        if user_id in self.locked_users:
            unlock_time = self.locked_users[user_id]
            if datetime.utcnow() < unlock_time:
                raise Exception("User is temporarily locked due to withdrawal action")
            else:
                # Remove user from locked list if lock expired
                del self.locked_users[user_id]
        
        # Simulate withdrawal process
        # Add user to locked list for 30 seconds
        self.locked_users[user_id] = datetime.utcnow() + timedelta(seconds=30)
        
        # In a real implementation, this would handle actual payment processing
        # For now, we just simulate the lock mechanism
        return {"status": "withdrawal_initiated", "lock_duration": 30}

    async def get_user_lock_status(self, user_id: int) -> bool:
        """Check if a user is currently locked"""
        if user_id in self.locked_users:
            unlock_time = self.locked_users[user_id]
            if datetime.utcnow() >= unlock_time:
                # Lock expired, remove user from locked list
                del self.locked_users[user_id]
                return False
            return True
        return False

    def get_admin_analytics(self) -> Dict:
        """Get admin analytics data"""
        return {
            "bookie_margin": self.bookie_margin,
            "total_service_deposit": self.total_service_deposit,
            "locked_users_count": len(self.locked_users),
            "active_events_count": 0,  # Would need DB query in real implementation
            "total_bets_placed": 0,    # Would need DB query in real implementation
            "total_payouts": 0         # Would need DB query in real implementation
        }


# Global instance of betting service
betting_service = BettingService()