import pytest
import numpy as np
from datetime import date
from backend.core.game_generator import (
    Game, Ticket, PoolSelector, SoftmaxSampler,
    StructuralScorer, GameGenerator, DiversityOptimizer,
    TicketGenerator
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


@pytest.fixture
def dna():
    """DNA de teste"""
    return DNA(genes=DNAGene.random(np.random.default_rng(42)))


def test_game_creation():
    """Testa criação de Game"""
    game = Game(numbers=[1, 5, 10, 15, 20, 3, 7, 12, 18, 22, 2, 8, 14, 19, 25], size=15, cost=3.0)
    
    assert len(game.numbers) == 15
    assert game.size == 15
    assert game.cost == 3.0
    assert game.numbers == sorted(game.numbers)  # Auto-ordenado


def test_ticket_creation():
    """Testa criação de Ticket"""
    games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(2, 17)), size=15, cost=3.0)
    ]
    
    ticket = Ticket(games=games, total_cost=6.0, total_games=2)
    
    assert len(ticket.games) == 2
    assert ticket.total_cost == 6.0
    assert ticket.total_games == 2


def test_pool_selector(engineer, dna):
    """Testa seleção de pool"""
    selector = PoolSelector(engineer, dna)
    
    pool = selector.select_pool(pool_size=20)
    
    assert len(pool) == 20
    assert all(1 <= n <= 25 for n in pool)
    assert len(set(pool)) == 20  # Sem duplicatas
    assert pool == sorted(pool)


def test_pool_selector_uses_dna_size(engineer, dna):
    """Testa que usa tamanho do DNA"""
    selector = PoolSelector(engineer, dna)
    
    pool = selector.select_pool()  # Sem especificar tamanho
    
    assert len(pool) == dna.genes.pool_size


def test_softmax_sampler(dna):
    """Testa amostragem softmax"""
    sampler = SoftmaxSampler(dna, seed=42)
    
    pool = list(range(1, 26))
    scores = np.random.rand(25)
    
    sampled = sampler.sample(pool, scores, n_samples=15)
    
    assert len(sampled) == 15
    assert len(set(sampled)) == 15  # Sem duplicatas
    assert all(n in pool for n in sampled)
    assert sampled == sorted(sampled)


def test_softmax_temperature():
    """Testa cálculo de temperatura"""
    dna = DNA(genes=DNAGene(
        w15=0.5, w16=0.3, w17=0.2,
        wf=0.5, wa=0.3, wr=0.2, wc_aff=1.0,
        T_base=2.0, kappa=0.5,
        wp=0.5, wl=0.5, ws=0.5, wo=0.5,
        wcov=0.5, wd=0.5, woverlap=0.5,
        pool_size=20, candidates_per_game=50, refine_iterations=100
    ))
    
    sampler = SoftmaxSampler(dna, seed=42)
    temp = sampler._compute_temperature()
    
    assert temp >= 0.1  # Temperatura mínima
    assert isinstance(temp, float)


def test_structural_scorer_parity(dna):
    """Testa score de paridade"""
    scorer = StructuralScorer(dna)
    
    # Balanceado: 7 pares, 8 ímpares
    balanced = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    score_balanced = scorer._score_parity(balanced)
    
    # Desbalanceado: todos ímpares
    unbalanced = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 1, 3]
    score_unbalanced = scorer._score_parity(unbalanced)
    
    assert score_balanced > score_unbalanced


def test_structural_scorer_distribution(dna):
    """Testa score de distribuição"""
    scorer = StructuralScorer(dna)
    
    # Distribuído: 3 por linha
    distributed = [1, 2, 3, 6, 7, 8, 11, 12, 13, 16, 17, 18, 21, 22, 23]
    score_dist = scorer._score_distribution(distributed)
    
    # Concentrado: tudo na primeira linha
    concentrated = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    score_conc = scorer._score_distribution(concentrated)
    
    assert score_dist > score_conc


def test_structural_scorer_sequences(dna):
    """Testa score de sequências"""
    scorer = StructuralScorer(dna)
    
    # Sem sequências longas
    no_seq = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 2, 4]
    score_no_seq = scorer._score_sequences(no_seq)
    
    # Com sequência longa
    long_seq = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 21, 22, 25]
    score_long_seq = scorer._score_sequences(long_seq)
    
    assert score_no_seq > score_long_seq


def test_game_generator(engineer, dna):
    """Testa geração de jogo"""
    generator = GameGenerator(engineer, dna, seed=42)
    
    game = generator.generate_game(size=15)
    
    assert len(game.numbers) == 15
    assert game.size == 15
    assert game.cost == 3.0
    assert game.score >= 0
    assert all(1 <= n <= 25 for n in game.numbers)


def test_game_generator_different_sizes(engineer, dna):
    """Testa geração de jogos de tamanhos diferentes"""
    generator = GameGenerator(engineer, dna, seed=42)
    
    game_15 = generator.generate_game(size=15)
    game_16 = generator.generate_game(size=16)
    game_17 = generator.generate_game(size=17)
    
    assert len(game_15.numbers) == 15
    assert len(game_16.numbers) == 16
    assert len(game_17.numbers) == 17
    
    assert game_15.cost == 3.0
    assert game_16.cost == 48.0
    assert game_17.cost == 408.0


def test_game_generator_with_pool(engineer, dna):
    """Testa geração com pool específico"""
    generator = GameGenerator(engineer, dna, seed=42)
    
    pool = list(range(1, 21))  # Pool de 20 números
    game = generator.generate_game(size=15, pool=pool)
    
    assert all(n in pool for n in game.numbers)


