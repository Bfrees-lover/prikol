from fastapi import APIRouter, Depends
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta

from ..models.database import AsyncSessionLocal
from ..models import User, Event, Bet
from ..services.betting_service import betting_service

router = APIRouter(prefix="/admin")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/dashboard")
async def get_admin_dashboard(db: AsyncSession = Depends(get_db)):
    """Main admin dashboard with comprehensive analytics"""
    # Get basic stats
    user_count_result = await db.execute(sqlalchemy.select(func.count(User.id)))
    user_count = user_count_result.scalar()
    
    event_count_result = await db.execute(sqlalchemy.select(func.count(Event.id)))
    event_count = event_count_result.scalar()
    
    bet_count_result = await db.execute(sqlalchemy.select(func.count(Bet.id)))
    bet_count = bet_count_result.scalar()
    
    # Get financial stats
    total_balances_result = await db.execute(sqlalchemy.select(func.sum(User.balance)))
    total_balances = total_balances_result.scalar() or 0.0
    
    total_deposited_result = await db.execute(sqlalchemy.select(func.sum(User.total_deposited)))
    total_deposited = total_deposited_result.scalar() or 0.0
    
    # Get service analytics
    service_analytics = betting_service.get_admin_analytics()
    
    return {
        "basic_stats": {
            "total_users": user_count,
            "total_events": event_count,
            "total_bets": bet_count,
        },
        "financial_stats": {
            "total_user_balances": total_balances,
            "total_deposited_by_users": total_deposited,
        },
        "service_analytics": service_analytics
    }


@router.get("/users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """Get all users with their balances and deposit history"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "balance": user.balance,
            "total_deposited": user.total_deposited,
            "is_active": user.is_active,
            "created_at": user.created_at
        })
    
    return {"users": user_list}


@router.get("/events")
async def get_all_events(db: AsyncSession = Depends(get_db)):
    """Get all events with detailed statistics"""
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.bets))
    )
    events = result.scalars().all()
    
    event_list = []
    for event in events:
        # Calculate stats for this event
        total_bets = len(event.bets)
        total_staked = sum(bet.amount for bet in event.bets)
        
        event_list.append({
            "id": event.id,
            "name": event.name,
            "sport_type": event.sport_type,
            "is_active": event.is_active,
            "is_finished": event.is_finished,
            "result": event.result,
            "start_time": event.start_time,
            "total_bets": total_bets,
            "total_staked": total_staked,
            "created_at": event.created_at
        })
    
    return {"events": event_list}


@router.get("/bets")
async def get_all_bets(db: AsyncSession = Depends(get_db)):
    """Get all bets with details"""
    result = await db.execute(
        select(Bet)
        .options(joinedload(Bet.user), joinedload(Bet.event))
    )
    bets = result.scalars().all()
    
    bet_list = []
    for bet in bets:
        bet_list.append({
            "id": bet.id,
            "user_id": bet.user_id,
            "username": bet.user.username if bet.user else "Unknown",
            "event_id": bet.event_id,
            "event_name": bet.event.name if bet.event else "Unknown",
            "amount": bet.amount,
            "odds": bet.odds,
            "predicted_outcome": bet.predicted_outcome,
            "is_won": bet.is_won,
            "payout": bet.payout,
            "placed_at": bet.placed_at,
            "resolved_at": bet.resolved_at
        })
    
    return {"bets": bet_list}


@router.get("/analytics")
async def get_detailed_analytics(db: AsyncSession = Depends(get_db)):
    """Get detailed analytics for the admin dashboard"""
    # Service-level analytics
    service_analytics = betting_service.get_admin_analytics()
    
    # Additional DB-based analytics
    # Active users in the last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.updated_at >= yesterday)
    )
    active_users_last_24h = active_users_result.scalar()
    
    # Bets in the last 24 hours
    recent_bets_result = await db.execute(
        select(func.count(Bet.id)).where(Bet.placed_at >= yesterday)
    )
    bets_last_24h = recent_bets_result.scalar()
    
    # Revenue calculation (approximate)
    total_deposited_result = await db.execute(select(func.sum(User.total_deposited)))
    total_deposited = total_deposited_result.scalar() or 0.0
    
    total_payouts_result = await db.execute(select(func.sum(Bet.payout)))
    total_payouts = total_payouts_result.scalar() or 0.0
    
    approximate_revenue = total_deposited - total_payouts
    
    return {
        "service_analytics": service_analytics,
        "activity_analytics": {
            "active_users_last_24h": active_users_last_24h,
            "bets_last_24h": bets_last_24h,
        },
        "financial_analytics": {
            "total_deposited": total_deposited,
            "total_payouts": total_payouts,
            "approximate_revenue": approximate_revenue
        }
    }