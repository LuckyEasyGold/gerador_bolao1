"""
Algoritmo Genético para Lotofácil
Evolui estratégias de geração de bolões
"""
import numpy as np
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
from backend.models.dna import DNA, DNAGene
from backend.core.feature_engineering import FeatureEngineer
from backend.core.game_generator import TicketGenerator
from backend.core.monte_carlo import MonteCarloSimulator
from backend.config import get_settings

settings = get_settings()


@dataclass
class GenerationStats:
    """Estatísticas de uma geração"""
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    std_fitness: float
    best_roi: float
    avg_roi: float
    diversity: float
    elapsed_time: float
    
    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "best_fitness": self.best_fitness,
            "avg_fitness": self.avg_fitness,
            "worst_fitness": self.worst_fitness,
            "std_fitness": self.std_fitness,
            "best_roi": self.best_roi,
            "avg_roi": self.avg_roi,
            "diversity": self.diversity,
            "elapsed_time": self.elapsed_time
        }


@dataclass
class EvolutionResult:
    """Resultado completo da evolução"""
    best_dna: DNA
    best_fitness: float
    generations_run: int
    total_time: float
    convergence_generation: Optional[int]
    generation_stats: List[GenerationStats]
    
    def to_dict(self) -> dict:
        return {
            "best_dna": self.best_dna.genes.to_dict(),
            "best_fitness": self.best_fitness,
            "generations_run": self.generations_run,
            "total_time": self.total_time,
            "convergence_generation": self.convergence_generation,
            "generation_stats": [g.to_dict() for g in self.generation_stats]
        }


class Population:
    """Gerencia população de DNAs"""
    
    def __init__(self, size: int, seed: Optional[int] = None):
        self.size = size
        self.rng = np.random.default_rng(seed)
        self.individuals: List[DNA] = []
    
    def initialize_random(self) -> None:
        """Inicializa população aleatória"""
        self.individuals = [
            DNA(genes=DNAGene.random(self.rng))
            for _ in range(self.size)
        ]
    
    def add(self, dna: DNA) -> None:
        """Adiciona indivíduo à população"""
        self.individuals.append(dna)
    
    def get_best(self, n: int = 1) -> List[DNA]:
        """Retorna os n melhores indivíduos"""
        sorted_pop = sorted(
            self.individuals,
            key=lambda x: x.fitness,
            reverse=True
        )
        return sorted_pop[:n]
    
    def get_worst(self, n: int = 1) -> List[DNA]:
        """Retorna os n piores indivíduos"""
        sorted_pop = sorted(
            self.individuals,
            key=lambda x: x.fitness
        )
        return sorted_pop[:n]
    
    def get_stats(self) -> Tuple[float, float, float, float]:
        """Retorna estatísticas da população"""
        fitnesses = [ind.fitness for ind in self.individuals]
        return (
            max(fitnesses),
            np.mean(fitnesses),
            min(fitnesses),
            np.std(fitnesses)
        )
    
    def calculate_diversity(self) -> float:
        """
        Calcula diversidade genética da população
        
        Usa distância euclidiana média entre indivíduos
        """
        if len(self.individuals) < 2:
            return 0.0
        
        # Converte DNAs para vetores
        vectors = []
        for ind in self.individuals:
            genes_dict = ind.genes.to_dict()
            vector = [float(v) for v in genes_dict.values()]
            vectors.append(vector)
        
        vectors = np.array(vectors)
        
        # Calcula distância média
        total_distance = 0.0
        count = 0
        
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                distance = np.linalg.norm(vectors[i] - vectors[j])
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0


class TournamentSelector:
    """Seleção por torneio"""
    
    def __init__(self, tournament_size: int = 3, seed: Optional[int] = None):
        self.tournament_size = tournament_size
        self.rng = np.random.default_rng(seed)
    
    def select(self, population: Population) -> DNA:
        """
        Seleciona um indivíduo via torneio
        
        Escolhe aleatoriamente tournament_size indivíduos
        e retorna o melhor deles
        """
        tournament = self.rng.choice(
            population.individuals,
            size=min(self.tournament_size, len(population.individuals)),
            replace=False
        )
        
        return max(tournament, key=lambda x: x.fitness)
    
    def select_pair(self, population: Population) -> Tuple[DNA, DNA]:
        """Seleciona par de pais"""
        parent1 = self.select(population)
        parent2 = self.select(population)
        
        # Garante que são diferentes
        max_tries = 10
        tries = 0
        while parent1 is parent2 and tries < max_tries:
            parent2 = self.select(population)
            tries += 1
        
        return parent1, parent2


