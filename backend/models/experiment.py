from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentConfig(BaseModel):
    """Configuração de um experimento evolutivo"""
    
    population_size: int = Field(ge=10, le=1000, default=50)
    generations: int = Field(ge=1, le=10000, default=100)
    mutation_rate: float = Field(ge=0.0, le=1.0, default=0.1)
    mutation_strength: float = Field(ge=0.0, le=1.0, default=0.2)
    crossover_rate: float = Field(ge=0.0, le=1.0, default=0.7)
    elitism_rate: float = Field(ge=0.0, le=0.5, default=0.1)
    tournament_size: int = Field(ge=2, le=10, default=3)
    simulations: int = Field(ge=100, le=100000, default=10000)
    convergence_threshold: float = Field(ge=0.0, le=1.0, default=0.001)
    convergence_generations: int = Field(ge=1, le=100, default=10)


class Experiment(BaseModel):
    """Representa um experimento de otimização"""
    
    id: Optional[int] = None
    name: str = Field(min_length=1, max_length=255)
    budget: float = Field(gt=0.0, description="Orçamento em reais")
    config: ExperimentConfig
    seed: Optional[int] = None
    status: ExperimentStatus = ExperimentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    best_fitness: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Experimento Teste 100 reais",
                "budget": 100.0,
                "config": {
                    "population_size": 50,
                    "generations": 100,
                    "simulations": 10000
                },
                "seed": 42
            }
        }
