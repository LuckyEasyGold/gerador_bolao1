"""
Simulador Monte Carlo para Lotofácil
Avalia estatisticamente bolões através de simulação de sorteios
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from backend.core.game_generator import Game, Ticket
from backend.config import get_settings

settings = get_settings()


@dataclass
class SimulationResult:
    """Resultado de uma simulação"""
    simulations: int
    avg_return: float
    std_return: float
    median_return: float
    min_return: float
    max_return: float
    win_rate: float
    roi: float
    sharpe_ratio: float
    max_prize: float
    prize_distribution: Dict[int, int]
    hit_distribution: Dict[int, int]
    
    def to_dict(self) -> Dict:
        return {
            "simulations": self.simulations,
            "avg_return": self.avg_return,
            "std_return": self.std_return,
            "median_return": self.median_return,
            "min_return": self.min_return,
            "max_return": self.max_return,
            "win_rate": self.win_rate,
            "roi": self.roi,
            "sharpe_ratio": self.sharpe_ratio,
            "max_prize": self.max_prize,
            "prize_distribution": self.prize_distribution,
            "hit_distribution": self.hit_distribution
        }


class DrawSimulator:
    """Simula sorteios da Lotofácil"""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)
    
    def simulate_draw(self) -> np.ndarray:
        """
        Simula um sorteio da Lotofácil
        
        Returns:
            Array com 15 números sorteados (1-25)
        """
        return self.rng.choice(
            range(1, settings.total_numbers + 1),
            size=settings.numbers_per_draw,
            replace=False
        )
    
    def simulate_draws(self, n_draws: int) -> np.ndarray:
        """
        Simula múltiplos sorteios
        
        Args:
            n_draws: Número de sorteios
        
        Returns:
            Array (n_draws, 15) com sorteios
        """
        draws = np.zeros((n_draws, settings.numbers_per_draw), dtype=int)
        for i in range(n_draws):
            draws[i] = self.simulate_draw()
        return draws


class CommonRandomNumbers:
    """
    Implementa técnica Common Random Numbers (CRN)
    Reduz variância ao comparar estratégias
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.draws_cache: Optional[np.ndarray] = None
        self.n_cached: int = 0
    
    def get_draws(self, n_draws: int) -> np.ndarray:
        """
        Retorna sorteios usando mesma seed
        
        Cacheia para reutilização
        """
        if self.draws_cache is None or self.n_cached != n_draws:
            simulator = DrawSimulator(seed=self.seed)
            self.draws_cache = simulator.simulate_draws(n_draws)
            self.n_cached = n_draws
        
        return self.draws_cache
    
    def reset(self):
        """Limpa cache"""
        self.draws_cache = None
        self.n_cached = 0


class PrizeEvaluator:
    """Avalia premiações de jogos"""
    
    def __init__(self):
        # Valores aproximados de prêmios
        self.prizes = {
            15: settings.prize_15,  # 15 acertos
            14: settings.prize_14,  # 14 acertos
            13: settings.prize_13,  # 13 acertos
            12: settings.prize_12,  # 12 acertos
            11: settings.prize_11   # 11 acertos
        }
    
    def count_hits(self, game_numbers: List[int], draw: np.ndarray) -> int:
        """
        Conta acertos de um jogo em um sorteio
        
        Args:
            game_numbers: Números do jogo
            draw: Números sorteados
        
        Returns:
            Quantidade de acertos
        """
        game_set = set(game_numbers)
        draw_set = set(draw)
        return len(game_set & draw_set)
    
    def evaluate_game(self, game: Game, draw: np.ndarray) -> float:
        """
        Avalia prêmio de um jogo em um sorteio
        
        Returns:
            Valor do prêmio (0 se não ganhou)
        """
        hits = self.count_hits(game.numbers, draw)
        return self.prizes.get(hits, 0.0)
    
    def evaluate_ticket(self, ticket: Ticket, draw: np.ndarray) -> Tuple[float, Dict[int, int]]:
        """
        Avalia prêmio total de um bolão em um sorteio
        
        Returns:
            (total_prize, hit_distribution)
        """
        total_prize = 0.0
        hit_distribution = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
        
        for game in ticket.games:
            hits = self.count_hits(game.numbers, draw)
            prize = self.prizes.get(hits, 0.0)
            total_prize += prize
            
            if hits >= 11:
                hit_distribution[hits] += 1
        
        return total_prize, hit_distribution