class GeneticOperators:
    """Operadores genéticos (crossover e mutação)"""
    
    def __init__(self, mutation_rate: float = 0.1, 
                 mutation_strength: float = 0.2,
                 seed: Optional[int] = None):
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.rng = np.random.default_rng(seed)
    
    def crossover(self, parent1: DNA, parent2: DNA) -> DNA:
        """
        Crossover uniforme
        
        Cada gene tem 50% de chance de vir de cada pai
        """
        return DNA.crossover(parent1, parent2, self.rng)
    
    def mutate(self, dna: DNA) -> DNA:
        """
        Mutação gaussiana
        
        Cada gene tem mutation_rate de chance de sofrer mutação
        """
        return dna.mutate(
            mutation_rate=self.mutation_rate,
            mutation_strength=self.mutation_strength,
            rng=self.rng
        )


class Elitism:
    """Implementa elitismo"""
    
    @staticmethod
    def preserve_elite(population: Population, 
                      elite_size: int) -> List[DNA]:
        """
        Preserva os melhores indivíduos
        
        Args:
            population: População atual
            elite_size: Quantos preservar
        
        Returns:
            Lista com elite
        """
        return population.get_best(elite_size)


class ConvergenceDetector:
    """Detecta convergência do algoritmo"""
    
    def __init__(self, threshold: float = 0.001, 
                 patience: int = 10):
        self.threshold = threshold
        self.patience = patience
        self.history: List[float] = []
    
    def update(self, best_fitness: float) -> None:
        """Atualiza histórico"""
        self.history.append(best_fitness)
    
    def has_converged(self) -> bool:
        """
        Verifica se convergiu
        
        Convergência = melhoria < threshold por patience gerações
        """
        if len(self.history) < self.patience:
            return False
        
        recent = self.history[-self.patience:]
        improvement = max(recent) - min(recent)
        
        return improvement < self.threshold
    
    def get_convergence_generation(self) -> Optional[int]:
        """Retorna geração onde convergiu"""
        if not self.has_converged():
            return None
        
        return len(self.history) - self.patience


class FitnessEvaluator:
    """Avalia fitness de indivíduos"""
    
    def __init__(self, engineer: FeatureEngineer, 
                 budget: float,
                 simulations: int = 1000,
                 seed: Optional[int] = None):
        self.engineer = engineer
        self.budget = budget
        self.simulations = simulations
        self.seed = seed
    
    def evaluate(self, dna: DNA) -> float:
        """
        Avalia fitness de um DNA
        
        Fitness = função do ROI e risco
        """
        # Gera bolão
        generator = TicketGenerator(self.engineer, dna, seed=self.seed)
        ticket = generator.generate_ticket(self.budget)
        
        # Simula
        simulator = MonteCarloSimulator(seed=self.seed, use_crn=True)
        result = simulator.simulate_ticket(ticket, self.simulations)
        
        # Fitness = ROI - penalização por risco
        # Sharpe Ratio já considera risco
        fitness = result.sharpe_ratio
        
        # Atualiza DNA
        dna.fitness = fitness
        dna.roi = result.roi
        dna.risk = result.std_return / result.avg_return if result.avg_return > 0 else 1.0
        
        return fitness
    
    def evaluate_population(self, population: Population) -> None:
        """Avalia toda a população"""
        for individual in population.individuals:
            if individual.fitness == 0.0:  # Não avaliado ainda
                self.evaluate(individual)


