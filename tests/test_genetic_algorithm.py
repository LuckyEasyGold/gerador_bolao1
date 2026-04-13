import pytest
import numpy as np
from datetime import date
from backend.core.genetic_algorithm import (
    Population, TournamentSelector, GeneticOperators,
    Elitism, ConvergenceDetector, FitnessEvaluator,
    GeneticAlgorithm, GenerationStats, EvolutionResult
)
from backend.core.feature_engineering import FeatureEngineer
from backend.models.dna import DNA, DNAGene
from backend.models.contest import Contest


@pytest.fixture
def sample_contests():
    """Cria concursos de exemplo"""
    return [
        Contest(contest_id=i, draw_date=date(2024, 1, i),
                numbers=list(range(1 + (i % 3), 16 + (i % 3))))
        for i in range(1, 21)
    ]


@pytest.fixture
def engineer(sample_contests):
    """FeatureEngineer fitted"""
    eng = FeatureEngineer()
    eng.fit(sample_contests)
    return eng


def test_population_initialization():
    """Testa inicialização de população"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    assert len(pop.individuals) == 10
    assert all(isinstance(ind, DNA) for ind in pop.individuals)


def test_population_get_best():
    """Testa seleção dos melhores"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    # Define fitness manualmente
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    best = pop.get_best(3)
    
    assert len(best) == 3
    assert best[0].fitness == 9.0
    assert best[1].fitness == 8.0


def test_population_get_worst():
    """Testa seleção dos piores"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    worst = pop.get_worst(3)
    
    assert len(worst) == 3
    assert worst[0].fitness == 0.0


def test_population_stats():
    """Testa estatísticas da população"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    best, avg, worst, std = pop.get_stats()
    
    assert best == 9.0
    assert avg == 4.5
    assert worst == 0.0
    assert std > 0


def test_population_diversity():
    """Testa cálculo de diversidade"""
    pop = Population(size=5, seed=42)
    pop.initialize_random()
    
    diversity = pop.calculate_diversity()
    
    assert diversity > 0
    assert isinstance(diversity, float)


def test_tournament_selector():
    """Testa seleção por torneio"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    selector = TournamentSelector(tournament_size=3, seed=42)
    selected = selector.select(pop)
    
    assert isinstance(selected, DNA)
    assert selected.fitness >= 0


def test_tournament_selector_pair():
    """Testa seleção de par"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    selector = TournamentSelector(tournament_size=3, seed=42)
    parent1, parent2 = selector.select_pair(pop)
    
    assert isinstance(parent1, DNA)
    assert isinstance(parent2, DNA)


def test_genetic_operators_crossover():
    """Testa crossover"""
    rng = np.random.default_rng(42)
    parent1 = DNA(genes=DNAGene.random(rng))
    parent2 = DNA(genes=DNAGene.random(rng))
    
    operators = GeneticOperators(seed=42)
    child = operators.crossover(parent1, parent2)
    
    assert isinstance(child, DNA)
    assert child.generation > 0


def test_genetic_operators_mutate():
    """Testa mutação"""
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    original_genes = dna.genes.to_dict()
    
    operators = GeneticOperators(mutation_rate=1.0, seed=42)
    mutated = operators.mutate(dna)
    
    assert isinstance(mutated, DNA)
    # Pelo menos um gene deve ter mudado
    assert mutated.genes.to_dict() != original_genes


def test_elitism():
    """Testa elitismo"""
    pop = Population(size=10, seed=42)
    pop.initialize_random()
    
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    elite = Elitism.preserve_elite(pop, elite_size=3)
    
    assert len(elite) == 3
    assert elite[0].fitness == 9.0


def test_convergence_detector():
    """Testa detector de convergência"""
    detector = ConvergenceDetector(threshold=0.01, patience=5)
    
    # Simula melhoria
    for i in range(10):
        detector.update(1.0 + i * 0.1)
    
    assert not detector.has_converged()
    
    # Simula estagnação
    for i in range(10):
        detector.update(2.0)
    
    assert detector.has_converged()


def test_convergence_detector_generation():
    """Testa identificação de geração de convergência"""
    detector = ConvergenceDetector(threshold=0.01, patience=5)
    
    for i in range(10):
        detector.update(1.0)
    
    if detector.has_converged():
        gen = detector.get_convergence_generation()
        assert gen is not None
        assert gen >= 0


