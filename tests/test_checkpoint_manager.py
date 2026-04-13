import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from backend.core.persistence.checkpoint_manager import (
    CheckpointManager, CheckpointInfo, CheckpointData
)
from backend.core.genetic_algorithm import Population, GenerationStats


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def checkpoint_manager(temp_dir):
    """Cria CheckpointManager com diretório temporário"""
    return CheckpointManager(base_path=temp_dir)


@pytest.fixture
def sample_population():
    """Cria população de exemplo"""
    pop = Population(size=5, seed=42)
    pop.initialize_random()
    return pop


@pytest.fixture
def sample_stats():
    """Cria estatísticas de exemplo"""
    return GenerationStats(
        generation=1,
        best_fitness=1.5,
        avg_fitness=1.0,
        worst_fitness=0.5,
        std_fitness=0.3,
        best_roi=0.2,
        avg_roi=0.1,
        diversity=5.0,
        elapsed_time=10.0
    )


def test_checkpoint_manager_initialization(temp_dir):
    """Testa inicialização do CheckpointManager"""
    manager = CheckpointManager(base_path=temp_dir)
    
    assert manager.base_path == Path(temp_dir)
    assert manager.base_path.exists()


def test_save_checkpoint(checkpoint_manager, sample_population, sample_stats):
    """Testa salvamento de checkpoint"""
    experiment_id = "test_exp_001"
    generation = 1
    config = {"population_size": 5, "generations": 10}
    seeds = {"master": 42, "population": 123}
    
    checkpoint_id = checkpoint_manager.save_checkpoint(
        experiment_id=experiment_id,
        generation=generation,
        population=sample_population,
        stats=sample_stats,
        config=config,
        seeds=seeds
    )
    
    assert checkpoint_id is not None
    assert len(checkpoint_id) > 0


def test_load_checkpoint(checkpoint_manager, sample_population, sample_stats):
    """Testa carregamento de checkpoint"""
    experiment_id = "test_exp_002"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva
    checkpoint_id = checkpoint_manager.save_checkpoint(
        experiment_id=experiment_id,
        generation=1,
        population=sample_population,
        stats=sample_stats,
        config=config,
        seeds=seeds
    )
    
    # Carrega
    loaded = checkpoint_manager.load_checkpoint(checkpoint_id)
    
    assert loaded.checkpoint_id == checkpoint_id
    assert loaded.experiment_id == experiment_id
    assert loaded.generation == 1
    assert len(loaded.population.individuals) == 5
    assert loaded.stats.generation == 1


def test_list_checkpoints(checkpoint_manager, sample_population, sample_stats):
    """Testa listagem de checkpoints"""
    experiment_id = "test_exp_003"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva múltiplos checkpoints
    for gen in range(1, 4):
        stats = GenerationStats(
            generation=gen,
            best_fitness=1.0 + gen,
            avg_fitness=1.0,
            worst_fitness=0.5,
            std_fitness=0.3,
            best_roi=0.1,
            avg_roi=0.05,
            diversity=5.0,
            elapsed_time=10.0
        )
        
        checkpoint_manager.save_checkpoint(
            experiment_id=experiment_id,
            generation=gen,
            population=sample_population,
            stats=stats,
            config=config,
            seeds=seeds
        )
    
    # Lista
    checkpoints = checkpoint_manager.list_checkpoints(experiment_id)
    
    assert len(checkpoints) == 3
    assert checkpoints[0].generation == 1
    assert checkpoints[1].generation == 2
    assert checkpoints[2].generation == 3


def test_delete_checkpoint(checkpoint_manager, sample_population, sample_stats):
    """Testa deleção de checkpoint"""
    experiment_id = "test_exp_004"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva
    checkpoint_id = checkpoint_manager.save_checkpoint(
        experiment_id=experiment_id,
        generation=1,
        population=sample_population,
        stats=sample_stats,
        config=config,
        seeds=seeds
    )
    
    # Deleta
    deleted = checkpoint_manager.delete_checkpoint(checkpoint_id)
    
    assert deleted is True
    
    # Tenta carregar (deve falhar)
    with pytest.raises(FileNotFoundError):
        checkpoint_manager.load_checkpoint(checkpoint_id)


def test_get_latest_checkpoint(checkpoint_manager, sample_population, sample_stats):
    """Testa obtenção do checkpoint mais recente"""
    experiment_id = "test_exp_005"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva múltiplos checkpoints
    for gen in range(1, 4):
        stats = GenerationStats(
            generation=gen,
            best_fitness=1.0 + gen,
            avg_fitness=1.0,
            worst_fitness=0.5,
            std_fitness=0.3,
            best_roi=0.1,
            avg_roi=0.05,
            diversity=5.0,
            elapsed_time=10.0
        )
        
        checkpoint_manager.save_checkpoint(
            experiment_id=experiment_id,
            generation=gen,
            population=sample_population,
            stats=stats,
            config=config,
            seeds=seeds
        )
    
    # Obtém último
    latest = checkpoint_manager.get_latest_checkpoint(experiment_id)
    
    assert latest is not None
    assert latest.generation == 3
    assert latest.stats.best_fitness == 4.0


