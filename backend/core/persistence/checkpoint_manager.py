"""
CheckpointManager - Gerenciamento de Checkpoints
Salva e carrega estado completo de experimentos
"""
import json
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid

from backend.core.genetic_algorithm import Population, GenerationStats
from backend.config import get_settings

settings = get_settings()


@dataclass
class CheckpointInfo:
    """Informações de um checkpoint"""
    id: str
    experiment_id: str
    generation: int
    created_at: datetime
    file_path: str
    file_size: int
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "generation": self.generation,
            "created_at": self.created_at.isoformat(),
            "file_path": self.file_path,
            "file_size": self.file_size
        }


@dataclass
class CheckpointData:
    """Dados completos de um checkpoint"""
    checkpoint_id: str
    experiment_id: str
    generation: int
    population: Population
    stats: GenerationStats
    config: Dict[str, Any]
    seeds: Dict[str, int]
    created_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "experiment_id": self.experiment_id,
            "generation": self.generation,
            "population_size": len(self.population.individuals),
            "stats": self.stats.to_dict(),
            "config": self.config,
            "seeds": self.seeds,
            "created_at": self.created_at.isoformat()
        }


class CheckpointManager:
    """
    Gerencia checkpoints de experimentos
    
    Salva estado completo por geração para permitir:
    - Retomada de execução
    - Replay de experimentos
    - Auditoria completa
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: Diretório base para checkpoints
        """
        self.base_path = Path(base_path or "data/checkpoints")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self,
                       experiment_id: str,
                       generation: int,
                       population: Population,
                       stats: GenerationStats,
                       config: Dict[str, Any],
                       seeds: Dict[str, int]) -> str:
        """
        Salva checkpoint de uma geração
        
        Args:
            experiment_id: ID do experimento
            generation: Número da geração
            population: População atual
            stats: Estatísticas da geração
            config: Configuração do experimento
            seeds: Seeds utilizadas
        
        Returns:
            ID do checkpoint criado
        """
        checkpoint_id = str(uuid.uuid4())
        
        # Cria diretório do experimento
        exp_dir = self.base_path / experiment_id
        exp_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo
        filename = f"gen_{generation:04d}_{checkpoint_id}.pkl"
        file_path = exp_dir / filename
        
        # Dados do checkpoint
        checkpoint_data = CheckpointData(
            checkpoint_id=checkpoint_id,
            experiment_id=experiment_id,
            generation=generation,
            population=population,
            stats=stats,
            config=config,
            seeds=seeds,
            created_at=datetime.now()
        )
        
        # Salva em pickle (binário, eficiente)
        with open(file_path, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        # Salva metadados em JSON (legível)
        meta_path = exp_dir / f"gen_{generation:04d}_{checkpoint_id}.json"
        with open(meta_path, 'w') as f:
            json.dump(checkpoint_data.to_dict(), f, indent=2)
        
        return checkpoint_id
    
    def load_checkpoint(self, checkpoint_id: str) -> CheckpointData:
        """
        Carrega checkpoint pelo ID
        
        Args:
            checkpoint_id: ID do checkpoint
        
        Returns:
            CheckpointData completo
        
        Raises:
            FileNotFoundError: Se checkpoint não existe
        """
        # Busca arquivo
        for exp_dir in self.base_path.iterdir():
            if not exp_dir.is_dir():
                continue
            
            for file_path in exp_dir.glob(f"*{checkpoint_id}.pkl"):
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
        
        raise FileNotFoundError(f"Checkpoint {checkpoint_id} não encontrado")
    
    def list_checkpoints(self, experiment_id: str) -> List[CheckpointInfo]:
        """
        Lista checkpoints de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            Lista de CheckpointInfo ordenada por geração
        """
        exp_dir = self.base_path / experiment_id
        
        if not exp_dir.exists():
            return []
        
        checkpoints = []
        
        for file_path in exp_dir.glob("*.pkl"):
            # Extrai informações do nome
            parts = file_path.stem.split('_')
            generation = int(parts[1])
            checkpoint_id = parts[2]
            
            # Estatísticas do arquivo
            stat = file_path.stat()
            
            checkpoints.append(CheckpointInfo(
                id=checkpoint_id,
                experiment_id=experiment_id,
                generation=generation,
                created_at=datetime.fromtimestamp(stat.st_mtime),
                file_path=str(file_path),
                file_size=stat.st_size
            ))
        
        # Ordena por geração
        checkpoints.sort(key=lambda x: x.generation)
        
        return checkpoints
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Deleta checkpoint
        
        Args:
            checkpoint_id: ID do checkpoint
        
        Returns:
            True se deletado, False se não encontrado
        """
        # Busca e deleta arquivo
        for exp_dir in self.base_path.iterdir():
            if not exp_dir.is_dir():
                continue
            
            for file_path in exp_dir.glob(f"*{checkpoint_id}.*"):
                file_path.unlink()
                return True
        
        return False
    
    def cleanup_old_checkpoints(self, days: int = 30) -> int:
        """
        Remove checkpoints antigos
        
        Args:
            days: Idade mínima em dias
        
        Returns:
            Número de checkpoints removidos
        """
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        for exp_dir in self.base_path.iterdir():
            if not exp_dir.is_dir():
                continue
            
            for file_path in exp_dir.glob("*.pkl"):
                stat = file_path.stat()
                created = datetime.fromtimestamp(stat.st_mtime)
                
                if created < cutoff:
                    # Remove pickle e json
                    file_path.unlink()
                    json_path = file_path.with_suffix('.json')
                    if json_path.exists():
                        json_path.unlink()
                    removed += 1
        
        return removed
    
    def get_latest_checkpoint(self, experiment_id: str) -> Optional[CheckpointData]:
        """
        Retorna checkpoint mais recente de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            CheckpointData ou None se não existe
        """
        checkpoints = self.list_checkpoints(experiment_id)
        
        if not checkpoints:
            return None
        
        # Último checkpoint (maior geração)
        latest = checkpoints[-1]
        return self.load_checkpoint(latest.id)
    
    def get_checkpoint_by_generation(self,
                                    experiment_id: str,
                                    generation: int) -> Optional[CheckpointData]:
        """
        Retorna checkpoint de uma geração específica
        
        Args:
            experiment_id: ID do experimento
            generation: Número da geração
        
        Returns:
            CheckpointData ou None se não existe
        """
        checkpoints = self.list_checkpoints(experiment_id)
        
        for cp in checkpoints:
            if cp.generation == generation:
                return self.load_checkpoint(cp.id)
        
        return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de armazenamento
        
        Returns:
            Dict com estatísticas
        """
        total_size = 0
        total_checkpoints = 0
        experiments = 0
        
        for exp_dir in self.base_path.iterdir():
            if not exp_dir.is_dir():
                continue
            
            experiments += 1
            
            for file_path in exp_dir.glob("*.pkl"):
                total_size += file_path.stat().st_size
                total_checkpoints += 1
        
        return {
            "total_experiments": experiments,
            "total_checkpoints": total_checkpoints,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "avg_checkpoint_size_mb": (total_size / total_checkpoints / (1024 * 1024)) 
                                      if total_checkpoints > 0 else 0
        }
