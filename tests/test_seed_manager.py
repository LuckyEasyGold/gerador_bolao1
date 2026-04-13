import pytest
import tempfile
import shutil

from backend.core.persistence.seed_manager import SeedManager


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def seed_manager(temp_dir):
    """Cria SeedManager com diretório temporário"""
    return SeedManager(base_path=temp_dir)


def test_seed_manager_initialization(temp_dir):
    """Testa inicialização do SeedManager"""
    manager = SeedManager(base_path=temp_dir)
    
    assert manager.base_path.exists()


def test_register_seed(seed_manager):
    """Testa registro de seed"""
    experiment_id = "test_exp_001"
    component = "population"
    seed = 42
    
    seed_manager.register_seed(experiment_id, component, seed)
    
    # Verifica se foi registrada
    seeds = seed_manager.get_seeds(experiment_id)
    assert seeds[component] == seed


def test_get_seeds(seed_manager):
    """Testa obtenção de seeds"""
    experiment_id = "test_exp_002"
    
    # Registra múltiplas seeds
    seed_manager.register_seed(experiment_id, "master", 42)
    seed_manager.register_seed(experiment_id, "population", 123)
    seed_manager.register_seed(experiment_id, "selector", 456)
    
    # Obtém todas
    seeds = seed_manager.get_seeds(experiment_id)
    
    assert len(seeds) == 3
    assert seeds["master"] == 42
    assert seeds["population"] == 123
    assert seeds["selector"] == 456


def test_get_seed(seed_manager):
    """Testa obtenção de seed específica"""
    experiment_id = "test_exp_003"
    
    seed_manager.register_seed(experiment_id, "master", 42)
    seed_manager.register_seed(experiment_id, "population", 123)
    
    # Obtém seed específica
    seed = seed_manager.get_seed(experiment_id, "population")
    
    assert seed == 123


def test_get_seed_nonexistent(seed_manager):
    """Testa obtenção de seed inexistente"""
    seed = seed_manager.get_seed("nonexistent_exp", "master")
    
    assert seed is None


def test_validate_seeds_valid(seed_manager):
    """Testa validação de seeds válidas"""
    experiment_id = "test_exp_004"
    
    # Registra seeds necessárias
    seed_manager.register_seed(experiment_id, "master", 42)
    seed_manager.register_seed(experiment_id, "population", 123)
    seed_manager.register_seed(experiment_id, "selector", 456)
    seed_manager.register_seed(experiment_id, "operators", 789)
    seed_manager.register_seed(experiment_id, "monte_carlo", 101)
    
    # Valida
    is_valid = seed_manager.validate_seeds(experiment_id)
    
    assert is_valid is True


def test_validate_seeds_invalid(seed_manager):
    """Testa validação de seeds inválidas"""
    experiment_id = "test_exp_005"
    
    # Registra apenas master
    seed_manager.register_seed(experiment_id, "master", 42)
    
    # Valida (deve falhar)
    is_valid = seed_manager.validate_seeds(experiment_id)
    
    assert is_valid is False


def test_generate_seed_chain(seed_manager):
    """Testa geração de chain de seeds"""
    master_seed = 42
    
    seeds = seed_manager.generate_seed_chain(master_seed)
    
    assert "master" in seeds
    assert seeds["master"] == master_seed
    assert "population" in seeds
    assert "selector" in seeds
    assert "operators" in seeds
    
    # Seeds devem ser diferentes
    unique_seeds = set(seeds.values())
    assert len(unique_seeds) == len(seeds)


def test_generate_seed_chain_deterministic(seed_manager):
    """Testa determinismo da geração de seeds"""
    master_seed = 42
    
    # Gera duas vezes
    seeds1 = seed_manager.generate_seed_chain(master_seed)
    seeds2 = seed_manager.generate_seed_chain(master_seed)
    
    # Devem ser idênticas
    assert seeds1 == seeds2


def test_generate_seed_chain_custom_components(seed_manager):
    """Testa geração com componentes customizados"""
    master_seed = 42
    components = ["master", "comp1", "comp2"]
    
    seeds = seed_manager.generate_seed_chain(master_seed, components)
    
    assert len(seeds) == 3
    assert "master" in seeds
    assert "comp1" in seeds
    assert "comp2" in seeds


def test_register_seed_chain(seed_manager):
    """Testa registro de chain completa"""
    experiment_id = "test_exp_006"
    master_seed = 42
    
    seeds = seed_manager.register_seed_chain(experiment_id, master_seed)
    
    # Verifica se foram registradas
    loaded_seeds = seed_manager.get_seeds(experiment_id)
    
    assert loaded_seeds == seeds
    assert loaded_seeds["master"] == master_seed


