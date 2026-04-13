"""
Feature Engineering para Lotofácil
Calcula features históricas para alimentar o algoritmo genético
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from backend.models.contest import Contest
from backend.config import get_settings

settings = get_settings()


class FrequencyCalculator:
    """Calcula frequências históricas de cada número"""
    
    def __init__(self):
        self.frequencies: Dict[int, int] = defaultdict(int)
        self.total_contests: int = 0
    
    def update(self, contests: List[Contest]) -> None:
        """Atualiza frequências com novos concursos"""
        for contest in contests:
            self.total_contests += 1
            for number in contest.numbers:
                self.frequencies[number] += 1
    
    def get_frequency(self, number: int) -> float:
        """Retorna frequência relativa de um número (0-1)"""
        if self.total_contests == 0:
            return 0.0
        return self.frequencies.get(number, 0) / self.total_contests
    
    def get_all_frequencies(self) -> np.ndarray:
        """Retorna array com frequências de todos os números (1-25)"""
        return np.array([
            self.get_frequency(n) 
            for n in range(1, settings.total_numbers + 1)
        ])
    
    def get_normalized_frequencies(self) -> np.ndarray:
        """Retorna frequências normalizadas (soma = 1)"""
        freqs = self.get_all_frequencies()
        total = freqs.sum()
        return freqs / total if total > 0 else freqs
    
    def get_top_k(self, k: int = 10) -> List[Tuple[int, float]]:
        """Retorna os k números mais frequentes"""
        freqs = [(n, self.get_frequency(n)) for n in range(1, 26)]
        return sorted(freqs, key=lambda x: x[1], reverse=True)[:k]
    
    def to_dict(self) -> Dict[str, any]:
        """Serializa para dicionário"""
        return {
            "frequencies": dict(self.frequencies),
            "total_contests": self.total_contests,
            "normalized": self.get_normalized_frequencies().tolist()
        }


class DelayCalculator:
    """Calcula atraso (delay) de cada número"""
    
    def __init__(self):
        self.last_appearance: Dict[int, int] = {}
        self.current_contest_id: int = 0
    
    def update(self, contests: List[Contest]) -> None:
        """Atualiza atrasos com novos concursos"""
        # Ordena por contest_id para processar em ordem
        sorted_contests = sorted(contests, key=lambda c: c.contest_id)
        
        for contest in sorted_contests:
            self.current_contest_id = contest.contest_id
            for number in contest.numbers:
                self.last_appearance[number] = contest.contest_id
    
    def get_delay(self, number: int) -> int:
        """Retorna atraso de um número (concursos desde última aparição)"""
        if number not in self.last_appearance:
            return self.current_contest_id  # Nunca apareceu
        return self.current_contest_id - self.last_appearance[number]
    
    def get_all_delays(self) -> np.ndarray:
        """Retorna array com atrasos de todos os números (1-25)"""
        return np.array([
            self.get_delay(n) 
            for n in range(1, settings.total_numbers + 1)
        ])
    
    def get_normalized_delays(self) -> np.ndarray:
        """Retorna atrasos normalizados (0-1)"""
        delays = self.get_all_delays()
        max_delay = delays.max()
        return delays / max_delay if max_delay > 0 else delays
    
    def get_most_delayed(self, k: int = 10) -> List[Tuple[int, int]]:
        """Retorna os k números mais atrasados"""
        delays = [(n, self.get_delay(n)) for n in range(1, 26)]
        return sorted(delays, key=lambda x: x[1], reverse=True)[:k]
    
    def to_dict(self) -> Dict[str, any]:
        """Serializa para dicionário"""
        return {
            "last_appearance": dict(self.last_appearance),
            "current_contest_id": self.current_contest_id,
            "delays": self.get_all_delays().tolist()
        }


class RepetitionDetector:
    """Detecta números repetidos do último concurso"""
    
    def __init__(self):
        self.last_contest: Optional[Contest] = None
    
    def update(self, contests: List[Contest]) -> None:
        """Atualiza com novos concursos"""
        if contests:
            # Pega o mais recente
            sorted_contests = sorted(contests, key=lambda c: c.contest_id)
            self.last_contest = sorted_contests[-1]
    
    def get_repetition_mask(self) -> np.ndarray:
        """Retorna máscara binária indicando números do último concurso"""
        mask = np.zeros(settings.total_numbers, dtype=int)
        if self.last_contest:
            for number in self.last_contest.numbers:
                mask[number - 1] = 1
        return mask
    
    def is_repeated(self, number: int) -> bool:
        """Verifica se número estava no último concurso"""
        if not self.last_contest:
            return False
        return number in self.last_contest.numbers
    
    def get_repeated_numbers(self) -> List[int]:
        """Retorna lista de números do último concurso"""
        if not self.last_contest:
            return []
        return sorted(self.last_contest.numbers)
    
    def to_dict(self) -> Dict[str, any]:
        """Serializa para dicionário"""
        return {
            "last_contest_id": self.last_contest.contest_id if self.last_contest else None,
            "last_numbers": self.get_repeated_numbers(),
            "mask": self.get_repetition_mask().tolist()
        }


class AffinityMatrix:
    """Calcula matriz de afinidade (co-ocorrência) entre números"""
    
    def __init__(self):
        # Matriz 25x25 de co-ocorrências
        self.matrix = np.zeros((settings.total_numbers, settings.total_numbers))
        self.total_contests = 0
    
    def update(self, contests: List[Contest]) -> None:
        """Atualiza matriz com novos concursos"""
        for contest in contests:
            self.total_contests += 1
            numbers = contest.numbers
            
            # Incrementa co-ocorrências
            for i, num1 in enumerate(numbers):
                for num2 in numbers[i:]:  # Evita duplicatas
                    idx1, idx2 = num1 - 1, num2 - 1
                    self.matrix[idx1, idx2] += 1
                    if idx1 != idx2:  # Matriz simétrica
                        self.matrix[idx2, idx1] += 1
    
    def get_affinity(self, num1: int, num2: int) -> float:
        """Retorna afinidade entre dois números (0-1)"""
        if self.total_contests == 0:
            return 0.0
        idx1, idx2 = num1 - 1, num2 - 1
        return self.matrix[idx1, idx2] / self.total_contests
    
    def get_normalized_matrix(self) -> np.ndarray:
        """Retorna matriz normalizada (0-1)"""
        if self.total_contests == 0:
            return self.matrix.copy()
        return self.matrix / self.total_contests
    
    def get_affinity_score(self, numbers: List[int]) -> float:
        """Calcula score de afinidade para um conjunto de números"""
        if len(numbers) < 2:
            return 0.0
        
        total_affinity = 0.0
        count = 0
        
        for i, num1 in enumerate(numbers):
            for num2 in numbers[i+1:]:
                total_affinity += self.get_affinity(num1, num2)
                count += 1
        
        return total_affinity / count if count > 0 else 0.0
    
    def get_best_companions(self, number: int, k: int = 5) -> List[Tuple[int, float]]:
        """Retorna os k números com maior afinidade com o número dado"""
        idx = number - 1
        affinities = [
            (n + 1, self.matrix[idx, n] / self.total_contests if self.total_contests > 0 else 0)
            for n in range(settings.total_numbers)
            if n != idx
        ]
        return sorted(affinities, key=lambda x: x[1], reverse=True)[:k]
    
    def to_dict(self) -> Dict[str, any]:
        """Serializa para dicionário"""
        return {
            "matrix": self.get_normalized_matrix().tolist(),
            "total_contests": self.total_contests
        }


class FeatureEngineer:
    """Orquestrador de todas as features"""
    
    def __init__(self):
        self.frequency_calc = FrequencyCalculator()
        self.delay_calc = DelayCalculator()
        self.repetition_detector = RepetitionDetector()
        self.affinity_matrix = AffinityMatrix()
        self._is_fitted = False
    
    def fit(self, contests: List[Contest]) -> "FeatureEngineer":
        """Calcula todas as features a partir dos concursos"""
        if not contests:
            raise ValueError("Lista de concursos vazia")
        
        # Atualiza todos os calculadores
        self.frequency_calc.update(contests)
        self.delay_calc.update(contests)
        self.repetition_detector.update(contests)
        self.affinity_matrix.update(contests)
        
        self._is_fitted = True
        return self
    
    def get_feature_vector(self, number: int) -> np.ndarray:
        """Retorna vetor de features para um número específico"""
        if not self._is_fitted:
            raise RuntimeError("FeatureEngineer não foi fitted. Chame fit() primeiro.")
        
        return np.array([
            self.frequency_calc.get_frequency(number),
            self.delay_calc.get_delay(number),
            1.0 if self.repetition_detector.is_repeated(number) else 0.0,
        ])
    
    def get_all_features(self) -> Dict[str, np.ndarray]:
        """Retorna todas as features como dicionário de arrays"""
        if not self._is_fitted:
            raise RuntimeError("FeatureEngineer não foi fitted. Chame fit() primeiro.")
        
        return {
            "frequencies": self.frequency_calc.get_all_frequencies(),
            "delays": self.delay_calc.get_all_delays(),
            "repetitions": self.repetition_detector.get_repetition_mask(),
            "affinity_matrix": self.affinity_matrix.get_normalized_matrix()
        }
    
    def compute_number_score(self, number: int, weights: Dict[str, float]) -> float:
        """
        Calcula score de um número usando features e pesos do DNA
        
        Args:
            number: Número a avaliar (1-25)
            weights: Dicionário com pesos {'wf': 0.5, 'wa': 0.3, 'wr': 0.2}
        """
        if not self._is_fitted:
            raise RuntimeError("FeatureEngineer não foi fitted. Chame fit() primeiro.")
        
        freq = self.frequency_calc.get_frequency(number)
        delay = self.delay_calc.get_delay(number)
        repeated = 1.0 if self.repetition_detector.is_repeated(number) else 0.0
        
        # Normaliza delay (quanto maior o atraso, maior o score)
        max_delay = self.delay_calc.get_all_delays().max()
        norm_delay = delay / max_delay if max_delay > 0 else 0.0
        
        # Score ponderado
        score = (
            weights.get('wf', 0.0) * freq +
            weights.get('wa', 0.0) * norm_delay +
            weights.get('wr', 0.0) * repeated
        )
        
        return score
    
    def compute_all_scores(self, weights: Dict[str, float]) -> np.ndarray:
        """Calcula scores para todos os números (1-25)"""
        return np.array([
            self.compute_number_score(n, weights)
            for n in range(1, settings.total_numbers + 1)
        ])
    
    def to_dict(self) -> Dict[str, any]:
        """Serializa todas as features"""
        return {
            "is_fitted": self._is_fitted,
            "frequency": self.frequency_calc.to_dict(),
            "delay": self.delay_calc.to_dict(),
            "repetition": self.repetition_detector.to_dict(),
            "affinity": self.affinity_matrix.to_dict()
        }
    
    @property
    def is_fitted(self) -> bool:
        """Verifica se o engineer foi fitted"""
        return self._is_fitted