class GeneticAlgorithm:
    """Algoritmo Genético completo"""
    
    def __init__(self,
                 engineer: FeatureEngineer,
                 budget: float,
                 population_size: int = 50,
                 generations: int = 100,
                 mutation_rate: float = 0.1,
                 mutation_strength: float = 0.2,
                 crossover_rate: float = 0.7,
                 elitism_rate: float = 0.1,
                 tournament_size: int = 3,
                 simulations: int = 1000,
                 convergence_threshold: float = 0.001,
                 convergence_patience: int = 10,
                 seed: Optional[int] = None,
                 callback: Optional[Callable[[int, Population], None]] = None):
        
        self.engineer = engineer
        self.budget = budget
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.elitism_rate = elitism_rate
        self.seed = seed
        self.callback = callback
        
        # Componentes
        self.rng = np.random.default_rng(seed)
        self.population = Population(population_size, seed)
        self.selector = TournamentSelector(tournament_size, seed)
        self.operators = GeneticOperators(mutation_rate, mutation_strength, seed)
        self.evaluator = FitnessEvaluator(engineer, budget, simulations, seed)
        self.convergence = ConvergenceDetector(
            convergence_threshold, 
            convergence_patience
        )
        
        # Estatísticas
        self.generation_stats: List[GenerationStats] = []
        self.start_time: Optional[datetime] = None
    
    def evolve(self) -> EvolutionResult:
        """
        Executa evolução completa
        
        Returns:
            EvolutionResult com melhor DNA e estatísticas
        """
        self.start_time = datetime.now()
        
        # Inicializa população
        print("Inicializando população...")
        self.population.initialize_random()
        
        # Avalia população inicial
        print("Avaliando população inicial...")
        self.evaluator.evaluate_population(self.population)
        
        # Evolução
        for gen in range(self.generations):
            gen_start = datetime.now()
            
            print(f"\nGeração {gen + 1}/{self.generations}")
            
            # Nova população
            new_population = Population(self.population_size, self.seed)
            
            # Elitismo
            elite_size = int(self.population_size * self.elitism_rate)
            elite = Elitism.preserve_elite(self.population, elite_size)
            for ind in elite:
                new_population.add(ind)
            
            # Gera resto da população
            while len(new_population.individuals) < self.population_size:
                # Seleção
                parent1, parent2 = self.selector.select_pair(self.population)
                
                # Crossover
                if self.rng.random() < self.crossover_rate:
                    child = self.operators.crossover(parent1, parent2)
                else:
                    child = parent1  # Clona
                
                # Mutação
                child = self.operators.mutate(child)
                
                # Avalia
                self.evaluator.evaluate(child)
                
                new_population.add(child)
            
            # Atualiza população
            self.population = new_population
            
            # Estatísticas
            best, avg, worst, std = self.population.get_stats()
            diversity = self.population.calculate_diversity()
            best_ind = self.population.get_best(1)[0]
            
            gen_time = (datetime.now() - gen_start).total_seconds()
            
            stats = GenerationStats(
                generation=gen + 1,
                best_fitness=best,
                avg_fitness=avg,
                worst_fitness=worst,
                std_fitness=std,
                best_roi=best_ind.roi,
                avg_roi=np.mean([ind.roi for ind in self.population.individuals]),
                diversity=diversity,
                elapsed_time=gen_time
            )
            
            self.generation_stats.append(stats)
            
            print(f"  Melhor fitness: {best:.4f}")
            print(f"  Fitness médio: {avg:.4f}")
            print(f"  Melhor ROI: {best_ind.roi:.4f}")
            print(f"  Diversidade: {diversity:.4f}")
            print(f"  Tempo: {gen_time:.2f}s")
            
            # Callback
            if self.callback:
                self.callback(gen + 1, self.population)
            
            # Convergência
            self.convergence.update(best)
            if self.convergence.has_converged():
                print(f"\n✓ Convergiu na geração {gen + 1}")
                break
        
        # Resultado final
        total_time = (datetime.now() - self.start_time).total_seconds()
        best_dna = self.population.get_best(1)[0]
        
        return EvolutionResult(
            best_dna=best_dna,
            best_fitness=best_dna.fitness,
            generations_run=len(self.generation_stats),
            total_time=total_time,
            convergence_generation=self.convergence.get_convergence_generation(),
            generation_stats=self.generation_stats
        )


class MultiObjectiveGA(GeneticAlgorithm):
    """
    Algoritmo Genético Multi-Objetivo
    
    Otimiza ROI e minimiza risco simultaneamente
    """
    
    def __init__(self, *args, roi_weight: float = 0.7, 
                 risk_weight: float = 0.3, **kwargs):
        super().__init__(*args, **kwargs)
        self.roi_weight = roi_weight
        self.risk_weight = risk_weight
    
    def _calculate_fitness(self, dna: DNA) -> float:
        """
        Fitness multi-objetivo
        
        Fitness = roi_weight * ROI - risk_weight * Risk
        """
        # Gera e simula
        generator = TicketGenerator(self.engineer, dna, seed=self.seed)
        ticket = generator.generate_ticket(self.budget)
        
        simulator = MonteCarloSimulator(seed=self.seed, use_crn=True)
        result = simulator.simulate_ticket(ticket, self.evaluator.simulations)
        
        # Fitness multi-objetivo
        roi_component = self.roi_weight * result.roi
        risk_component = self.risk_weight * dna.risk
        
        fitness = roi_component - risk_component
        
        dna.fitness = fitness
        dna.roi = result.roi
        dna.risk = result.std_return / result.avg_return if result.avg_return > 0 else 1.0
        
        return fitness