def test_fitness_evaluator(engineer):
    """Testa avaliador de fitness"""
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    
    evaluator = FitnessEvaluator(
        engineer=engineer,
        budget=50.0,
        simulations=100,
        seed=42
    )
    
    fitness = evaluator.evaluate(dna)
    
    assert isinstance(fitness, float)
    assert dna.fitness == fitness
    assert dna.roi != 0.0


def test_fitness_evaluator_population(engineer):
    """Testa avaliação de população"""
    pop = Population(size=5, seed=42)
    pop.initialize_random()
    
    evaluator = FitnessEvaluator(
        engineer=engineer,
        budget=50.0,
        simulations=100,
        seed=42
    )
    
    evaluator.evaluate_population(pop)
    
    assert all(ind.fitness != 0.0 for ind in pop.individuals)


@pytest.mark.slow
def test_genetic_algorithm_small(engineer):
    """Testa GA com população pequena"""
    ga = GeneticAlgorithm(
        engineer=engineer,
        budget=50.0,
        population_size=5,
        generations=3,
        simulations=100,
        seed=42
    )
    
    result = ga.evolve()
    
    assert isinstance(result, EvolutionResult)
    assert result.best_dna is not None
    assert result.best_fitness > 0
    assert result.generations_run <= 3
    assert len(result.generation_stats) > 0


def test_generation_stats():
    """Testa estatísticas de geração"""
    stats = GenerationStats(
        generation=1,
        best_fitness=1.5,
        avg_fitness=1.0,
        worst_fitness=0.5,
        std_fitness=0.3,
        best_roi=0.2,
        avg_roi=0.1,
        diversity=5.0,
        elapsed_time=10.5
    )
    
    data = stats.to_dict()
    
    assert data["generation"] == 1
    assert data["best_fitness"] == 1.5
    assert data["elapsed_time"] == 10.5


def test_evolution_result_serialization(engineer):
    """Testa serialização de resultado"""
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    dna.fitness = 1.5
    
    stats = [
        GenerationStats(
            generation=1,
            best_fitness=1.0,
            avg_fitness=0.8,
            worst_fitness=0.5,
            std_fitness=0.2,
            best_roi=0.1,
            avg_roi=0.05,
            diversity=5.0,
            elapsed_time=10.0
        )
    ]
    
    result = EvolutionResult(
        best_dna=dna,
        best_fitness=1.5,
        generations_run=1,
        total_time=10.0,
        convergence_generation=None,
        generation_stats=stats
    )
    
    data = result.to_dict()
    
    assert "best_dna" in data
    assert "best_fitness" in data
    assert "generation_stats" in data
    assert len(data["generation_stats"]) == 1


def test_population_diversity_identical():
    """Testa diversidade com população idêntica"""
    pop = Population(size=5, seed=42)
    
    # Cria população idêntica
    base_dna = DNA(genes=DNAGene.random(np.random.default_rng(42)))
    for _ in range(5):
        pop.add(base_dna)
    
    diversity = pop.calculate_diversity()
    
    assert diversity == 0.0  # Sem diversidade


def test_genetic_operators_mutation_rate():
    """Testa taxa de mutação"""
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    
    # Taxa 0 = sem mutação
    operators = GeneticOperators(mutation_rate=0.0, seed=42)
    mutated = operators.mutate(dna)
    
    # Genes devem ser idênticos (exceto geração)
    assert mutated.genes.to_dict() == dna.genes.to_dict()


def test_convergence_detector_no_convergence():
    """Testa quando não converge"""
    detector = ConvergenceDetector(threshold=0.01, patience=5)
    
    # Melhoria contínua
    for i in range(20):
        detector.update(float(i))
    
    assert not detector.has_converged()


def test_elitism_empty_population():
    """Testa elitismo com população vazia"""
    pop = Population(size=0, seed=42)
    
    elite = Elitism.preserve_elite(pop, elite_size=3)
    
    assert len(elite) == 0


def test_tournament_selector_small_population():
    """Testa torneio com população pequena"""
    pop = Population(size=2, seed=42)
    pop.initialize_random()
    
    for i, ind in enumerate(pop.individuals):
        ind.fitness = float(i)
    
    selector = TournamentSelector(tournament_size=5, seed=42)
    selected = selector.select(pop)
    
    assert isinstance(selected, DNA)
