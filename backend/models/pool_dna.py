"""
DNA Simplificado: Apenas o Pool de Números
Evolui qual é a melhor combinação de números para bolões
"""
from pydantic import BaseModel, Field
from typing import List, Set
import numpy as np


class PoolDNA(BaseModel):
    """
    Cromossomo simplificado: apenas o pool de números (15-25 números)
    
    Ao invés de evoluir 20+ parâmetros, evolui apenas:
    - Qual pool de números é melhor
    - Tamanho ideal do pool
    """
    
    pool: List[int] = Field(..., description="Pool de números selecionados (1-25)")
    fitness: float = Field(default=0.0, description="Fitness score (ROI médio)")
    roi: float = Field(default=0.0, description="ROI médio em simulações")
    generation: int = Field(default=0, description="Geração")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Garante pool ordenado e sem duplicatas
        self.pool = sorted(list(set(self.pool)))
    
    @classmethod
    def random(cls, min_size: int = 18, max_size: int = 25, 
               seed: int = None) -> "PoolDNA":
        """
        Gera pool aleatório
        
        Args:
            min_size: Tamanho mínimo (padrão: 18)
            max_size: Tamanho máximo (padrão: 25)
            seed: Seed opcional para reprodutibilidade
        
        Returns:
            PoolDNA com pool aleatório
        """
        rng = np.random.default_rng(seed)
        
        # Escolhe tamanho aleatório
        pool_size = rng.integers(min_size, max_size + 1)
        
        # Seleciona números aleatoriamente
        pool = sorted(rng.choice(range(1, 26), size=pool_size, replace=False).tolist())
        
        return cls(pool=pool)
    
    def mutate(self, mutation_rate: float = 0.3, seed: int = None) -> "PoolDNA":
        """
        Mutação: remove alguns números e adiciona outros
        
        Args:
            mutation_rate: Taxa de mutação (0-1)
            seed: Seed opcional
        
        Returns:
            Novo PoolDNA mutado
        """
        rng = np.random.default_rng(seed)
        
        new_pool = self.pool.copy()
        
        # Define quantos números remover/adicionar
        num_mutations = max(1, int(len(new_pool) * mutation_rate))
        
        # Remove números aleatoriamente
        if len(new_pool) > 15:  # Nunca ficar menor que 15
            indices_remove = rng.choice(len(new_pool), size=min(num_mutations, len(new_pool) - 15), replace=False)
            new_pool = [new_pool[i] for i in range(len(new_pool)) if i not in indices_remove]
        
        # Adiciona números novos
        available = [n for n in range(1, 26) if n not in new_pool]
        if available:
            num_add = min(num_mutations, len(available))
            new_numbers = rng.choice(available, size=num_add, replace=False).tolist()
            new_pool = sorted(new_pool + new_numbers)
        
        return PoolDNA(pool=new_pool, generation=self.generation + 1)
    
    @classmethod
    def crossover(cls, parent1: "PoolDNA", parent2: "PoolDNA", 
                  seed: int = None) -> "PoolDNA":
        """
        Crossover: combina pools de 2 pais
        
        Estratégia: pega alguns números de cada pai
        
        Args:
            parent1: Primeiro pai
            parent2: Segundo pai
            seed: Seed opcional
        
        Returns:
            Novo PoolDNA com genes dos dois pais
        """
        rng = np.random.default_rng(seed)
        
        # Pega proporção aleatória de cada pai
        ratio = rng.uniform(0.3, 0.7)
        
        size1 = max(1, int(len(parent1.pool) * ratio))
        size2 = len(parent2.pool) - (len(parent1.pool) - size1)
        
        # Seleciona números
        pool1_selected = rng.choice(parent1.pool, size=min(size1, len(parent1.pool)), replace=False).tolist()
        pool2_selected = rng.choice(parent2.pool, size=min(size2, len(parent2.pool)), replace=False).tolist()
        
        # Combina
        child_pool = sorted(list(set(pool1_selected + pool2_selected)))
        
        # Garante tamanho válido
        if len(child_pool) < 15:
            available = [n for n in range(1, 26) if n not in child_pool]
            num_add = 15 - len(child_pool)
            if available:
                child_pool = sorted(child_pool + rng.choice(available, size=min(num_add, len(available)), replace=False).tolist())
        elif len(child_pool) > 25:
            child_pool = sorted(rng.choice(child_pool, size=25, replace=False).tolist())
        
        return cls(pool=child_pool, generation=max(parent1.generation, parent2.generation) + 1)
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "pool": self.pool,
            "pool_size": len(self.pool),
            "fitness": float(self.fitness),
            "roi": float(self.roi),
            "generation": self.generation
        }
