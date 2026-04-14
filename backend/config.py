from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://lotofacil_user:lotofacil_pass@localhost:5432/lotofacil"
    redis_url: str = "redis://localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    
    # Optimization
    max_workers: int = 4
    cache_ttl: int = 3600
    auto_sync_contests_on_startup: bool = True
    
    # Monte Carlo
    default_simulations: int = 10000
    random_seed: int = 42
    
    # Lotofácil Constants
    total_numbers: int = 25
    numbers_per_draw: int = 15
    min_game_size: int = 15
    max_game_size: int = 20
    
    # Prize values (approximate)
    prize_15: float = 1500000.0
    prize_14: float = 1500.0
    prize_13: float = 25.0
    prize_12: float = 10.0
    prize_11: float = 5.0
    
    # Game costs
    cost_15: float = 3.00
    cost_16: float = 48.00
    cost_17: float = 408.00
    cost_18: float = 2448.00
    cost_19: float = 11628.00
    cost_20: float = 46512.00
    
    # API Caixa
    caixa_api_base_url: str = "https://servicebus2.caixa.gov.br/portaldeloterias/api"
    caixa_api_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
