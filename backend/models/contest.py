from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List


class Contest(BaseModel):
    """Representa um concurso da Lotofácil"""
    
    contest_id: int = Field(gt=0, description="Número do concurso")
    draw_date: date = Field(description="Data do sorteio")
    numbers: List[int] = Field(min_length=15, max_length=15, description="Números sorteados")
    
    @field_validator('numbers')
    @classmethod
    def validate_numbers(cls, v: List[int]) -> List[int]:
        """Valida que os números estão no range correto e são únicos"""
        if len(v) != 15:
            raise ValueError("Deve conter exatamente 15 números")
        
        if len(set(v)) != 15:
            raise ValueError("Números devem ser únicos")
        
        if not all(1 <= n <= 25 for n in v):
            raise ValueError("Números devem estar entre 1 e 25")
        
        return sorted(v)
    
    def to_set(self) -> set:
        """Retorna números como conjunto"""
        return set(self.numbers)
    
    def matches(self, game: List[int]) -> int:
        """Conta quantos números do jogo foram sorteados"""
        return len(self.to_set().intersection(set(game)))
    
    class Config:
        json_schema_extra = {
            "example": {
                "contest_id": 3000,
                "draw_date": "2024-01-15",
                "numbers": [1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 24, 25]
            }
        }