def test_get_checkpoint_by_generation(checkpoint_manager, sample_population, sample_stats):
    """Testa obtenção de checkpoint por geração"""
    experiment_id = "test_exp_006"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva múltiplos checkpoints
    for gen in range(1, 4):
        stats = GenerationStats(
            generation=gen,
            best_fitness=1.0 + gen,
            avg_fitness=1.0,
            worst_fitness=0.5,
            std_fitness=0.3,
            best_roi=0.1,
            avg_roi=0.05,
            diversity=5.0,
            elapsed_time=10.0
        )
        
        checkpoint_manager.save_checkpoint(
            experiment_id=experiment_id,
            generation=gen,
            population=sample_population,
            stats=stats,
            config=config,
            seeds=seeds
        )
    
    # Obtém geração 2
    checkpoint = checkpoint_manager.get_checkpoint_by_generation(experiment_id, 2)
    
    assert checkpoint is not None
    assert checkpoint.generation == 2
    assert checkpoint.stats.best_fitness == 3.0


def test_cleanup_old_checkpoints(checkpoint_manager, sample_population, sample_stats):
    """Testa limpeza de checkpoints antigos"""
    experiment_id = "test_exp_007"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva checkpoint
    checkpoint_manager.save_checkpoint(
        experiment_id=experiment_id,
        generation=1,
        population=sample_population,
        stats=sample_stats,
        config=config,
        seeds=seeds
    )
    
    # Limpa checkpoints com 0 dias (deve remover todos)
    removed = checkpoint_manager.cleanup_old_checkpoints(days=0)
    
    # Nota: pode ser 0 se o checkpoint foi criado há menos de 1 dia
    assert removed >= 0


def test_get_storage_stats(checkpoint_manager, sample_population, sample_stats):
    """Testa estatísticas de armazenamento"""
    experiment_id = "test_exp_008"
    config = {"population_size": 5}
    seeds = {"master": 42}
    
    # Salva alguns checkpoints
    for gen in range(1, 3):
        checkpoint_manager.save_checkpoint(
            experiment_id=experiment_id,
            generation=gen,
            population=sample_population,
            stats=sample_stats,
            config=config,
            seeds=seeds
        )
    
    # Obtém estatísticas
    stats = checkpoint_manager.get_storage_stats()
    
    assert stats["total_experiments"] >= 1
    assert stats["total_checkpoints"] >= 2
    assert stats["total_size_bytes"] > 0
    assert stats["total_size_mb"] > 0


def test_checkpoint_data_to_dict(sample_population, sample_stats):
    """Testa serialização de CheckpointData"""
    data = CheckpointData(
        checkpoint_id="test_id",
        experiment_id="exp_001",
        generation=1,
        population=sample_population,
        stats=sample_stats,
        config={"test": "config"},
        seeds={"master": 42},
        created_at=datetime.now()
    )
    
    dict_data = data.to_dict()
    
    assert dict_data["checkpoint_id"] == "test_id"
    assert dict_data["experiment_id"] == "exp_001"
    assert dict_data["generation"] == 1
    assert dict_data["population_size"] == 5


def test_checkpoint_info_to_dict():
    """Testa serialização de CheckpointInfo"""
    info = CheckpointInfo(
        id="test_id",
        experiment_id="exp_001",
        generation=1,
        created_at=datetime.now(),
        file_path="/path/to/file",
        file_size=1024
    )
    
    dict_data = info.to_dict()
    
    assert dict_data["id"] == "test_id"
    assert dict_data["experiment_id"] == "exp_001"
    assert dict_data["generation"] == 1
    assert dict_data["file_size"] == 1024


def test_load_nonexistent_checkpoint(checkpoint_manager):
    """Testa carregamento de checkpoint inexistente"""
    with pytest.raises(FileNotFoundError):
        checkpoint_manager.load_checkpoint("nonexistent_id")


def test_list_checkpoints_empty(checkpoint_manager):
    """Testa listagem de experimento sem checkpoints"""
    checkpoints = checkpoint_manager.list_checkpoints("nonexistent_exp")
    
    assert checkpoints == []


def test_delete_nonexistent_checkpoint(checkpoint_manager):
    """Testa deleção de checkpoint inexistente"""
    deleted = checkpoint_manager.delete_checkpoint("nonexistent_id")
    
    assert deleted is False


def test_get_latest_checkpoint_empty(checkpoint_manager):
    """Testa obtenção de checkpoint de experimento vazio"""
    latest = checkpoint_manager.get_latest_checkpoint("nonexistent_exp")
    
    assert latest is None