class ROICalculator:
    """Calcula métricas de retorno sobre investimento"""
    
    @staticmethod
    def calculate_roi(returns: np.ndarray, cost: float) -> float:
        """
        Calcula ROI médio
        
        ROI = (Retorno Médio - Custo) / Custo
        """
        if len(returns) == 0:
            return 0.0
        avg_return = returns.mean()
        return (avg_return - cost) / cost if cost > 0 else 0.0
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, cost: float, 
                               risk_free_rate: float = 0.0) -> float:
        """
        Calcula Sharpe Ratio
        
        Sharpe = (Retorno Médio - Taxa Livre de Risco) / Desvio Padrão
        """
        if len(returns) == 0:
            return 0.0
        avg_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return 0.0
        
        excess_return = avg_return - risk_free_rate
        return excess_return / std_return
    
    @staticmethod
    def calculate_win_rate(returns: np.ndarray, cost: float) -> float:
        """
        Calcula taxa de vitória (% de sorteios com lucro)
        """
        if len(returns) == 0:
            return 0.0
        wins = np.sum(returns > cost)
        return wins / len(returns) if len(returns) > 0 else 0.0
    
    @staticmethod
    def calculate_percentiles(returns: np.ndarray) -> Dict[str, float]:
        """Calcula percentis de retorno"""
        if len(returns) == 0:
            return {
                "p5": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 0.0,
                "p95": 0.0
            }
        return {
            "p5": np.percentile(returns, 5),
            "p25": np.percentile(returns, 25),
            "p50": np.percentile(returns, 50),
            "p75": np.percentile(returns, 75),
            "p95": np.percentile(returns, 95)
        }


class RiskAnalyzer:
    """Analisa risco de estratégias"""
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calcula Value at Risk (VaR)
        
        VaR = perda máxima esperada com X% de confiança
        """
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    @staticmethod
    def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calcula Conditional Value at Risk (CVaR)
        
        CVaR = perda média além do VaR
        """
        if len(returns) == 0:
            return 0.0
        var = RiskAnalyzer.calculate_var(returns, confidence)
        tail_losses = returns[returns <= var]
        return tail_losses.mean() if len(tail_losses) > 0 else var
    
    @staticmethod
    def calculate_max_drawdown(returns: np.ndarray) -> float:
        """
        Calcula máximo drawdown
        
        Maior queda de pico a vale
        """
        if len(returns) == 0:
            return 0.0
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        return drawdown.min()
    
    @staticmethod
    def calculate_downside_deviation(returns: np.ndarray, 
                                     target: float = 0.0) -> float:
        """
        Calcula desvio negativo (downside deviation)
        
        Considera apenas retornos abaixo do target
        """
        downside_returns = returns[returns < target]
        if len(downside_returns) == 0:
            return 0.0
        return np.sqrt(np.mean((downside_returns - target) ** 2))


