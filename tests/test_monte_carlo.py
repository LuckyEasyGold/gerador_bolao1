import pytest
import numpy as np
from backend.core.monte_carlo import (
    DrawSimulator, CommonRandomNumbers, PrizeEvaluator,
    ROICalculator, RiskAnalyzer, MonteCarloSimulator,
    ParallelSimulator, SimulationResult
)
from backend.core.game_generator import Game, Ticket


@pytest.fixture
def sample_game():
    """Jogo de exemplo"""
    return Game(
        numbers=list(range(1, 16)),
        size=15,
        cost=3.0
    )


@pytest.fixture
def sample_ticket():
    """Bolão de exemplo"""
    games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(11, 26)), size=15, cost=3.0)
    ]
    return Ticket(
        games=games,
        total_cost=6.0,
        total_games=2
    )


def test_draw_simulator():
    """Testa simulação de sorteio"""
    simulator = DrawSimulator(seed=42)
    
    draw = simulator.simulate_draw()
    
    assert len(draw) == 15
    assert len(set(draw)) == 15  # Sem duplicatas
    assert all(1 <= n <= 25 for n in draw)


def test_draw_simulator_reproducibility():
    """Testa reprodutibilidade com mesma seed"""
    sim1 = DrawSimulator(seed=42)
    sim2 = DrawSimulator(seed=42)
    
    draw1 = sim1.simulate_draw()
    draw2 = sim2.simulate_draw()
    
    assert np.array_equal(draw1, draw2)


def test_draw_simulator_multiple_draws():
    """Testa múltiplos sorteios"""
    simulator = DrawSimulator(seed=42)
    
    draws = simulator.simulate_draws(100)
    
    assert draws.shape == (100, 15)
    
    # Cada sorteio deve ter 15 números únicos
    for draw in draws:
        assert len(set(draw)) == 15


def test_common_random_numbers():
    """Testa CRN"""
    crn = CommonRandomNumbers(seed=42)
    
    draws1 = crn.get_draws(100)
    draws2 = crn.get_draws(100)
    
    # Deve retornar os mesmos sorteios
    assert np.array_equal(draws1, draws2)


def test_common_random_numbers_cache():
    """Testa cache do CRN"""
    crn = CommonRandomNumbers(seed=42)
    
    draws1 = crn.get_draws(100)
    assert crn.n_cached == 100
    
    # Segunda chamada deve usar cache
    draws2 = crn.get_draws(100)
    assert draws1 is draws2  # Mesma referência


def test_common_random_numbers_reset():
    """Testa reset do cache"""
    crn = CommonRandomNumbers(seed=42)
    
    crn.get_draws(100)
    assert crn.draws_cache is not None
    
    crn.reset()
    assert crn.draws_cache is None
    assert crn.n_cached == 0


def test_prize_evaluator_count_hits():
    """Testa contagem de acertos"""
    evaluator = PrizeEvaluator()
    
    game_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    draw = np.array([1, 2, 3, 4, 5, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25])
    
    hits = evaluator.count_hits(game_numbers, draw)
    
    assert hits == 5  # 5 números em comum


def test_prize_evaluator_evaluate_game():
    """Testa avaliação de prêmio"""
    evaluator = PrizeEvaluator()
    
    # Jogo com 15 acertos
    game = Game(numbers=list(range(1, 16)), size=15, cost=3.0)
    draw = np.array(list(range(1, 16)))
    
    prize = evaluator.evaluate_game(game, draw)
    
    assert prize == 1500000.0  # Prêmio de 15 acertos


def test_prize_evaluator_no_prize():
    """Testa quando não ganha"""
    evaluator = PrizeEvaluator()
    
    game = Game(numbers=list(range(1, 16)), size=15, cost=3.0)
    draw = np.array(list(range(11, 26)))  # Apenas 5 acertos
    
    prize = evaluator.evaluate_game(game, draw)
    
    assert prize == 0.0  # Sem prêmio


def test_prize_evaluator_evaluate_ticket(sample_ticket):
    """Testa avaliação de bolão"""
    evaluator = PrizeEvaluator()
    
    draw = np.array(list(range(1, 16)))
    
    total_prize, hit_dist = evaluator.evaluate_ticket(sample_ticket, draw)
    
    assert total_prize > 0
    assert isinstance(hit_dist, dict)
    assert all(k in hit_dist for k in [11, 12, 13, 14, 15])


