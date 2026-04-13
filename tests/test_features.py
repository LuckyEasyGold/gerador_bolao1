import pytest
import numpy as np
from datetime import date
from backend.core.feature_engineering import (
    FrequencyCalculator,
    DelayCalculator,
    RepetitionDetector,
    AffinityMatrix,
    FeatureEngineer
)
from backend.models.contest import Contest


@pytest.fixture
def sample_contests():
    """Cria concursos de exemplo para testes"""
    return [
        Contest(contest_id=1, draw_date=date(2024, 1, 1), 
                numbers=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]),
        Contest(contest_id=2, draw_date=date(2024, 1, 2),
                numbers=[1, 2, 3, 4, 5, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]),
        Contest(contest_id=3, draw_date=date(2024, 1, 3),
                numbers=[1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]),
    ]


def test_frequency_calculator(sample_contests):
    """Testa cálculo de frequências"""
    calc = FrequencyCalculator()
    calc.update(sample_contests)
    
    # Número 1 aparece em todos os 3 concursos
    assert calc.get_frequency(1) == 1.0
    
    # Número 25 aparece em 1 concurso
    assert calc.get_frequency(25) == pytest.approx(1/3)
    
    # Total de concursos
    assert calc.total_contests == 3
    
    # Array de frequências
    freqs = calc.get_all_frequencies()
    assert len(freqs) == 25
    assert freqs[0] == 1.0  # Número 1


def test_frequency_normalized(sample_contests):
    """Testa normalização de frequências"""
    calc = FrequencyCalculator()
    calc.update(sample_contests)
    
    norm_freqs = calc.get_normalized_frequencies()
    
    # Soma deve ser 1.0
    assert np.isclose(norm_freqs.sum(), 1.0)
    
    # Todos valores entre 0 e 1
    assert np.all(norm_freqs >= 0)
    assert np.all(norm_freqs <= 1)


def test_frequency_top_k(sample_contests):
    """Testa seleção dos k mais frequentes"""
    calc = FrequencyCalculator()
    calc.update(sample_contests)
    
    top_5 = calc.get_top_k(5)
    
    assert len(top_5) == 5
    # Primeiro deve ser o mais frequente
    assert top_5[0][0] in [1, 2, 3]  # Aparecem em todos


def test_delay_calculator(sample_contests):
    """Testa cálculo de atrasos"""
    calc = DelayCalculator()
    calc.update(sample_contests)
    
    # Número 1 apareceu no concurso 3 (último)
    assert calc.get_delay(1) == 0
    
    # Número 25 apareceu no concurso 2
    assert calc.get_delay(25) == 1
    
    # Array de atrasos
    delays = calc.get_all_delays()
    assert len(delays) == 25


def test_delay_most_delayed(sample_contests):
    """Testa seleção dos mais atrasados"""
    calc = DelayCalculator()
    calc.update(sample_contests)
    
    most_delayed = calc.get_most_delayed(5)
    
    assert len(most_delayed) == 5
    # Atrasos devem estar em ordem decrescente
    delays_only = [d for _, d in most_delayed]
    assert delays_only == sorted(delays_only, reverse=True)


def test_repetition_detector(sample_contests):
    """Testa detecção de repetições"""
    detector = RepetitionDetector()
    detector.update(sample_contests)
    
    # Último concurso tem números 1-3, 6-17
    assert detector.is_repeated(1) is True
    assert detector.is_repeated(4) is False
    assert detector.is_repeated(25) is False
    
    # Máscara binária
    mask = detector.get_repetition_mask()
    assert len(mask) == 25
    assert mask[0] == 1  # Número 1
    assert mask[3] == 0  # Número 4


def test_repetition_repeated_numbers(sample_contests):
    """Testa lista de números repetidos"""
    detector = RepetitionDetector()
    detector.update(sample_contests)
    
    repeated = detector.get_repeated_numbers()
    
    assert len(repeated) == 15
    assert 1 in repeated
    assert 2 in repeated
    assert 4 not in repeated


def test_affinity_matrix(sample_contests):
    """Testa matriz de afinidade"""
    matrix = AffinityMatrix()
    matrix.update(sample_contests)
    
    # Números 1 e 2 aparecem juntos em todos os 3 concursos
    assert matrix.get_affinity(1, 2) == 1.0
    
    # Números 1 e 25 aparecem juntos em 1 concurso
    assert matrix.get_affinity(1, 25) == pytest.approx(1/3)
    
    # Matriz deve ser simétrica
    assert matrix.get_affinity(1, 2) == matrix.get_affinity(2, 1)


