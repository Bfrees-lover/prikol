from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.database import AsyncSessionLocal
from ..models import User, Bet
from ..services.betting_service import betting_service

router = APIRouter(prefix="/user")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/profile")
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user profile information"""
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "balance": user.balance,
        "total_deposited": user.total_deposited,
        "is_active": user.is_active,
        "created_at": user.created_at
    }


@router.get("/bets")
async def get_user_bets(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all bets placed by a specific user"""
    result = await db.execute(
        select(Bet).filter(Bet.user_id == user_id)
    )
    bets = result.scalars().all()
    
    bet_list = []
    for bet in bets:
        bet_list.append({
            "id": bet.id,
            "event_id": bet.event_id,
            "amount": bet.amount,
            "odds": bet.odds,
            "predicted_outcome": bet.predicted_outcome,
            "is_won": bet.is_won,
            "payout": bet.payout,
            "placed_at": bet.placed_at,
            "resolved_at": bet.resolved_at
        })
    
    return {"bets": bet_list}


@router.get("/balance")
async def get_user_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user balance"""
    result = await db.execute(
        select(User.balance).filter(User.id == user_id)
    )
    balance = result.scalar_one_or_none()
    
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"balance": balance}


@router.post("/deposit")
async def deposit_funds(user_id: int, amount: float, db: AsyncSession = Depends(get_db)):
    """Deposit funds to user account"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.balance += amount
    user.total_deposited += amount
    
    await db.commit()
    
    return {"message": "Deposit successful", "new_balance": user.balance}


@router.post("/withdraw")
async def withdraw_funds(user_id: int, amount: float):
    """Withdraw funds from user account with temporary lock"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Check user lock status
    is_locked = await betting_service.get_user_lock_status(user_id)
    if is_locked:
        raise HTTPException(status_code=423, detail="Account temporarily locked due to recent withdrawal")
    
    # This would normally check if the user has sufficient balance
    # For this example, we'll just trigger the lock mechanism
    result = await betting_service.withdraw_money(user_id, amount)
    
    return result