def test_roi_calculator_calculate_roi():
    """Testa cálculo de ROI"""
    returns = np.array([10, 20, 30, 40, 50])
    cost = 20.0
    
    roi = ROICalculator.calculate_roi(returns, cost)
    
    # ROI = (30 - 20) / 20 = 0.5 (50%)
    assert roi == pytest.approx(0.5)


def test_roi_calculator_sharpe_ratio():
    """Testa cálculo de Sharpe Ratio"""
    returns = np.array([10, 20, 30, 40, 50])
    cost = 20.0
    
    sharpe = ROICalculator.calculate_sharpe_ratio(returns, cost)
    
    assert isinstance(sharpe, float)
    assert sharpe > 0


def test_roi_calculator_win_rate():
    """Testa cálculo de win rate"""
    returns = np.array([10, 25, 30, 15, 5])  # 3 acima do custo
    cost = 20.0
    
    win_rate = ROICalculator.calculate_win_rate(returns, cost)
    
    assert win_rate == 0.6  # 60%


def test_roi_calculator_percentiles():
    """Testa cálculo de percentis"""
    returns = np.array(range(1, 101))
    
    percentiles = ROICalculator.calculate_percentiles(returns)
    
    assert "p5" in percentiles
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert percentiles["p50"] == pytest.approx(50.5)


def test_risk_analyzer_var():
    """Testa cálculo de VaR"""
    returns = np.array(range(1, 101))
    
    var = RiskAnalyzer.calculate_var(returns, confidence=0.95)
    
    assert var == pytest.approx(5.95)


def test_risk_analyzer_cvar():
    """Testa cálculo de CVaR"""
    returns = np.array(range(1, 101))
    
    cvar = RiskAnalyzer.calculate_cvar(returns, confidence=0.95)
    
    assert cvar < RiskAnalyzer.calculate_var(returns, 0.95)


def test_risk_analyzer_max_drawdown():
    """Testa cálculo de max drawdown"""
    returns = np.array([10, -5, 15, -20, 30])
    
    max_dd = RiskAnalyzer.calculate_max_drawdown(returns)
    
    assert max_dd < 0  # Drawdown é negativo


def test_risk_analyzer_downside_deviation():
    """Testa cálculo de downside deviation"""
    returns = np.array([-10, -5, 0, 5, 10])
    
    downside_dev = RiskAnalyzer.calculate_downside_deviation(returns, target=0)
    
    assert downside_dev > 0


def test_monte_carlo_simulator_simulate_game(sample_game):
    """Testa simulação de jogo"""
    simulator = MonteCarloSimulator(seed=42)
    
    result = simulator.simulate_game(sample_game, n_simulations=100)
    
    assert isinstance(result, SimulationResult)
    assert result.simulations == 100
    assert result.avg_return >= 0
    assert result.roi is not None


def test_monte_carlo_simulator_simulate_ticket(sample_ticket):
    """Testa simulação de bolão"""
    simulator = MonteCarloSimulator(seed=42)
    
    result = simulator.simulate_ticket(sample_ticket, n_simulations=100)
    
    assert isinstance(result, SimulationResult)
    assert result.simulations == 100
    assert result.total_games == 2


def test_monte_carlo_simulator_reproducibility(sample_ticket):
    """Testa reprodutibilidade"""
    sim1 = MonteCarloSimulator(seed=42, use_crn=True)
    sim2 = MonteCarloSimulator(seed=42, use_crn=True)
    
    result1 = sim1.simulate_ticket(sample_ticket, n_simulations=100)
    result2 = sim2.simulate_ticket(sample_ticket, n_simulations=100)
    
    assert result1.avg_return == result2.avg_return
    assert result1.std_return == result2.std_return


def test_monte_carlo_simulator_compare_tickets(sample_ticket):
    """Testa comparação de bolões"""
    simulator = MonteCarloSimulator(seed=42, use_crn=True)
    
    # Cria segundo ticket
    games2 = [
        Game(numbers=list(range(5, 20)), size=15, cost=3.0),
        Game(numbers=list(range(10, 25)), size=15, cost=3.0)
    ]
    ticket2 = Ticket(games=games2, total_cost=6.0, total_games=2)
    
    results = simulator.compare_tickets([sample_ticket, ticket2], n_simulations=100)
    
    assert len(results) == 2
    assert all(isinstance(r, SimulationResult) for r in results)


