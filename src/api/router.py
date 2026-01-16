from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..models.database import AsyncSessionLocal
from ..services.auth_service import AuthService
from ..services.betting_service import betting_service

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    user_role = auth_service.get_current_user_role(token)
    
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user info from token (in a real app, you'd store user ID in the token)
    # For simplicity, we're just checking the role here
    return {"role": user_role}


# Authentication endpoints
@router.post("/register")
async def register(username: str, email: str, password: str, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = await auth_service.authenticate_user(db, username, password)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    user = auth_service.create_user(username, email, password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User created successfully", "user_id": user.id}


@router.post("/login")
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    """Login and return access token"""
    user = await auth_service.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token with user info
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }


# User endpoints
@router.get("/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user profile"""
    if current_user["role"] not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {"message": "User profile retrieved", "user_info": current_user}


@router.get("/user/balance")
async def get_user_balance(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user balance"""
    if current_user["role"] not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # In a real implementation, we would fetch the actual user balance from DB
    # For now, returning a mock value
    return {"balance": 100.0}


@router.post("/user/withdraw")
async def withdraw_money(amount: float, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Withdraw money from user account"""
    if current_user["role"] not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # We would need user_id in the token to implement this properly
    # For demo purposes, using a mock user_id
    user_id = 1  # This should come from the token
    
    try:
        result = await betting_service.withdraw_money(user_id, amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Betting endpoints
@router.get("/events")
async def get_events(db: AsyncSession = Depends(get_db)):
    """Get all active events"""
    # This would fetch events from the database
    # For now, returning mock data
    return {
        "events": [
            {"id": 1, "name": "Football Match: Team A vs Team B", "sport_type": "football", "odds": {"team_a_won": 2.1, "team_b_won": 3.2, "draw": 3.5}},
            {"id": 2, "name": "Basketball Game: Lions vs Tigers", "sport_type": "basketball", "odds": {"team_a_won": 1.9, "team_b_won": 1.85, "draw": "N/A"}},
            {"id": 3, "name": "Tennis Match: Eagles vs Wolves", "sport_type": "tennis", "odds": {"player1": 1.7, "player2": 2.1}}
        ]
    }


@router.post("/bet/place")
async def place_bet(event_id: int, amount: float, outcome: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Place a bet on an event"""
    if current_user["role"] not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # We would need user_id in the token to implement this properly
    user_id = 1  # This should come from the token
    
    try:
        # In a real implementation, we would pass the actual user_id
        bet = await betting_service.place_bet(db, user_id, event_id, amount, outcome)
        return {"message": "Bet placed successfully", "bet_id": bet.id, "odds": bet.odds}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Admin endpoints
@router.get("/admin/analytics")
async def get_admin_analytics(current_user: dict = Depends(get_current_user)):
    """Get admin analytics dashboard"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    analytics = betting_service.get_admin_analytics()
    return analytics


@router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get all users (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would fetch all users from the DB
    # For now, returning mock data
    return {
        "users": [
            {"id": 1, "username": "user1", "email": "user1@example.com", "balance": 150.0, "total_deposited": 200.0},
            {"id": 2, "username": "user2", "email": "user2@example.com", "balance": 75.5, "total_deposited": 100.0}
        ]
    }


@router.get("/admin/events")
async def get_admin_events(current_user: dict = Depends(get_current_user)):
    """Get all events for admin (with more details)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Return mock events with admin-specific details
    return {
        "events": [
            {"id": 1, "name": "Football Match: Team A vs Team B", "sport_type": "football", 
             "is_active": True, "is_finished": False, "total_bets": 15, "total_staked": 1250.0},
            {"id": 2, "name": "Basketball Game: Lions vs Tigers", "sport_type": "basketball", 
             "is_active": True, "is_finished": False, "total_bets": 8, "total_staked": 680.0}
        ]
    }