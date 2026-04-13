import pytest
import tempfile
import shutil

from backend.core.persistence.experiment_logger import (
    ExperimentLogger, LogLevel, LogType, LogEntry
)


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def logger(temp_dir):
    """Cria ExperimentLogger com diretório temporário"""
    return ExperimentLogger(base_path=temp_dir)


def test_logger_initialization(temp_dir):
    """Testa inicialização do logger"""
    logger = ExperimentLogger(base_path=temp_dir)
    
    assert logger.base_path.exists()


def test_log_start(logger):
    """Testa log de início"""
    experiment_id = "test_exp_001"
    config = {"population_size": 20, "generations": 50}
    
    logger.log_start(experiment_id, config)
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.START


def test_log_generation(logger):
    """Testa log de geração"""
    experiment_id = "test_exp_002"
    stats = {"best_fitness": 1.5, "avg_fitness": 1.0}
    
    logger.log_generation(experiment_id, 1, stats)
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.GENERATION


def test_log_convergence(logger):
    """Testa log de convergência"""
    experiment_id = "test_exp_003"
    
    logger.log_convergence(experiment_id, 10, "Threshold atingido")
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.CONVERGENCE


def test_log_completion(logger):
    """Testa log de conclusão"""
    experiment_id = "test_exp_004"
    result = {"best_fitness": 2.0, "generations_run": 50}
    
    logger.log_completion(experiment_id, result)
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.COMPLETION


def test_log_error(logger):
    """Testa log de erro"""
    experiment_id = "test_exp_005"
    error = ValueError("Test error")
    
    logger.log_error(experiment_id, error)
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].level == LogLevel.ERROR


def test_log_checkpoint(logger):
    """Testa log de checkpoint"""
    experiment_id = "test_exp_006"
    
    logger.log_checkpoint(experiment_id, "checkpoint_123", 5)
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.CHECKPOINT


def test_log_metric(logger):
    """Testa log de métrica"""
    experiment_id = "test_exp_007"
    
    logger.log_metric(experiment_id, "fitness", 1.5)
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.METRIC


def test_log_event(logger):
    """Testa log de evento"""
    experiment_id = "test_exp_008"
    
    logger.log_event(experiment_id, "Custom Event", {"key": "value"})
    
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 1
    assert logs[0].log_type == LogType.EVENT


def test_get_logs_with_filter(logger):
    """Testa obtenção de logs com filtro"""
    experiment_id = "test_exp_009"
    
    # Registra logs de diferentes tipos
    logger.log_start(experiment_id, {})
    logger.log_generation(experiment_id, 1, {})
    logger.log_error(experiment_id, ValueError("Test"))
    
    # Filtra apenas erros
    errors = logger.get_logs(experiment_id, level=LogLevel.ERROR)
    
    assert len(errors) == 1
    assert errors[0].level == LogLevel.ERROR


def test_get_errors(logger):
    """Testa obtenção apenas de erros"""
    experiment_id = "test_exp_010"
    
    logger.log_start(experiment_id, {})
    logger.log_error(experiment_id, ValueError("Error 1"))
    logger.log_error(experiment_id, ValueError("Error 2"))
    
    errors = logger.get_errors(experiment_id)
    
    assert len(errors) == 2


def test_get_metrics(logger):
    """Testa obtenção apenas de métricas"""
    experiment_id = "test_exp_011"
    
    logger.log_start(experiment_id, {})
    logger.log_metric(experiment_id, "fitness", 1.5)
    logger.log_metric(experiment_id, "roi", 0.2)
    
    metrics = logger.get_metrics(experiment_id)
    
    assert len(metrics) == 2


def test_get_summary(logger):
    """Testa obtenção de resumo"""
    experiment_id = "test_exp_012"
    
    logger.log_start(experiment_id, {})
    logger.log_generation(experiment_id, 1, {})
    logger.log_error(experiment_id, ValueError("Test"))
    logger.log_completion(experiment_id, {})
    
    summary = logger.get_summary(experiment_id)
    
    assert summary["total_logs"] == 4
    assert summary["errors"] == 1
    assert "by_level" in summary
    assert "by_type" in summary


def test_clear_logs(logger):
    """Testa limpeza de logs"""
    experiment_id = "test_exp_013"
    
    logger.log_start(experiment_id, {})
    logger.log_generation(experiment_id, 1, {})
    
    # Limpa
    cleared = logger.clear_logs(experiment_id)
    
    assert cleared is True
    
    # Verifica se foi limpo
    logs = logger.get_logs(experiment_id)
    assert len(logs) == 0


def test_clear_logs_nonexistent(logger):
    """Testa limpeza de logs inexistentes"""
    cleared = logger.clear_logs("nonexistent_exp")
    
    assert cleared is False


def test_log_entry_to_dict():
    """Testa serialização de LogEntry"""
    from datetime import datetime
    
    entry = LogEntry(
        timestamp=datetime.now(),
        experiment_id="exp_001",
        level=LogLevel.INFO,
        log_type=LogType.START,
        message="Test message",
        data={"key": "value"}
    )
    
    dict_data = entry.to_dict()
    
    assert dict_data["experiment_id"] == "exp_001"
    assert dict_data["level"] == "INFO"
    assert dict_data["type"] == "START"
    assert dict_data["message"] == "Test message"


def test_multiple_experiments(logger):
    """Testa logs de múltiplos experimentos"""
    logger.log_start("exp1", {})
    logger.log_start("exp2", {})
    logger.log_start("exp3", {})
    
    logs1 = logger.get_logs("exp1")
    logs2 = logger.get_logs("exp2")
    logs3 = logger.get_logs("exp3")
    
    assert len(logs1) == 1
    assert len(logs2) == 1
    assert len(logs3) == 1


def test_log_with_limit(logger):
    """Testa obtenção de logs com limite"""
    experiment_id = "test_exp_014"
    
    # Registra múltiplos logs
    for i in range(10):
        logger.log_generation(experiment_id, i, {})
    
    # Obtém apenas 5
    logs = logger.get_logs(experiment_id, limit=5)
    
    assert len(logs) == 5