class MonteCarloSimulator:
    """Simulador Monte Carlo completo"""
    
    def __init__(self, seed: Optional[int] = None, use_crn: bool = True):
        self.seed = seed
        self.use_crn = use_crn
        self.crn = CommonRandomNumbers(seed) if use_crn else None
        self.draw_simulator = DrawSimulator(seed)
        self.prize_evaluator = PrizeEvaluator()
        self.roi_calculator = ROICalculator()
        self.risk_analyzer = RiskAnalyzer()
    
    def simulate_ticket(self, ticket: Ticket, 
                       n_simulations: int = 10000) -> SimulationResult:
        """
        Simula bolão completo
        
        Args:
            ticket: Bolão a simular
            n_simulations: Número de simulações
        
        Returns:
            SimulationResult com métricas
        """
        # Gera ou recupera sorteios
        if self.use_crn and self.crn:
            draws = self.crn.get_draws(n_simulations)
        else:
            draws = self.draw_simulator.simulate_draws(n_simulations)
        
        # Simula cada sorteio
        returns = np.zeros(n_simulations)
        all_hit_distribution = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
        max_prize = 0.0
        
        for i in range(n_simulations):
            prize, hit_dist = self.prize_evaluator.evaluate_ticket(
                ticket, draws[i]
            )
            returns[i] = prize
            max_prize = max(max_prize, prize)
            
            # Acumula distribuição de acertos
            for hits, count in hit_dist.items():
                all_hit_distribution[hits] += count
        
        # Calcula métricas
        cost = ticket.total_cost
        
        roi = self.roi_calculator.calculate_roi(returns, cost)
        sharpe = self.roi_calculator.calculate_sharpe_ratio(returns, cost)
        win_rate = self.roi_calculator.calculate_win_rate(returns, cost)
        
        # Distribuição de prêmios
        prize_distribution = self._calculate_prize_distribution(returns)
        
        # Validações para arrays vazios
        if len(returns) == 0:
            return SimulationResult(
                simulations=n_simulations,
                avg_return=0.0,
                std_return=0.0,
                median_return=0.0,
                min_return=0.0,
                max_return=0.0,
                win_rate=0.0,
                roi=0.0,
                sharpe_ratio=0.0,
                max_prize=0.0,
                prize_distribution=prize_distribution,
                hit_distribution=all_hit_distribution
            )
        
        return SimulationResult(
            simulations=n_simulations,
            avg_return=float(returns.mean()),
            std_return=float(returns.std()),
            median_return=float(np.median(returns)),
            min_return=float(returns.min()),
            max_return=float(returns.max()),
            win_rate=float(win_rate),
            roi=float(roi),
            sharpe_ratio=float(sharpe),
            max_prize=float(max_prize),
            prize_distribution=prize_distribution,
            hit_distribution=all_hit_distribution
        )
    
    def simulate_game(self, game: Game, 
                     n_simulations: int = 10000) -> SimulationResult:
        """Simula jogo individual"""
        # Cria ticket temporário com um jogo
        ticket = Ticket(
            games=[game],
            total_cost=game.cost,
            total_games=1
        )
        return self.simulate_ticket(ticket, n_simulations)
    
    def compare_tickets(self, tickets: List[Ticket], 
                       n_simulations: int = 10000) -> List[SimulationResult]:
        """
        Compara múltiplos bolões usando CRN
        
        Garante que todos são avaliados nos mesmos sorteios
        """
        # Força uso de CRN
        if not self.use_crn:
            self.crn = CommonRandomNumbers(self.seed or 42)
            self.use_crn = True
        
        results = []
        for ticket in tickets:
            result = self.simulate_ticket(ticket, n_simulations)
            results.append(result)
        
        return results
    
    def _calculate_prize_distribution(self, returns: np.ndarray) -> Dict[int, int]:
        """Calcula distribuição de faixas de prêmio"""
        distribution = {
            0: 0,      # Sem prêmio
            1: 0,      # R$ 1-10
            10: 0,     # R$ 10-100
            100: 0,    # R$ 100-1000
            1000: 0,   # R$ 1000-10000
            10000: 0   # R$ 10000+
        }
        
        for ret in returns:
            if ret == 0:
                distribution[0] += 1
            elif ret < 10:
                distribution[1] += 1
            elif ret < 100:
                distribution[10] += 1
            elif ret < 1000:
                distribution[100] += 1
            elif ret < 10000:
                distribution[1000] += 1
            else:
                distribution[10000] += 1
        
        return distribution
    
    def calculate_risk_metrics(self, ticket: Ticket, 
                               n_simulations: int = 10000) -> Dict[str, float]:
        """
        Calcula métricas de risco detalhadas
        """
        # Simula
        if self.use_crn and self.crn:
            draws = self.crn.get_draws(n_simulations)
        else:
            draws = self.draw_simulator.simulate_draws(n_simulations)
        
        returns = np.zeros(n_simulations)
        for i in range(n_simulations):
            prize, _ = self.prize_evaluator.evaluate_ticket(ticket, draws[i])
            returns[i] = prize
        
        # Calcula métricas de risco
        var_95 = self.risk_analyzer.calculate_var(returns, 0.95)
        cvar_95 = self.risk_analyzer.calculate_cvar(returns, 0.95)
        max_dd = self.risk_analyzer.calculate_max_drawdown(returns)
        downside_dev = self.risk_analyzer.calculate_downside_deviation(
            returns, target=ticket.total_cost
        )
        
        percentiles = self.roi_calculator.calculate_percentiles(returns)
        
        return {
            "var_95": float(var_95),
            "cvar_95": float(cvar_95),
            "max_drawdown": float(max_dd),
            "downside_deviation": float(downside_dev),
            **percentiles
        }


