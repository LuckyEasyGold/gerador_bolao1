from pydantic import BaseModel, Field, field_validator
from typing import Dict
import numpy as np


class DNAGene(BaseModel):
    """Define os ranges válidos para cada gene do DNA evolutivo"""
    
    # Pesos de orçamento
    w15: float = Field(ge=0.0, le=1.0, description="Peso orçamento jogo 15")
    w16: float = Field(ge=0.0, le=1.0, description="Peso orçamento jogo 16")
    w17: float = Field(ge=0.0, le=1.0, description="Peso orçamento jogo 17")
    
    # Pesos de features históricas
    wf: float = Field(ge=-1.0, le=1.0, description="Peso frequência histórica")
    wa: float = Field(ge=-1.0, le=1.0, description="Peso atraso")
    wr: float = Field(ge=-1.0, le=1.0, description="Peso repetição concurso anterior")
    wc_aff: float = Field(ge=0.0, le=2.0, description="Peso afinidade combinatória")
    
    # Temperatura
    T_base: float = Field(ge=0.1, le=5.0, description="Temperatura base")
    kappa: float = Field(ge=0.0, le=1.0, description="Modulação dinâmica temperatura")
    
    # Pesos estruturais
    wp: float = Field(ge=0.0, le=1.0, description="Peso paridade")
    wl: float = Field(ge=0.0, le=1.0, description="Peso linhas/colunas")
    ws: float = Field(ge=0.0, le=1.0, description="Peso sequências")
    wo: float = Field(ge=0.0, le=1.0, description="Peso overlap local")
    
    # Pesos globais
    wcov: float = Field(ge=0.0, le=1.0, description="Peso cobertura global")
    wd: float = Field(ge=0.0, le=1.0, description="Peso diversidade frequência")
    woverlap: float = Field(ge=0.0, le=1.0, description="Peso overlap global")
    
    # Parâmetros de geração
    pool_size: int = Field(ge=18, le=25, description="Tamanho do pool de dezenas")
    candidates_per_game: int = Field(ge=10, le=200, description="Candidatos por jogo")
    refine_iterations: int = Field(ge=10, le=2000, description="Iterações busca local")
    
    @field_validator('w15', 'w16', 'w17')
    @classmethod
    def validate_budget_weights(cls, v: float) -> float:
        """Garante que pesos de orçamento estão normalizados"""
        return max(0.0, min(1.0, v))
    
    def to_dict(self) -> Dict[str, float]:
        """Converte DNA para dicionário"""
        return self.model_dump()
    
    @classmethod
    def random(cls, rng: np.random.Generator = None) -> "DNAGene":
        """Gera DNA aleatório dentro dos ranges válidos"""
        if rng is None:
            rng = np.random.default_rng()
        
        return cls(
            w15=rng.uniform(0.0, 1.0),
            w16=rng.uniform(0.0, 1.0),
            w17=rng.uniform(0.0, 1.0),
            wf=rng.uniform(-1.0, 1.0),
            wa=rng.uniform(-1.0, 1.0),
            wr=rng.uniform(-1.0, 1.0),
            wc_aff=rng.uniform(0.0, 2.0),
            T_base=rng.uniform(0.1, 5.0),
            kappa=rng.uniform(0.0, 1.0),
            wp=rng.uniform(0.0, 1.0),
            wl=rng.uniform(0.0, 1.0),
            ws=rng.uniform(0.0, 1.0),
            wo=rng.uniform(0.0, 1.0),
            wcov=rng.uniform(0.0, 1.0),
            wd=rng.uniform(0.0, 1.0),
            woverlap=rng.uniform(0.0, 1.0),
            pool_size=rng.integers(18, 26),
            candidates_per_game=rng.integers(10, 201),
            refine_iterations=rng.integers(10, 2001),
        )


class DNA(BaseModel):
    """Representa um indivíduo completo com fitness"""
    
    genes: DNAGene
    fitness: float = 0.0
    roi: float = 0.0
    risk: float = 0.0
    generation: int = 0
    
    def mutate(self, mutation_rate: float = 0.1, mutation_strength: float = 0.2, 
               rng: np.random.Generator = None) -> "DNA":
        """Aplica mutação gaussiana com clamp nos genes"""
        if rng is None:
            rng = np.random.default_rng()
        
        genes_dict = self.genes.to_dict()
        mutated = {}
        
        for key, value in genes_dict.items():
            if rng.random() < mutation_rate:
                if isinstance(value, int):
                    # Mutação inteira
                    delta = rng.integers(-2, 3)
                    mutated[key] = value + delta
                else:
                    # Mutação gaussiana
                    delta = rng.normal(0, mutation_strength)
                    mutated[key] = value + delta
            else:
                mutated[key] = value
        
        # Cria novo DNA com genes mutados (validação automática via Pydantic)
        return DNA(
            genes=DNAGene(**mutated),
            generation=self.generation + 1
        )
    
    @staticmethod
    def crossover(parent1: "DNA", parent2: "DNA", 
                  rng: np.random.Generator = None) -> "DNA":
        """Crossover uniforme entre dois pais"""
        if rng is None:
            rng = np.random.default_rng()
        
        genes1 = parent1.genes.to_dict()
        genes2 = parent2.genes.to_dict()
        child_genes = {}
        
        for key in genes1.keys():
            child_genes[key] = genes1[key] if rng.random() < 0.5 else genes2[key]
        
        return DNA(
            genes=DNAGene(**child_genes),
            generation=max(parent1.generation, parent2.generation) + 1
        )
