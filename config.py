from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Самарин Сережкин - Ставки на спорт"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./betting_platform.db"
    
    # Security settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Betting settings
    bookie_margin: float = 0.05  # 5% bookie margin
    min_bet_amount: float = 1.0
    max_bet_amount: float = 10000.0
    
    # Withdrawal settings
    withdrawal_lock_duration: int = 30  # 30 seconds lock after withdrawal
    min_withdrawal_amount: float = 10.0
    max_withdrawal_amount: float = 5000.0
    
    # Supported sports
    supported_sports: list = ["football", "basketball", "tennis", "hockey", "volleyball"]
    
    # Rebit Emcy broker settings (placeholder)
    rebit_emcy_api_url: str = os.getenv("REBIT_EMCY_API_URL", "https://rebit-emcy-api.example.com")
    rebit_emcy_api_key: str = os.getenv("REBIT_EMCY_API_KEY", "your-rebit-emcy-api-key")
    

settings = Settings()