def test_diversity_optimizer_coverage(dna):
    """Testa cálculo de cobertura"""
    optimizer = DiversityOptimizer(dna)
    
    games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(11, 26)), size=15, cost=3.0)
    ]
    
    coverage = optimizer._calculate_coverage(games)
    
    # Cobre 25 números únicos
    assert coverage == 1.0


def test_diversity_optimizer_diversity(dna):
    """Testa cálculo de diversidade"""
    optimizer = DiversityOptimizer(dna)
    
    # Jogos muito diferentes
    diverse_games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(11, 26)), size=15, cost=3.0)
    ]
    
    # Jogos idênticos
    identical_games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(1, 16)), size=15, cost=3.0)
    ]
    
    div_diverse = optimizer._calculate_diversity(diverse_games)
    div_identical = optimizer._calculate_diversity(identical_games)
    
    assert div_diverse > div_identical


def test_diversity_optimizer_overlap(dna):
    """Testa cálculo de overlap"""
    optimizer = DiversityOptimizer(dna)
    
    # Jogos com muito overlap
    high_overlap = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(1, 16)), size=15, cost=3.0)
    ]
    
    # Jogos com pouco overlap
    low_overlap = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(11, 26)), size=15, cost=3.0)
    ]
    
    overlap_high = optimizer._calculate_overlap(high_overlap)
    overlap_low = optimizer._calculate_overlap(low_overlap)
    
    assert overlap_high > overlap_low


def test_diversity_optimizer_optimize_ticket(dna):
    """Testa otimização de ticket"""
    optimizer = DiversityOptimizer(dna)
    
    games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(11, 26)), size=15, cost=3.0)
    ]
    
    ticket = optimizer.optimize_ticket(games)
    
    assert ticket.total_games == 2
    assert ticket.total_cost == 6.0
    assert ticket.diversity_score >= 0
    assert ticket.coverage_score >= 0


def test_ticket_generator_budget_distribution(engineer, dna):
    """Testa distribuição de orçamento"""
    generator = TicketGenerator(engineer, dna, seed=42)
    
    distribution = generator._distribute_budget(100.0)
    
    assert 15 in distribution
    assert 16 in distribution
    assert 17 in distribution
    
    # Verifica que usa o orçamento
    total_cost = (
        distribution[15] * 3.0 +
        distribution[16] * 48.0 +
        distribution[17] * 408.0
    )
    assert total_cost <= 100.0


def test_ticket_generator_generate_ticket(engineer, dna):
    """Testa geração de ticket completo"""
    generator = TicketGenerator(engineer, dna, seed=42)
    
    ticket = generator.generate_ticket(budget=100.0)
    
    assert ticket.total_cost <= 100.0
    assert ticket.total_games > 0
    assert len(ticket.games) == ticket.total_games
    assert all(isinstance(g, Game) for g in ticket.games)


def test_ticket_generator_respects_budget(engineer, dna):
    """Testa que respeita orçamento"""
    generator = TicketGenerator(engineer, dna, seed=42)
    
    budgets = [50.0, 100.0, 200.0, 500.0]
    
    for budget in budgets:
        ticket = generator.generate_ticket(budget=budget)
        assert ticket.total_cost <= budget


def test_ticket_serialization():
    """Testa serialização de ticket"""
    games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0, score=0.8),
        Game(numbers=list(range(2, 17)), size=15, cost=3.0, score=0.7)
    ]
    
    ticket = Ticket(
        games=games,
        total_cost=6.0,
        total_games=2,
        diversity_score=0.9,
        coverage_score=0.85
    )
    
    data = ticket.to_dict()
    
    assert "games" in data
    assert "total_cost" in data
    assert "total_games" in data
    assert "diversity_score" in data
    assert "coverage_score" in data
    assert len(data["games"]) == 2


def test_game_serialization():
    """Testa serialização de game"""
    game = Game(
        numbers=list(range(1, 16)),
        size=15,
        cost=3.0,
        score=0.85
    )
    
    data = game.to_dict()
    
    assert "numbers" in data
    assert "size" in data
    assert "cost" in data
    assert "score" in data
    assert data["size"] == 15
    assert data["cost"] == 3.0


def test_reproducibility(engineer, dna):
    """Testa reprodutibilidade com mesma seed"""
    gen1 = TicketGenerator(engineer, dna, seed=42)
    gen2 = TicketGenerator(engineer, dna, seed=42)
    
    ticket1 = gen1.generate_ticket(budget=100.0)
    ticket2 = gen2.generate_ticket(budget=100.0)
    
    # Deve gerar tickets idênticos
    assert ticket1.total_games == ticket2.total_games
    assert ticket1.total_cost == ticket2.total_cost
    
    for g1, g2 in zip(ticket1.games, ticket2.games):
        assert g1.numbers == g2.numbers


def test_different_seeds_produce_different_results(engineer, dna):
    """Testa que seeds diferentes produzem resultados diferentes"""
    gen1 = TicketGenerator(engineer, dna, seed=42)
    gen2 = TicketGenerator(engineer, dna, seed=123)
    
    ticket1 = gen1.generate_ticket(budget=100.0)
    ticket2 = gen2.generate_ticket(budget=100.0)
    
    # Deve gerar tickets diferentes
    different = False
    for g1, g2 in zip(ticket1.games, ticket2.games):
        if g1.numbers != g2.numbers:
            different = True
            break
    
    assert different
