"""
Motor de Geração de Jogos para Lotofácil
Gera bolões otimizados usando features históricas e DNA evolutivo
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from backend.models.dna import DNA
from backend.core.feature_engineering import FeatureEngineer
from backend.config import get_settings

settings = get_settings()


@dataclass
class Game:
    """Representa um jogo individual"""
    numbers: List[int]
    size: int
    cost: float
    score: float = 0.0
    
    def __post_init__(self):
        self.numbers = sorted(self.numbers)
    
    def to_dict(self) -> Dict:
        return {
            "numbers": self.numbers,
            "size": self.size,
            "cost": self.cost,
            "score": self.score
        }


@dataclass
class Ticket:
    """Representa um bolão completo"""
    games: List[Game]
    total_cost: float
    total_games: int
    diversity_score: float = 0.0
    coverage_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "games": [g.to_dict() for g in self.games],
            "total_cost": self.total_cost,
            "total_games": self.total_games,
            "diversity_score": self.diversity_score,
            "coverage_score": self.coverage_score
        }


class PoolSelector:
    """Seleciona pool de dezenas usando features e DNA"""
    
    def __init__(self, engineer: FeatureEngineer, dna: DNA):
        self.engineer = engineer
        self.dna = dna
        self.rng = np.random.default_rng()
    
    def select_pool(self, pool_size: Optional[int] = None) -> List[int]:
        """
        Seleciona pool de dezenas usando estratégia gulosa
        
        Args:
            pool_size: Tamanho do pool (usa DNA se None)
        
        Returns:
            Lista de números selecionados
        """
        if pool_size is None:
            pool_size = self.dna.genes.pool_size
        
        # Calcula scores usando pesos do DNA
        weights = {
            'wf': self.dna.genes.wf,
            'wa': self.dna.genes.wa,
            'wr': self.dna.genes.wr
        }
        
        scores = self.engineer.compute_all_scores(weights)
        
        # Adiciona componente de afinidade
        if self.dna.genes.wc_aff > 0:
            scores = self._apply_affinity_boost(scores)
        
        # Seleciona top pool_size números
        top_indices = np.argsort(scores)[-pool_size:]
        pool = [idx + 1 for idx in top_indices]
        
        return sorted(pool)
    
    def _apply_affinity_boost(self, scores: np.ndarray) -> np.ndarray:
        """Aplica boost baseado em afinidade"""
        boosted = scores.copy()
        
        # Para cada número, adiciona score baseado em afinidade com outros números de alto score
        for i in range(len(scores)):
            num = i + 1
            companions = self.engineer.affinity_matrix.get_best_companions(num, k=5)
            
            # Boost proporcional à afinidade com números de alto score
            boost = 0.0
            for comp_num, affinity in companions:
                comp_score = scores[comp_num - 1]
                boost += affinity * comp_score
            
            boosted[i] += self.dna.genes.wc_aff * boost / 5
        
        return boosted


class SoftmaxSampler:
    """Amostragem de números usando softmax com temperatura"""
    
    def __init__(self, dna: DNA, seed: Optional[int] = None):
        self.dna = dna
        self.rng = np.random.default_rng(seed)
    
    def sample(self, pool: List[int], scores: np.ndarray, 
               n_samples: int, temperature: Optional[float] = None) -> List[int]:
        """
        Amostra números do pool usando softmax
        
        Args:
            pool: Pool de números disponíveis
            scores: Scores dos números
            n_samples: Quantos números amostrar
            temperature: Temperatura (usa DNA se None)
        
        Returns:
            Lista de números amostrados
        """
        if temperature is None:
            temperature = self._compute_temperature()
        
        # Garante que n_samples não excede o tamanho do pool
        n_samples = min(n_samples, len(pool))
        
        # Garante que o pool não está vazio
        if not pool:
            return []
        
        # Extrai scores do pool
        pool_scores = np.array([scores[num - 1] for num in pool])
        
        # Aplica softmax com temperatura
        probs = self._softmax(pool_scores, temperature)
        
        # Amostra sem reposição
        sampled_indices = self.rng.choice(
            len(pool), 
            size=n_samples, 
            replace=False, 
            p=probs
        )
        
        return sorted([pool[i] for i in sampled_indices])
    
    def _compute_temperature(self) -> float:
        """Calcula temperatura dinâmica baseada no DNA"""
        # T = T_base * (1 + kappa * noise)
        noise = self.rng.normal(0, 1)
        temp = self.dna.genes.T_base * (1 + self.dna.genes.kappa * noise)
        return max(0.1, temp)  # Garante temperatura mínima
    
    def _softmax(self, scores: np.ndarray, temperature: float) -> np.ndarray:
        """Calcula softmax com temperatura"""
        # Evita overflow/underflow
        exp_scores = np.exp((scores - np.max(scores)) / temperature)
        sum_exp = exp_scores.sum()
        if sum_exp == 0:
            # Retorna distribuição uniforme se todos os scores forem zero
            return np.ones(len(scores)) / len(scores)
        return exp_scores / sum_exp


class StructuralScorer:
    """Calcula score estrutural de um jogo"""
    
    def __init__(self, dna: DNA):
        self.dna = dna
    
    def score_game(self, numbers: List[int]) -> float:
        """
        Calcula score estrutural de um jogo
        
        Considera:
        - Paridade (pares vs ímpares)
        - Distribuição por linhas/colunas
        - Sequências consecutivas
        - Overlap com outros jogos
        """
        score = 0.0
        
        # 1. Paridade
        if self.dna.genes.wp > 0:
            score += self.dna.genes.wp * self._score_parity(numbers)
        
        # 2. Linhas/Colunas (cartela 5x5)
        if self.dna.genes.wl > 0:
            score += self.dna.genes.wl * self._score_distribution(numbers)
        
        # 3. Sequências
        if self.dna.genes.ws > 0:
            score += self.dna.genes.ws * self._score_sequences(numbers)
        
        return score
    
    def _score_parity(self, numbers: List[int]) -> float:
        """Score baseado em paridade (ideal: 7-8 pares, 7-8 ímpares)"""
        evens = sum(1 for n in numbers if n % 2 == 0)
        odds = len(numbers) - evens
        
        # Ideal: balanceado
        ideal_evens = len(numbers) / 2
        deviation = abs(evens - ideal_evens)
        
        # Score: 1.0 se balanceado, 0.0 se muito desbalanceado
        max_deviation = len(numbers) / 2
        return 1.0 - (deviation / max_deviation)
    
    def _score_distribution(self, numbers: List[int]) -> float:
        """Score baseado em distribuição na cartela 5x5"""
        # Cartela Lotofácil: 5 linhas x 5 colunas
        # Linha 1: 1-5, Linha 2: 6-10, etc.
        
        lines = [0] * 5
        for num in numbers:
            line = (num - 1) // 5
            lines[line] += 1
        
        # Ideal: distribuição uniforme (3 por linha)
        ideal_per_line = len(numbers) / 5
        deviations = [abs(count - ideal_per_line) for count in lines]
        avg_deviation = sum(deviations) / 5
        
        # Score: 1.0 se uniforme, 0.0 se concentrado
        max_deviation = len(numbers)
        return 1.0 - (avg_deviation / max_deviation)
    
    def _score_sequences(self, numbers: List[int]) -> float:
        """Score baseado em sequências consecutivas"""
        # Penaliza muitas sequências longas
        sorted_nums = sorted(numbers)
        
        sequences = []
        current_seq = 1
        
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i-1] + 1:
                current_seq += 1
            else:
                if current_seq > 1:
                    sequences.append(current_seq)
                current_seq = 1
        
        if current_seq > 1:
            sequences.append(current_seq)
        
        # Penaliza sequências longas (> 3)
        penalty = sum(max(0, seq - 3) for seq in sequences)
        max_penalty = len(numbers)
        
        return 1.0 - (penalty / max_penalty)


class GameGenerator:
    """Gera jogos individuais"""
    
    def __init__(self, engineer: FeatureEngineer, dna: DNA, seed: Optional[int] = None):
        self.engineer = engineer
        self.dna = dna
        self.pool_selector = PoolSelector(engineer, dna)
        self.sampler = SoftmaxSampler(dna, seed)
        self.scorer = StructuralScorer(dna)
        self.rng = np.random.default_rng(seed)
    
    def generate_game(self, size: int, pool: Optional[List[int]] = None) -> Game:
        """
        Gera um jogo de tamanho especificado
        
        Args:
            size: Tamanho do jogo (15, 16, 17, etc.)
            pool: Pool de números (gera novo se None)
        
        Returns:
            Game gerado
        """
        if pool is None:
            pool = self.pool_selector.select_pool()
        
        # Garante que o pool não está vazio
        if not pool:
            # Retorna jogo aleatório como fallback
            numbers = sorted(self.rng.choice(range(1, settings.total_numbers + 1), size=size, replace=False))
            return Game(
                numbers=numbers,
                size=size,
                cost=self._get_cost(size)
            )
        
        # Calcula scores
        weights = {
            'wf': self.dna.genes.wf,
            'wa': self.dna.genes.wa,
            'wr': self.dna.genes.wr
        }
        scores = self.engineer.compute_all_scores(weights)
        
        # Gera múltiplos candidatos
        candidates = []
        # Garante pelo menos 1 candidato
        num_candidates = max(1, self.dna.genes.candidates_per_game)
        for _ in range(num_candidates):
            numbers = self.sampler.sample(pool, scores, size)
            game = Game(
                numbers=numbers,
                size=size,
                cost=self._get_cost(size)
            )
            game.score = self.scorer.score_game(numbers)
            candidates.append(game)
        
        # Seleciona melhor candidato
        best_game = max(candidates, key=lambda g: g.score)
        
        # Refinamento local
        best_game = self._refine_game(best_game, pool, scores)
        
        return best_game
    
    def _refine_game(self, game: Game, pool: List[int], scores: np.ndarray) -> Game:
        """Refinamento local via busca hill-climbing"""
        current = game
        
        for _ in range(self.dna.genes.refine_iterations):
            # Tenta trocar um número
            candidate = self._mutate_game(current, pool, scores)
            
            if candidate.score > current.score:
                current = candidate
            else:
                # Aceita piora com pequena probabilidade (simulated annealing)
                if self.rng.random() < 0.01:
                    current = candidate
        
        return current
    
    def _mutate_game(self, game: Game, pool: List[int], scores: np.ndarray) -> Game:
        """Cria variação do jogo trocando um número"""
        numbers = game.numbers.copy()
        
        # Remove um número aleatório
        idx_remove = self.rng.integers(0, len(numbers))
        removed = numbers.pop(idx_remove)
        
        # Adiciona outro do pool
        available = [n for n in pool if n not in numbers]
        if not available:
            numbers.append(removed)
            return game
        
        # Escolhe baseado em scores
        available_scores = np.array([scores[n - 1] for n in available])
        
        # Normaliza scores para garantir que sejam não-negativos
        min_score = available_scores.min()
        if min_score < 0:
            available_scores = available_scores - min_score
        
        total_score = available_scores.sum()
        if total_score == 0 or np.isnan(total_score) or np.isinf(total_score):
            # Distribuição uniforme se todos os scores forem zero ou inválidos
            probs = np.ones(len(available)) / len(available)
        else:
            probs = available_scores / total_score
            # Garante que probs soma 1.0 e não tem valores negativos
            probs = np.abs(probs)
            probs = probs / probs.sum()
        
        new_num = self.rng.choice(available, p=probs)
        numbers.append(new_num)
        
        new_game = Game(
            numbers=sorted(numbers),
            size=game.size,
            cost=game.cost
        )
        new_game.score = self.scorer.score_game(new_game.numbers)
        
        return new_game
    
    def _get_cost(self, size: int) -> float:
        """Retorna custo de um jogo baseado no tamanho"""
        costs = {
            15: settings.cost_15,
            16: settings.cost_16,
            17: settings.cost_17,
            18: settings.cost_18,
            19: settings.cost_19,
            20: settings.cost_20
        }
        return costs.get(size, 0.0)


class DiversityOptimizer:
    """Otimiza diversidade global do bolão"""
    
    def __init__(self, dna: DNA):
        self.dna = dna
    
    def optimize_ticket(self, games: List[Game]) -> Ticket:
        """
        Otimiza diversidade global do bolão
        
        Calcula:
        - Cobertura: quantos números únicos são cobertos
        - Diversidade: quão diferentes são os jogos entre si
        - Overlap: sobreposição entre jogos
        """
        total_cost = sum(g.cost for g in games)
        
        # Calcula métricas
        coverage = self._calculate_coverage(games)
        diversity = self._calculate_diversity(games)
        overlap = self._calculate_overlap(games)
        
        # Score global
        diversity_score = (
            self.dna.genes.wcov * coverage +
            self.dna.genes.wd * diversity -
            self.dna.genes.woverlap * overlap
        )
        
        return Ticket(
            games=games,
            total_cost=total_cost,
            total_games=len(games),
            diversity_score=diversity_score,
            coverage_score=coverage
        )
    
    def _calculate_coverage(self, games: List[Game]) -> float:
        """Calcula cobertura de números únicos"""
        all_numbers = set()
        for game in games:
            all_numbers.update(game.numbers)
        
        # Score: proporção de números cobertos (0-1)
        return len(all_numbers) / settings.total_numbers
    
    def _calculate_diversity(self, games: List[Game]) -> float:
        """Calcula diversidade entre jogos"""
        if len(games) < 2:
            return 1.0
        
        # Calcula distância média entre todos os pares de jogos
        total_distance = 0.0
        count = 0
        
        for i in range(len(games)):
            for j in range(i + 1, len(games)):
                # Distância de Jaccard
                set_i = set(games[i].numbers)
                set_j = set(games[j].numbers)
                
                intersection = len(set_i & set_j)
                union = len(set_i | set_j)
                
                distance = 1.0 - (intersection / union if union > 0 else 0)
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    def _calculate_overlap(self, games: List[Game]) -> float:
        """Calcula overlap médio entre jogos"""
        if len(games) < 2:
            return 0.0
        
        total_overlap = 0.0
        count = 0
        
        for i in range(len(games)):
            for j in range(i + 1, len(games)):
                set_i = set(games[i].numbers)
                set_j = set(games[j].numbers)
                
                overlap = len(set_i & set_j) / min(len(set_i), len(set_j))
                total_overlap += overlap
                count += 1
        
        return total_overlap / count if count > 0 else 0.0


class TicketGenerator:
    """Gera bolões completos respeitando orçamento"""
    
    def __init__(self, engineer: FeatureEngineer, dna: DNA, seed: Optional[int] = None):
        self.engineer = engineer
        self.dna = dna
        self.game_generator = GameGenerator(engineer, dna, seed)
        self.diversity_optimizer = DiversityOptimizer(dna)
        self.rng = np.random.default_rng(seed)
    
    def generate_ticket(self, budget: float) -> Ticket:
        """
        Gera bolão completo respeitando orçamento
        
        Args:
            budget: Orçamento em reais
        
        Returns:
            Ticket otimizado
        """
        # Garante orçamento mínimo
        if budget < settings.cost_15:
            budget = settings.cost_15
        
        # Seleciona pool uma vez
        pool = self.game_generator.pool_selector.select_pool()
        
        # Garante que o pool não está vazio
        if not pool:
            pool = list(range(1, settings.total_numbers + 1))
        
        # Distribui orçamento entre tamanhos de jogo
        distribution = self._distribute_budget(budget)
        
        # Verifica se há jogos para gerar
        total_games = sum(distribution.values())
        if total_games == 0:
            # Força pelo menos 1 jogo de 15 números
            distribution = {15: 1, 16: 0, 17: 0}
        
        # Gera jogos
        games = []
        for size, count in distribution.items():
            for _ in range(count):
                game = self.game_generator.generate_game(size, pool)
                games.append(game)
        
        # Otimiza diversidade
        ticket = self.diversity_optimizer.optimize_ticket(games)
        
        return ticket
    
    def _distribute_budget(self, budget: float) -> Dict[int, int]:
        """
        Distribui orçamento entre tamanhos de jogo usando pesos do DNA
        
        Returns:
            Dict {tamanho: quantidade}
        """
        # Garante orçamento mínimo
        if budget < settings.cost_15:
            budget = settings.cost_15
        
        # Pesos do DNA
        w15 = self.dna.genes.w15
        w16 = self.dna.genes.w16
        w17 = self.dna.genes.w17
        
        # Normaliza pesos
        total_weight = w15 + w16 + w17
        if total_weight == 0:
            w15 = w16 = w17 = 1/3
        else:
            w15 /= total_weight
            w16 /= total_weight
            w17 /= total_weight
        
        # Distribui orçamento
        budget_15 = budget * w15
        budget_16 = budget * w16
        budget_17 = budget * w17
        
        # Calcula quantidades (garante pelo menos 1 jogo)
        count_15 = max(1, int(budget_15 / settings.cost_15))
        count_16 = max(0, int(budget_16 / settings.cost_16))
        count_17 = max(0, int(budget_17 / settings.cost_17))
        
        # Ajusta para usar todo o orçamento
        remaining = budget - (
            count_15 * settings.cost_15 +
            count_16 * settings.cost_16 +
            count_17 * settings.cost_17
        )
        
        # Adiciona jogos de 15 com o restante
        if remaining >= settings.cost_15:
            count_15 += int(remaining / settings.cost_15)
        
        return {15: count_15, 16: count_16, 17: count_17}
