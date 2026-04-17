"""
Algoritmo Genético Simplificado
Evolui apenas o pool ótimo de números (15-25 números)
Muito mais rápido e interpretável que o GA original
"""
import numpy as np
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass
import time

from backend.models.pool_dna import PoolDNA
from backend.core.monte_carlo import MonteCarloSimulator
from backend.models.contest import Contest


@dataclass
class PoolGenerationStats:
    """Estatísticas de uma geração"""
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    best_pool: List[int]
    best_roi: float
    elapsed_time: float
    
    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "best_fitness": float(self.best_fitness),
            "avg_fitness": float(self.avg_fitness),
            "worst_fitness": float(self.worst_fitness),
            "best_pool": self.best_pool,
            "best_roi": float(self.best_roi),
            "elapsed_time": float(self.elapsed_time)
        }


@dataclass
class PoolEvolutionResult:
    """Resultado final da evolução"""
    best_pool: List[int]
    best_fitness: float
    best_roi: float
    generations_run: int
    total_time: float
    generation_stats: List[PoolGenerationStats]
    
    def to_dict(self) -> dict:
        return {
            "best_pool": self.best_pool,
            "pool_size": len(self.best_pool),
            "best_fitness": float(self.best_fitness),
            "best_roi": float(self.best_roi),
            "generations_run": self.generations_run,
            "total_time": float(self.total_time),
            "generation_stats": [g.to_dict() for g in self.generation_stats]
        }


class PoolGeneticAlgorithm:
    """
    GA Simplificado: Evolui apenas o pool de números
    
    Objetivo: Encontrar qual combinação de 15-25 números tem melhor ROI
    """
    
    def __init__(
        self,
        contests: List[Contest],
        population_size: int = 10,
        generations: int = 20,
        simulations: int = 500,
        mutation_rate: float = 0.3,
        elitism_rate: float = 0.2,
        seed: Optional[int] = None,
        callback: Optional[Callable] = None
    ):
        """
        Args:
            contests: Histórico de concursos
            population_size: Tamanho população (padrão: 10)
            generations: Quantas gerações (padrão: 20)
            simulations: Simulações Monte Carlo por pool (padrão: 500)
            mutation_rate: Taxa mutação (padrão: 0.3)
            elitism_rate: Taxa elitismo (padrão: 0.2)
            seed: Seed para reprodutibilidade
            callback: Função chamada a cada geração
        """
        self.contests = contests
        self.population_size = population_size
        self.generations = generations
        self.simulations = simulations
        self.mutation_rate = mutation_rate
        self.elitism_rate = elitism_rate
        self.rng = np.random.default_rng(seed)
        self.callback = callback
        
        self.simulator = MonteCarloSimulator(contests, seed=seed)
        self.population: List[PoolDNA] = []
        self.generation_stats: List[PoolGenerationStats] = []
    
    def evolve(self) -> PoolEvolutionResult:
        """
        Executa evolução
        
        Returns:
            Resultado com pool ótimo encontrado
        """
        start_time = time.time()
        
        # Inicializa população
        self._initialize_population()
        
        # Evalua população inicial
        self._evaluate_population()
        
        # Evolui
        for gen in range(self.generations):
            gen_start = time.time()
            
            # Seleciona e reproduz
            self._selection_and_reproduction()
            
            # Avalia novamente
            self._evaluate_population()
            
            # Coleta estatísticas
            stats = self._collect_stats(gen, gen_start)
            self.generation_stats.append(stats)
            
            # Callback
            if self.callback:
                self.callback(gen, self.population, stats)
        
        # Retorna melhor resultado
        best = self.get_best()
        total_time = time.time() - start_time
        
        return PoolEvolutionResult(
            best_pool=best.pool,
            best_fitness=best.fitness,
            best_roi=best.roi,
            generations_run=self.generations,
            total_time=total_time,
            generation_stats=self.generation_stats
        )
    
    def _initialize_population(self) -> None:
        """Inicializa população com pools aleatórios"""
        self.population = [
            PoolDNA.random(min_size=18, max_size=25, seed=int(self.rng.integers(0, 1000000)))
            for _ in range(self.population_size)
        ]
    
    def _evaluate_population(self) -> None:
        """Avalia fitness de cada indivíduo na população"""
        for individual in self.population:
            # Simula loterias com esse pool
            roi_results = []
            
            for _ in range(self.simulations):
                # Gera bolão simples com esse pool
                numbers = self.rng.choice(individual.pool, size=15, replace=False)
                
                # Simula
                wins = self.simulator.simulate_single_draw(list(numbers))
                cost = 10.0  # Custoj15 = R$ 10
                roi = (wins - cost) / cost if cost > 0 else 0
                roi_results.append(roi)
            
            # Calcula fitness como ROI médio
            avg_roi = float(np.mean(roi_results))
            fitness = max(0, avg_roi)  # Fitness nunca negativo
            
            individual.fitness = fitness
            individual.roi = avg_roi
    
    def _selection_and_reproduction(self) -> None:
        """
        Seleção por torneio e reprodução
        Mantém elites e cria nova geração
        """
        # Ordena por fitness
        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        
        # Mantém elites
        num_elites = max(1, int(len(self.population) * self.elitism_rate))
        elites = sorted_pop[:num_elites]
        
        # Cria nova população
        new_population = elites.copy()
        
        # Reproduz até completar população
        while len(new_population) < self.population_size:
            # Torneio simples
            parent1 = self._tournament_select(sorted_pop)
            parent2 = self._tournament_select(sorted_pop)
            
            # Crossover
            child = PoolDNA.crossover(parent1, parent2, seed=int(self.rng.integers(0, 1000000)))
            
            # Mutação
            if self.rng.random() < 0.7:  # 70% de chance de mutar
                child = child.mutate(mutation_rate=self.mutation_rate, 
                                   seed=int(self.rng.integers(0, 1000000)))
            
            new_population.append(child)
        
        self.population = new_population[:self.population_size]
    
    def _tournament_select(self, population: List[PoolDNA], tournament_size: int = 3) -> PoolDNA:
        """Seleção por torneio"""
        tournament_indices = self.rng.choice(len(population), size=min(tournament_size, len(population)), replace=False)
        tournament = [population[i] for i in tournament_indices]
        return max(tournament, key=lambda x: x.fitness)
    
    def _collect_stats(self, generation: int, gen_start: float) -> PoolGenerationStats:
        """Coleta estatísticas da geração"""
        fitness_values = [ind.fitness for ind in self.population]
        roi_values = [ind.roi for ind in self.population]
        
        best = max(self.population, key=lambda x: x.fitness)
        
        return PoolGenerationStats(
            generation=generation,
            best_fitness=float(max(fitness_values)),
            avg_fitness=float(np.mean(fitness_values)),
            worst_fitness=float(min(fitness_values)),
            best_pool=best.pool,
            best_roi=float(best.roi),
            elapsed_time=time.time() - gen_start
        )
    
    def get_best(self) -> PoolDNA:
        """Retorna melhor indivíduo da população atual"""
        return max(self.population, key=lambda x: x.fitness)
