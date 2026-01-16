from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key for JWT tokens (in production, this should be stored securely)
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthService:
    def __init__(self):
        pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a plain password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, session: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        result = await session.execute(select(User).filter(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def get_current_user_role(self, token: str) -> Optional[str]:
        """Extract user role from token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_role: str = payload.get("role")
            if username is None or user_role is None:
                return None
            return user_role
        except JWTError:
            return None

    def create_user(self, username: str, email: str, password: str, role: str = "user") -> User:
        """Create a new user object with hashed password"""
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            balance=100.0  # Start with $100 balance for new users
        )
        return user