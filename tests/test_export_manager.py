import pytest
import json
import csv
from io import StringIO
import tempfile
import shutil

from backend.core.persistence.export_manager import ExportManager
from backend.core.game_generator import Ticket, Game
from backend.models.dna import DNA, DNAGene
import numpy as np


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def export_manager(temp_dir):
    """Cria ExportManager com diretório temporário"""
    return ExportManager(base_path=temp_dir)


@pytest.fixture
def sample_ticket():
    """Cria bolão de exemplo"""
    games = [
        Game(numbers=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], cost=2.50),
        Game(numbers=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], cost=2.50),
        Game(numbers=[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25], cost=2.50)
    ]
    
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    
    return Ticket(games=games, dna=dna)


@pytest.fixture
def sample_dna():
    """Cria DNA de exemplo"""
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    dna.fitness = 1.5
    dna.roi = 0.2
    dna.risk = 0.1
    return dna


def test_export_manager_initialization(temp_dir):
    """Testa inicialização do ExportManager"""
    manager = ExportManager(base_path=temp_dir)
    
    assert manager.base_path.exists()


def test_export_ticket_json(export_manager, sample_ticket):
    """Testa exportação de bolão em JSON"""
    data = export_manager.export_ticket(sample_ticket, format="json")
    
    assert data is not None
    
    # Valida JSON
    parsed = json.loads(data.decode('utf-8'))
    assert "games" in parsed
    assert "total_games" in parsed
    assert "total_cost" in parsed
    assert len(parsed["games"]) == 3


def test_export_ticket_csv(export_manager, sample_ticket):
    """Testa exportação de bolão em CSV"""
    data = export_manager.export_ticket(sample_ticket, format="csv")
    
    assert data is not None
    
    # Valida CSV
    csv_text = data.decode('utf-8')
    reader = csv.reader(StringIO(csv_text))
    rows = list(reader)
    
    assert len(rows) > 0


def test_export_ticket_txt(export_manager, sample_ticket):
    """Testa exportação de bolão em TXT"""
    data = export_manager.export_ticket(sample_ticket, format="txt")
    
    assert data is not None
    
    # Valida TXT
    text = data.decode('utf-8')
    assert "BOLÃO LOTOFÁCIL" in text
    assert "Jogo" in text


def test_export_ticket_invalid_format(export_manager, sample_ticket):
    """Testa exportação com formato inválido"""
    with pytest.raises(ValueError):
        export_manager.export_ticket(sample_ticket, format="invalid")


def test_export_ticket_without_metadata(export_manager, sample_ticket):
    """Testa exportação sem metadados"""
    data = export_manager.export_ticket(
        sample_ticket,
        format="json",
        include_metadata=False
    )
    
    parsed = json.loads(data.decode('utf-8'))
    assert "metadata" not in parsed


def test_export_experiment_json(export_manager):
    """Testa exportação de experimento em JSON"""
    experiment_data = {
        "id": "exp_001",
        "name": "Test Experiment",
        "config": {"population_size": 20},
        "result": {"best_fitness": 1.5}
    }
    
    data = export_manager.export_experiment(experiment_data, format="json")
    
    assert data is not None
    
    parsed = json.loads(data.decode('utf-8'))
    assert "experiment" in parsed
    assert parsed["experiment"]["id"] == "exp_001"


def test_export_experiment_csv(export_manager):
    """Testa exportação de experimento em CSV"""
    experiment_data = {
        "id": "exp_001",
        "name": "Test Experiment",
        "config": {"population_size": 20},
        "result": {"best_fitness": 1.5}
    }
    
    data = export_manager.export_experiment(experiment_data, format="csv")
    
    assert data is not None
    
    csv_text = data.decode('utf-8')
    assert "exp_001" in csv_text


def test_export_dna_json(export_manager, sample_dna):
    """Testa exportação de DNA em JSON"""
    data = export_manager.export_dna(sample_dna, format="json")
    
    assert data is not None
    
    parsed = json.loads(data.decode('utf-8'))
    assert "dna" in parsed
    assert "fitness" in parsed
    assert parsed["fitness"] == 1.5


def test_export_dna_csv(export_manager, sample_dna):
    """Testa exportação de DNA em CSV"""
    data = export_manager.export_dna(sample_dna, format="csv")
    
    assert data is not None
    
    csv_text = data.decode('utf-8')
    reader = csv.reader(StringIO(csv_text))
    rows = list(reader)
    
    assert len(rows) > 0


def test_export_dna_txt(export_manager, sample_dna):
    """Testa exportação de DNA em TXT"""
    data = export_manager.export_dna(sample_dna, format="txt")
    
    assert data is not None
    
    text = data.decode('utf-8')
    assert "DNA EVOLUTIVO" in text
    assert "GENES:" in text


def test_save_export(export_manager, sample_ticket):
    """Testa salvamento de exportação"""
    data = export_manager.export_ticket(sample_ticket, format="json")
    
    file_path = export_manager.save_export(
        data,
        "test_ticket.json",
        experiment_id="exp_001"
    )
    
    assert file_path is not None
    assert "exp_001" in file_path
    assert "test_ticket.json" in file_path


def test_validate_export_json(export_manager, sample_ticket):
    """Testa validação de exportação JSON"""
    data = export_manager.export_ticket(sample_ticket, format="json")
    
    is_valid = export_manager.validate_export(data, "json")
    
    assert is_valid is True


def test_validate_export_csv(export_manager, sample_ticket):
    """Testa validação de exportação CSV"""
    data = export_manager.export_ticket(sample_ticket, format="csv")
    
    is_valid = export_manager.validate_export(data, "csv")
    
    assert is_valid is True


def test_validate_export_txt(export_manager, sample_ticket):
    """Testa validação de exportação TXT"""
    data = export_manager.export_ticket(sample_ticket, format="txt")
    
    is_valid = export_manager.validate_export(data, "txt")
    
    assert is_valid is True


def test_validate_export_invalid(export_manager):
    """Testa validação de exportação inválida"""
    invalid_data = b"invalid json {{"
    
    is_valid = export_manager.validate_export(invalid_data, "json")
    
    assert is_valid is False


def test_export_ticket_json_structure(export_manager, sample_ticket):
    """Testa estrutura detalhada do JSON exportado"""
    data = export_manager.export_ticket(sample_ticket, format="json")
    parsed = json.loads(data.decode('utf-8'))
    
    assert isinstance(parsed["games"], list)
    assert isinstance(parsed["total_games"], int)
    assert isinstance(parsed["total_cost"], float)
    assert parsed["total_games"] == len(sample_ticket.games)


def test_export_multiple_formats(export_manager, sample_ticket):
    """Testa exportação em múltiplos formatos"""
    json_data = export_manager.export_ticket(sample_ticket, format="json")
    csv_data = export_manager.export_ticket(sample_ticket, format="csv")
    txt_data = export_manager.export_ticket(sample_ticket, format="txt")
    
    assert json_data != csv_data
    assert csv_data != txt_data
    assert json_data != txt_data


def test_export_dna_with_metrics(export_manager, sample_dna):
    """Testa exportação de DNA com métricas"""
    data = export_manager.export_dna(sample_dna, format="json")
    parsed = json.loads(data.decode('utf-8'))
    
    assert parsed["fitness"] == sample_dna.fitness
    assert parsed["roi"] == sample_dna.roi
    assert parsed["risk"] == sample_dna.risk
    assert parsed["generation"] == sample_dna.generation