def test_compare_seeds_identical(seed_manager):
    """Testa comparação de seeds idênticas"""
    master_seed = 42
    
    # Registra mesmas seeds em dois experimentos
    seed_manager.register_seed_chain("exp1", master_seed)
    seed_manager.register_seed_chain("exp2", master_seed)
    
    # Compara
    comparison = seed_manager.compare_seeds("exp1", "exp2")
    
    # Todas devem ser iguais
    assert all(comparison.values())


def test_compare_seeds_different(seed_manager):
    """Testa comparação de seeds diferentes"""
    # Registra seeds diferentes
    seed_manager.register_seed_chain("exp1", 42)
    seed_manager.register_seed_chain("exp2", 123)
    
    # Compara
    comparison = seed_manager.compare_seeds("exp1", "exp2")
    
    # Nenhuma deve ser igual
    assert not any(comparison.values())


def test_get_seed_hash(seed_manager):
    """Testa geração de hash de seeds"""
    experiment_id = "test_exp_007"
    
    seed_manager.register_seed_chain(experiment_id, 42)
    
    hash1 = seed_manager.get_seed_hash(experiment_id)
    
    assert hash1 is not None
    assert len(hash1) == 64  # SHA256


def test_get_seed_hash_deterministic(seed_manager):
    """Testa determinismo do hash"""
    experiment_id = "test_exp_008"
    
    seed_manager.register_seed_chain(experiment_id, 42)
    
    hash1 = seed_manager.get_seed_hash(experiment_id)
    hash2 = seed_manager.get_seed_hash(experiment_id)
    
    assert hash1 == hash2


def test_get_seed_hash_different_seeds(seed_manager):
    """Testa hash de seeds diferentes"""
    seed_manager.register_seed_chain("exp1", 42)
    seed_manager.register_seed_chain("exp2", 123)
    
    hash1 = seed_manager.get_seed_hash("exp1")
    hash2 = seed_manager.get_seed_hash("exp2")
    
    assert hash1 != hash2


def test_list_experiments(seed_manager):
    """Testa listagem de experimentos"""
    # Registra seeds em múltiplos experimentos
    seed_manager.register_seed("exp1", "master", 42)
    seed_manager.register_seed("exp2", "master", 123)
    seed_manager.register_seed("exp3", "master", 456)
    
    # Lista
    experiments = seed_manager.list_experiments()
    
    assert len(experiments) >= 3
    assert "exp1" in experiments
    assert "exp2" in experiments
    assert "exp3" in experiments


def test_delete_seeds(seed_manager):
    """Testa deleção de seeds"""
    experiment_id = "test_exp_009"
    
    # Registra seeds
    seed_manager.register_seed(experiment_id, "master", 42)
    
    # Deleta
    deleted = seed_manager.delete_seeds(experiment_id)
    
    assert deleted is True
    
    # Verifica se foi deletado
    seeds = seed_manager.get_seeds(experiment_id)
    assert len(seeds) == 0


def test_delete_seeds_nonexistent(seed_manager):
    """Testa deleção de seeds inexistentes"""
    deleted = seed_manager.delete_seeds("nonexistent_exp")
    
    assert deleted is False


def test_seed_components_constant():
    """Testa constante de componentes"""
    assert "master" in SeedManager.COMPONENTS
    assert "population" in SeedManager.COMPONENTS
    assert "selector" in SeedManager.COMPONENTS
    assert "operators" in SeedManager.COMPONENTS
    assert "monte_carlo" in SeedManager.COMPONENTS


def test_multiple_seed_updates(seed_manager):
    """Testa múltiplas atualizações de seeds"""
    experiment_id = "test_exp_010"
    
    # Registra seed inicial
    seed_manager.register_seed(experiment_id, "master", 42)
    
    # Atualiza
    seed_manager.register_seed(experiment_id, "master", 123)
    
    # Verifica se foi atualizada
    seed = seed_manager.get_seed(experiment_id, "master")
    assert seed == 123


def test_seed_chain_different_masters(seed_manager):
    """Testa chains com diferentes master seeds"""
    seeds1 = seed_manager.generate_seed_chain(42)
    seeds2 = seed_manager.generate_seed_chain(123)
    
    # Master seeds devem ser diferentes
    assert seeds1["master"] != seeds2["master"]
    
    # Outras seeds também devem ser diferentes
    assert seeds1["population"] != seeds2["population"]
    assert seeds1["selector"] != seeds2["selector"]
