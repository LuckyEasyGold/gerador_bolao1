"""
ReplayEngine - Motor de Replay de Experimentos
Permite replay completo e validação de reprodutibilidade
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from backend.core.genetic_algorithm import GeneticAlgorithm, EvolutionResult
from backend.core.feature_engineering import FeatureEngineer
from backend.core.persistence.checkpoint_manager import CheckpointManager
from backend.core.persistence.seed_manager import SeedManager
from backend.core.persistence.experiment_logger import ExperimentLogger


@dataclass
class ValidationReport:
    """Relatório de validação de reprodutibilidade"""
    is_reproducible: bool
    original_experiment_id: str
    replay_experiment_id: str
    differences: List[Dict[str, Any]]
    original_result: Dict[str, Any]
    replay_result: Dict[str, Any]
    validation_time: float
    
    def to_dict(self) -> dict:
        return {
            "is_reproducible": self.is_reproducible,
            "original_experiment_id": self.original_experiment_id,
            "replay_experiment_id": self.replay_experiment_id,
            "differences": self.differences,
            "original_result": self.original_result,
            "replay_result": self.replay_result,
            "validation_time": self.validation_time
        }


@dataclass
class ComparisonReport:
    """Relatório de comparação entre experimentos"""
    experiment_id1: str
    experiment_id2: str
    fitness_diff: float
    roi_diff: float
    generations_diff: int
    time_diff: float
    seeds_match: bool
    detailed_comparison: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "experiment_id1": self.experiment_id1,
            "experiment_id2": self.experiment_id2,
            "fitness_diff": self.fitness_diff,
            "roi_diff": self.roi_diff,
            "generations_diff": self.generations_diff,
            "time_diff": self.time_diff,
            "seeds_match": self.seeds_match,
            "detailed_comparison": self.detailed_comparison
        }


class ReplayEngine:
    """
    Motor de replay de experimentos
    
    Permite:
    - Replay completo de experimentos
    - Replay a partir de checkpoints
    - Validação de reprodutibilidade
    - Comparação de resultados
    """
    
    def __init__(self,
                 checkpoint_manager: Optional[CheckpointManager] = None,
                 seed_manager: Optional[SeedManager] = None,
                 logger: Optional[ExperimentLogger] = None):
        """
        Args:
            checkpoint_manager: Gerenciador de checkpoints
            seed_manager: Gerenciador de seeds
            logger: Logger de experimentos
        """
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.seed_manager = seed_manager or SeedManager()
        self.logger = logger or ExperimentLogger()
    
    def replay_experiment(self,
                         experiment_id: str,
                         engineer: FeatureEngineer) -> EvolutionResult:
        """
        Replay completo de um experimento
        
        Usa as mesmas seeds e configurações do experimento original
        para garantir reprodutibilidade exata.
        
        Args:
            experiment_id: ID do experimento original
            engineer: FeatureEngineer fitted
        
        Returns:
            EvolutionResult do replay
        
        Raises:
            ValueError: Se experimento não tem seeds registradas
        """
        # Carrega seeds originais
        seeds = self.seed_manager.get_seeds(experiment_id)
        
        if not seeds:
            raise ValueError(f"Experimento {experiment_id} não tem seeds registradas")
        
        # Carrega primeiro checkpoint para pegar config
        checkpoints = self.checkpoint_manager.list_checkpoints(experiment_id)
        
        if not checkpoints:
            raise ValueError(f"Experimento {experiment_id} não tem checkpoints")
        
        first_checkpoint = self.checkpoint_manager.load_checkpoint(checkpoints[0].id)
        config = first_checkpoint.config
        
        # Cria GA com mesmas configurações e seeds
        ga = GeneticAlgorithm(
            engineer=engineer,
            budget=config["budget"],
            population_size=config["population_size"],
            generations=config["generations"],
            mutation_rate=config.get("mutation_rate", 0.1),
            mutation_strength=config.get("mutation_strength", 0.2),
            crossover_rate=config.get("crossover_rate", 0.7),
            elitism_rate=config.get("elitism_rate", 0.1),
            tournament_size=config.get("tournament_size", 3),
            simulations=config.get("simulations", 1000),
            convergence_threshold=config.get("convergence_threshold", 0.001),
            convergence_patience=config.get("convergence_patience", 10),
            seed=seeds.get("master")
        )
        
        # Executa replay
        print(f"Iniciando replay do experimento {experiment_id}...")
        result = ga.evolve()
        print(f"Replay concluído!")
        
        return result
    
    def replay_from_checkpoint(self,
                               checkpoint_id: str,
                               engineer: FeatureEngineer,
                               additional_generations: int = 10) -> EvolutionResult:
        """
        Replay a partir de um checkpoint
        
        Carrega estado de um checkpoint e continua evolução.
        
        Args:
            checkpoint_id: ID do checkpoint
            engineer: FeatureEngineer fitted
            additional_generations: Gerações adicionais a executar
        
        Returns:
            EvolutionResult do replay
        """
        # Carrega checkpoint
        checkpoint = self.checkpoint_manager.load_checkpoint(checkpoint_id)
        
        # Cria GA com configuração do checkpoint
        config = checkpoint.config
        seeds = checkpoint.seeds
        
        ga = GeneticAlgorithm(
            engineer=engineer,
            budget=config["budget"],
            population_size=config["population_size"],
            generations=additional_generations,
            mutation_rate=config.get("mutation_rate", 0.1),
            mutation_strength=config.get("mutation_strength", 0.2),
            crossover_rate=config.get("crossover_rate", 0.7),
            elitism_rate=config.get("elitism_rate", 0.1),
            tournament_size=config.get("tournament_size", 3),
            simulations=config.get("simulations", 1000),
            seed=seeds.get("master")
        )
        
        # Restaura população
        ga.population = checkpoint.population
        
        # Continua evolução
        print(f"Continuando de geração {checkpoint.generation}...")
        result = ga.evolve()
        
        return result
    
    def validate_reproducibility(self,
                                experiment_id: str,
                                engineer: FeatureEngineer,
                                tolerance: float = 1e-6) -> ValidationReport:
        """
        Valida reprodutibilidade de um experimento
        
        Executa replay e compara resultados bit-a-bit.
        
        Args:
            experiment_id: ID do experimento
            engineer: FeatureEngineer fitted
            tolerance: Tolerância para comparação de floats
        
        Returns:
            ValidationReport com resultado da validação
        """
        start_time = datetime.now()
        
        # Carrega resultado original
        latest_checkpoint = self.checkpoint_manager.get_latest_checkpoint(experiment_id)
        
        if not latest_checkpoint:
            raise ValueError(f"Experimento {experiment_id} não tem checkpoints")
        
        original_result = {
            "best_fitness": latest_checkpoint.stats.best_fitness,
            "avg_fitness": latest_checkpoint.stats.avg_fitness,
            "best_roi": latest_checkpoint.stats.best_roi,
            "generation": latest_checkpoint.generation
        }
        
        # Executa replay
        replay_result_obj = self.replay_experiment(experiment_id, engineer)
        
        replay_result = {
            "best_fitness": replay_result_obj.best_fitness,
            "avg_fitness": replay_result_obj.generation_stats[-1].avg_fitness,
            "best_roi": replay_result_obj.best_dna.roi,
            "generation": replay_result_obj.generations_run
        }
        
        # Compara resultados
        differences = []
        
        for key in original_result:
            orig_val = original_result[key]
            replay_val = replay_result[key]
            
            if isinstance(orig_val, float):
                diff = abs(orig_val - replay_val)
                if diff > tolerance:
                    differences.append({
                        "field": key,
                        "original": orig_val,
                        "replay": replay_val,
                        "difference": diff
                    })
            elif orig_val != replay_val:
                differences.append({
                    "field": key,
                    "original": orig_val,
                    "replay": replay_val
                })
        
        validation_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationReport(
            is_reproducible=(len(differences) == 0),
            original_experiment_id=experiment_id,
            replay_experiment_id=f"{experiment_id}_replay",
            differences=differences,
            original_result=original_result,
            replay_result=replay_result,
            validation_time=validation_time
        )
    
    def compare_results(self,
                       experiment_id1: str,
                       experiment_id2: str) -> ComparisonReport:
        """
        Compara resultados de dois experimentos
        
        Args:
            experiment_id1: ID do primeiro experimento
            experiment_id2: ID do segundo experimento
        
        Returns:
            ComparisonReport com comparação detalhada
        """
        # Carrega checkpoints finais
        cp1 = self.checkpoint_manager.get_latest_checkpoint(experiment_id1)
        cp2 = self.checkpoint_manager.get_latest_checkpoint(experiment_id2)
        
        if not cp1 or not cp2:
            raise ValueError("Um ou ambos experimentos não têm checkpoints")
        
        # Compara seeds
        seeds1 = self.seed_manager.get_seeds(experiment_id1)
        seeds2 = self.seed_manager.get_seeds(experiment_id2)
        seeds_match = (seeds1 == seeds2)
        
        # Calcula diferenças
        fitness_diff = cp1.stats.best_fitness - cp2.stats.best_fitness
        roi_diff = cp1.stats.best_roi - cp2.stats.best_roi
        generations_diff = cp1.generation - cp2.generation
        
        # Tempo (aproximado pelos timestamps)
        time_diff = (cp1.created_at - cp2.created_at).total_seconds()
        
        # Comparação detalhada
        detailed = {
            "experiment1": {
                "best_fitness": cp1.stats.best_fitness,
                "avg_fitness": cp1.stats.avg_fitness,
                "best_roi": cp1.stats.best_roi,
                "generation": cp1.generation,
                "diversity": cp1.stats.diversity
            },
            "experiment2": {
                "best_fitness": cp2.stats.best_fitness,
                "avg_fitness": cp2.stats.avg_fitness,
                "best_roi": cp2.stats.best_roi,
                "generation": cp2.generation,
                "diversity": cp2.stats.diversity
            }
        }
        
        return ComparisonReport(
            experiment_id1=experiment_id1,
            experiment_id2=experiment_id2,
            fitness_diff=fitness_diff,
            roi_diff=roi_diff,
            generations_diff=generations_diff,
            time_diff=time_diff,
            seeds_match=seeds_match,
            detailed_comparison=detailed
        )