def test_monte_carlo_simulator_risk_metrics(sample_ticket):
    """Testa cálculo de métricas de risco"""
    simulator = MonteCarloSimulator(seed=42)
    
    risk_metrics = simulator.calculate_risk_metrics(sample_ticket, n_simulations=100)
    
    assert "var_95" in risk_metrics
    assert "cvar_95" in risk_metrics
    assert "max_drawdown" in risk_metrics
    assert "downside_deviation" in risk_metrics
    assert "p50" in risk_metrics


def test_simulation_result_serialization():
    """Testa serialização de resultado"""
    result = SimulationResult(
        simulations=1000,
        avg_return=100.0,
        std_return=50.0,
        median_return=90.0,
        min_return=0.0,
        max_return=500.0,
        win_rate=0.3,
        roi=0.5,
        sharpe_ratio=1.2,
        max_prize=500.0,
        prize_distribution={0: 700, 1: 200, 10: 80, 100: 15, 1000: 4, 10000: 1},
        hit_distribution={11: 100, 12: 50, 13: 20, 14: 5, 15: 1}
    )
    
    data = result.to_dict()
    
    assert "simulations" in data
    assert "avg_return" in data
    assert "roi" in data
    assert "prize_distribution" in data
    assert data["simulations"] == 1000


def test_parallel_simulator(sample_ticket):
    """Testa simulador paralelo"""
    simulator = ParallelSimulator(n_workers=2, seed=42)
    
    result = simulator.simulate_ticket_parallel(sample_ticket, n_simulations=100)
    
    assert isinstance(result, SimulationResult)
    assert result.simulations == 100


def test_parallel_vs_sequential(sample_ticket):
    """Compara resultados paralelo vs sequencial"""
    # Sequencial
    seq_sim = MonteCarloSimulator(seed=42, use_crn=False)
    seq_result = seq_sim.simulate_ticket(sample_ticket, n_simulations=100)
    
    # Paralelo
    par_sim = ParallelSimulator(n_workers=2, seed=42)
    par_result = par_sim.simulate_ticket_parallel(sample_ticket, n_simulations=100)
    
    # Resultados devem ser similares (não idênticos devido a divisão)
    assert abs(seq_result.avg_return - par_result.avg_return) < 50.0


def test_prize_distribution_calculation():
    """Testa cálculo de distribuição de prêmios"""
    simulator = MonteCarloSimulator(seed=42)
    
    returns = np.array([0, 5, 15, 150, 1500, 15000])
    
    dist = simulator._calculate_prize_distribution(returns)
    
    assert dist[0] == 1  # 1 sem prêmio
    assert dist[1] == 1  # 1 entre 1-10
    assert dist[10] == 1  # 1 entre 10-100
    assert dist[100] == 1  # 1 entre 100-1000
    assert dist[1000] == 1  # 1 entre 1000-10000
    assert dist[10000] == 1  # 1 acima de 10000


def test_hit_distribution_accumulation(sample_ticket):
    """Testa acumulação de distribuição de acertos"""
    simulator = MonteCarloSimulator(seed=42)
    
    result = simulator.simulate_ticket(sample_ticket, n_simulations=100)
    
    # Deve ter contagem para cada faixa de acertos
    assert all(k in result.hit_distribution for k in [11, 12, 13, 14, 15])
    assert sum(result.hit_distribution.values()) >= 0


def test_different_seeds_produce_different_results(sample_ticket):
    """Testa que seeds diferentes produzem resultados diferentes"""
    sim1 = MonteCarloSimulator(seed=42, use_crn=False)
    sim2 = MonteCarloSimulator(seed=123, use_crn=False)
    
    result1 = sim1.simulate_ticket(sample_ticket, n_simulations=100)
    result2 = sim2.simulate_ticket(sample_ticket, n_simulations=100)
    
    # Resultados devem ser diferentes
    assert result1.avg_return != result2.avg_return
