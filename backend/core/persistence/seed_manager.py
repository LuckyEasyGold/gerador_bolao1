"""
SeedManager - Gerenciamento de Seeds
Garante reprodutibilidade através de versionamento de seeds
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import hashlib


@dataclass
class SeedRecord:
    """Registro de seed"""
    experiment_id: str
    component: str
    seed: int
    created_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "component": self.component,
            "seed": self.seed,
            "created_at": self.created_at.isoformat()
        }


class SeedManager:
    """
    Gerencia seeds para reprodutibilidade
    
    Mantém registro de todas as seeds utilizadas em cada
    componente de cada experimento, garantindo replay exato.
    """
    
    # Componentes padrão que usam seeds
    COMPONENTS = [
        "master",
        "population",
        "selector",
        "operators",
        "evaluator",
        "monte_carlo",
        "game_generator",
        "feature_engineer"
    ]
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: Diretório base para seeds
        """
        self.base_path = Path(base_path or "data/seeds")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def register_seed(self,
                     experiment_id: str,
                     component: str,
                     seed: int) -> None:
        """
        Registra seed de um componente
        
        Args:
            experiment_id: ID do experimento
            component: Nome do componente
            seed: Valor da seed
        """
        # Carrega seeds existentes
        seeds = self.get_seeds(experiment_id)
        
        # Adiciona nova seed
        seeds[component] = seed
        
        # Salva
        self._save_seeds(experiment_id, seeds)
    
    def get_seeds(self, experiment_id: str) -> Dict[str, int]:
        """
        Retorna todas as seeds de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            Dict {component: seed}
        """
        file_path = self.base_path / f"{experiment_id}.json"
        
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return data.get("seeds", {})
    
    def get_seed(self, experiment_id: str, component: str) -> Optional[int]:
        """
        Retorna seed de um componente específico
        
        Args:
            experiment_id: ID do experimento
            component: Nome do componente
        
        Returns:
            Seed ou None se não existe
        """
        seeds = self.get_seeds(experiment_id)
        return seeds.get(component)
    
    def validate_seeds(self, experiment_id: str) -> bool:
        """
        Valida se todas as seeds necessárias estão registradas
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            True se válido, False caso contrário
        """
        seeds = self.get_seeds(experiment_id)
        
        # Verifica se master seed existe
        if "master" not in seeds:
            return False
        
        # Verifica componentes principais
        required = ["population", "selector", "operators", "monte_carlo"]
        
        for component in required:
            if component not in seeds:
                return False
        
        return True
    
    def generate_seed_chain(self,
                           master_seed: int,
                           components: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Gera chain de seeds a partir de master seed
        
        Usa hash determinístico para gerar seeds únicas
        para cada componente a partir da master seed.
        
        Args:
            master_seed: Seed principal
            components: Lista de componentes (usa padrão se None)
        
        Returns:
            Dict {component: seed}
        """
        if components is None:
            components = self.COMPONENTS
        
        seeds = {"master": master_seed}
        
        for i, component in enumerate(components):
            if component == "master":
                continue
            
            # Gera seed determinística usando hash
            data = f"{master_seed}:{component}:{i}".encode()
            hash_value = hashlib.sha256(data).hexdigest()
            seed = int(hash_value[:16], 16) % (2**31 - 1)
            
            seeds[component] = seed
        
        return seeds
    
    def register_seed_chain(self,
                           experiment_id: str,
                           master_seed: int,
                           components: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Gera e registra chain completa de seeds
        
        Args:
            experiment_id: ID do experimento
            master_seed: Seed principal
            components: Lista de componentes
        
        Returns:
            Dict com todas as seeds geradas
        """
        seeds = self.generate_seed_chain(master_seed, components)
        
        # Registra todas
        for component, seed in seeds.items():
            self.register_seed(experiment_id, component, seed)
        
        return seeds
    
    def compare_seeds(self,
                     experiment_id1: str,
                     experiment_id2: str) -> Dict[str, bool]:
        """
        Compara seeds de dois experimentos
        
        Args:
            experiment_id1: ID do primeiro experimento
            experiment_id2: ID do segundo experimento
        
        Returns:
            Dict {component: são_iguais}
        """
        seeds1 = self.get_seeds(experiment_id1)
        seeds2 = self.get_seeds(experiment_id2)
        
        all_components = set(seeds1.keys()) | set(seeds2.keys())
        
        comparison = {}
        for component in all_components:
            seed1 = seeds1.get(component)
            seed2 = seeds2.get(component)
            comparison[component] = (seed1 == seed2)
        
        return comparison
    
    def get_seed_hash(self, experiment_id: str) -> str:
        """
        Retorna hash único das seeds de um experimento
        
        Útil para verificação rápida de reprodutibilidade
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            Hash SHA256 das seeds
        """
        seeds = self.get_seeds(experiment_id)
        
        # Ordena para garantir determinismo
        sorted_seeds = sorted(seeds.items())
        
        # Gera hash
        data = json.dumps(sorted_seeds).encode()
        return hashlib.sha256(data).hexdigest()
    
    def list_experiments(self) -> List[str]:
        """
        Lista todos os experimentos com seeds registradas
        
        Returns:
            Lista de IDs de experimentos
        """
        experiments = []
        
        for file_path in self.base_path.glob("*.json"):
            experiment_id = file_path.stem
            experiments.append(experiment_id)
        
        return sorted(experiments)
    
    def delete_seeds(self, experiment_id: str) -> bool:
        """
        Deleta seeds de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            True se deletado, False se não encontrado
        """
        file_path = self.base_path / f"{experiment_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def _save_seeds(self, experiment_id: str, seeds: Dict[str, int]) -> None:
        """Salva seeds em arquivo"""
        file_path = self.base_path / f"{experiment_id}.json"
        
        data = {
            "experiment_id": experiment_id,
            "seeds": seeds,
            "updated_at": datetime.now().isoformat(),
            "seed_hash": self._calculate_hash(seeds)
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _calculate_hash(self, seeds: Dict[str, int]) -> str:
        """Calcula hash das seeds"""
        sorted_seeds = sorted(seeds.items())
        data = json.dumps(sorted_seeds).encode()
        return hashlib.sha256(data).hexdigest()
