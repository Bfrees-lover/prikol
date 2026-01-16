import random
from datetime import datetime, timedelta
from typing import Dict, List
from enum import Enum


class SportType(Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    HOCKEY = "hockey"
    VOLLEYBALL = "volleyball"


def generate_random_event(sport_type: SportType = None) -> Dict:
    """Generate a random sports event"""
    if not sport_type:
        sport_type = random.choice(list(SportType))
    
    teams = [
        "Team A", "Team B", "Team C", "Team D", "Team E", "Team F", 
        "Lions", "Tigers", "Bears", "Eagles", "Wolves", "Sharks",
        "Dragons", "Phoenix", "Hawks", "Falcons", "Ravens", "Owls",
        "Giants", "Warriors", "Knights", "Raiders", "Pirates", "Vikings"
    ]
    
    team1 = random.choice(teams)
    team2 = random.choice([t for t in teams if t != team1])
    
    event_name = f"{sport_type.value.title()} Match: {team1} vs {team2}"
    
    return {
        "name": event_name,
        "sport_type": sport_type.value,
        "description": f"Upcoming {sport_type.value} match between {team1} and {team2}",
        "start_time": datetime.utcnow() + timedelta(hours=random.randint(1, 48)),
        "is_active": True,
        "is_finished": False
    }


def calculate_dynamic_odds(base_probability: float, market_bias: float = 0.0) -> float:
    """
    Calculate dynamic odds based on probability and market bias
    Args:
        base_probability: Probability of the outcome (0-1)
        market_bias: How much the market is leaning toward this outcome (-1 to 1)
    Returns:
        Adjusted odds considering market bias
    """
    if base_probability <= 0 or base_probability >= 1:
        raise ValueError("Probability must be between 0 and 1 (exclusive)")
    
    # Convert probability to fair odds
    fair_odds = 1.0 / base_probability
    
    # Apply market bias adjustment
    # Positive bias = more people betting on this outcome = lower odds
    # Negative bias = fewer people betting on this outcome = higher odds
    bias_factor = 1.0 - (market_bias * 0.2)  # 20% max adjustment for market bias
    
    adjusted_odds = fair_odds * bias_factor
    
    # Apply bookmaker margin (typically 5-10%)
    bookmaker_margin = 0.05
    final_odds = adjusted_odds * (1 - bookmaker_margin)
    
    return round(final_odds, 2)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency with proper symbols"""
    return f"{amount:.2f} {currency}"


def validate_outcome_prediction(outcome: str, valid_outcomes: List[str]) -> bool:
    """Validate if the predicted outcome is valid for the event"""
    return outcome.lower() in [o.lower() for o in valid_outcomes]


def get_sport_outcomes(sport_type: str) -> List[str]:
    """Get possible outcomes for a given sport type"""
    outcomes_map = {
        "football": ["team_a_won", "team_b_won", "draw"],
        "basketball": ["team_a_won", "team_b_won"],
        "tennis": ["player1", "player2"],
        "hockey": ["team_a_won", "team_b_won", "overtime"],
        "volleyball": ["team_a_won", "team_b_won"]
    }
    
    return outcomes_map.get(sport_type.lower(), ["team_a_won", "team_b_won", "draw"])