class ParallelSimulator:
    """Simulador paralelo usando multiprocessing"""
    
    def __init__(self, n_workers: Optional[int] = None, seed: int = 42):
        self.n_workers = n_workers or settings.max_workers
        self.seed = seed
    
    def simulate_ticket_parallel(self, ticket: Ticket, 
                                 n_simulations: int = 10000) -> SimulationResult:
        """
        Simula bolão usando múltiplos processos
        
        Divide simulações entre workers
        """
        sims_per_worker = n_simulations // self.n_workers
        
        # Cria seeds diferentes para cada worker
        seeds = [self.seed + i for i in range(self.n_workers)]
        
        # Executa em paralelo
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            futures = [
                executor.submit(
                    self._simulate_chunk,
                    ticket,
                    sims_per_worker,
                    seed
                )
                for seed in seeds
            ]
            
            results = [f.result() for f in futures]
        
        # Agrega resultados
        return self._aggregate_results(results, ticket.total_cost)
    
    @staticmethod
    def _simulate_chunk(ticket: Ticket, n_sims: int, 
                       seed: int) -> Tuple[np.ndarray, Dict[int, int]]:
        """Simula chunk de simulações (executado em worker)"""
        simulator = MonteCarloSimulator(seed=seed, use_crn=False)
        
        draws = simulator.draw_simulator.simulate_draws(n_sims)
        returns = np.zeros(n_sims)
        hit_dist = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
        
        for i in range(n_sims):
            prize, hits = simulator.prize_evaluator.evaluate_ticket(
                ticket, draws[i]
            )
            returns[i] = prize
            for h, c in hits.items():
                hit_dist[h] += c
        
        return returns, hit_dist
    
    def _aggregate_results(self, results: List[Tuple[np.ndarray, Dict[int, int]]], 
                          cost: float) -> SimulationResult:
        """Agrega resultados de múltiplos workers"""
        # Concatena returns
        all_returns = np.concatenate([r[0] for r in results])
        
        # Agrega hit distributions
        total_hits = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
        for _, hits in results:
            for h, c in hits.items():
                total_hits[h] += c
        
        # Calcula métricas
        roi_calc = ROICalculator()
        
        roi = roi_calc.calculate_roi(all_returns, cost)
        sharpe = roi_calc.calculate_sharpe_ratio(all_returns, cost)
        win_rate = roi_calc.calculate_win_rate(all_returns, cost)
        
        simulator = MonteCarloSimulator()
        prize_dist = simulator._calculate_prize_distribution(all_returns)
        
        return SimulationResult(
            simulations=len(all_returns),
            avg_return=float(all_returns.mean()),
            std_return=float(all_returns.std()),
            median_return=float(np.median(all_returns)),
            min_return=float(all_returns.min()),
            max_return=float(all_returns.max()),
            win_rate=float(win_rate),
            roi=float(roi),
            sharpe_ratio=float(sharpe),
            max_prize=float(all_returns.max()),
            prize_distribution=prize_dist,
            hit_distribution=total_hits
        )