def test_affinity_score(sample_contests):
    """Testa score de afinidade para conjunto"""
    matrix = AffinityMatrix()
    matrix.update(sample_contests)
    
    # Números que aparecem juntos frequentemente
    score_high = matrix.get_affinity_score([1, 2, 3])
    
    # Números que raramente aparecem juntos
    score_low = matrix.get_affinity_score([1, 25])
    
    assert score_high > score_low


def test_affinity_best_companions(sample_contests):
    """Testa busca de melhores companheiros"""
    matrix = AffinityMatrix()
    matrix.update(sample_contests)
    
    companions = matrix.get_best_companions(1, k=5)
    
    assert len(companions) == 5
    # Deve retornar tuplas (número, afinidade)
    assert all(isinstance(c, tuple) and len(c) == 2 for c in companions)
    # Afinidades em ordem decrescente
    affinities = [a for _, a in companions]
    assert affinities == sorted(affinities, reverse=True)


def test_feature_engineer_fit(sample_contests):
    """Testa fitting do FeatureEngineer"""
    engineer = FeatureEngineer()
    
    assert not engineer.is_fitted
    
    engineer.fit(sample_contests)
    
    assert engineer.is_fitted


def test_feature_engineer_empty_contests():
    """Testa erro com lista vazia"""
    engineer = FeatureEngineer()
    
    with pytest.raises(ValueError):
        engineer.fit([])


def test_feature_engineer_not_fitted():
    """Testa erro quando não fitted"""
    engineer = FeatureEngineer()
    
    with pytest.raises(RuntimeError):
        engineer.get_feature_vector(1)


def test_feature_engineer_feature_vector(sample_contests):
    """Testa vetor de features"""
    engineer = FeatureEngineer()
    engineer.fit(sample_contests)
    
    vector = engineer.get_feature_vector(1)
    
    assert len(vector) == 3  # freq, delay, repetition
    assert vector[0] == 1.0  # Frequência
    assert vector[1] == 0  # Delay
    assert vector[2] == 1.0  # Repetido


def test_feature_engineer_all_features(sample_contests):
    """Testa recuperação de todas as features"""
    engineer = FeatureEngineer()
    engineer.fit(sample_contests)
    
    features = engineer.get_all_features()
    
    assert "frequencies" in features
    assert "delays" in features
    assert "repetitions" in features
    assert "affinity_matrix" in features
    
    assert len(features["frequencies"]) == 25
    assert len(features["delays"]) == 25
    assert len(features["repetitions"]) == 25
    assert features["affinity_matrix"].shape == (25, 25)


def test_feature_engineer_compute_score(sample_contests):
    """Testa cálculo de score com pesos"""
    engineer = FeatureEngineer()
    engineer.fit(sample_contests)
    
    weights = {'wf': 0.5, 'wa': 0.3, 'wr': 0.2}
    
    score = engineer.compute_number_score(1, weights)
    
    assert isinstance(score, float)
    assert score >= 0


def test_feature_engineer_compute_all_scores(sample_contests):
    """Testa cálculo de scores para todos os números"""
    engineer = FeatureEngineer()
    engineer.fit(sample_contests)
    
    weights = {'wf': 0.5, 'wa': 0.3, 'wr': 0.2}
    
    scores = engineer.compute_all_scores(weights)
    
    assert len(scores) == 25
    assert np.all(scores >= 0)


def test_feature_engineer_serialization(sample_contests):
    """Testa serialização para dicionário"""
    engineer = FeatureEngineer()
    engineer.fit(sample_contests)
    
    data = engineer.to_dict()
    
    assert data["is_fitted"] is True
    assert "frequency" in data
    assert "delay" in data
    assert "repetition" in data
    assert "affinity" in data


def test_frequency_serialization(sample_contests):
    """Testa serialização de FrequencyCalculator"""
    calc = FrequencyCalculator()
    calc.update(sample_contests)
    
    data = calc.to_dict()
    
    assert "frequencies" in data
    assert "total_contests" in data
    assert "normalized" in data
    assert data["total_contests"] == 3


def test_delay_serialization(sample_contests):
    """Testa serialização de DelayCalculator"""
    calc = DelayCalculator()
    calc.update(sample_contests)
    
    data = calc.to_dict()
    
    assert "last_appearance" in data
    assert "current_contest_id" in data
    assert "delays" in data


def test_affinity_serialization(sample_contests):
    """Testa serialização de AffinityMatrix"""
    matrix = AffinityMatrix()
    matrix.update(sample_contests)
    
    data = matrix.to_dict()
    
    assert "matrix" in data
    assert "total_contests" in data
    assert len(data["matrix"]) == 25
    assert len(data["matrix"][0]) == 25
