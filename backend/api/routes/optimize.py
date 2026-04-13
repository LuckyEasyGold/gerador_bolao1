from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict
from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.genetic_algorithm import GeneticAlgorithm
from backend.models.experiment import ExperimentConfig

router = APIRouter(prefix="/optimize", tags=["optimize"])

# Armazena experimentos em execução (em produção usar Redis/DB)
running_experiments: Dict[str, dict] = {}


class OptimizeRequest(BaseModel):
    """Request para otimização"""
    name: str = Field(..., min_length=1, max_length=255)
    budget: float = Field(gt=0, description="Orçamento em reais")
    config: Optional[ExperimentConfig] = None
    seed: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Otimização R$ 100",
                "budget": 100.0,
                "config": {
                    "population_size": 20,
                    "generations": 50,
                    "simulations": 1000
                },
                "seed": 42
            }
        }


@router.post("/start")
async def start_optimization(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Inicia otimização evolutiva
    
    - Executa em background
    - Retorna ID para acompanhamento
    - Evolui estratégia automaticamente
    """
    # Busca concursos
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    # Calcula features
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # Config padrão se não fornecida
    if request.config is None:
        config = ExperimentConfig(
            population_size=20,
            generations=50,
            simulations=1000
        )
    else:
        config = request.config
    
    # Cria ID único
    import uuid
    experiment_id = str(uuid.uuid4())
    
    # Armazena status inicial
    running_experiments[experiment_id] = {
        "id": experiment_id,
        "name": request.name,
        "budget": request.budget,
        "status": "starting",
        "progress": 0,
        "current_generation": 0,
        "best_fitness": None,
        "result": None
    }
    
    # Executa em background
    background_tasks.add_task(
        run_optimization,
        experiment_id,
        engineer,
        request.budget,
        config,
        request.seed
    )
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "message": "Otimização iniciada",
        "config": config.model_dump()
    }


def run_optimization(experiment_id: str, 
                    engineer: FeatureEngineer,
                    budget: float,
                    config: ExperimentConfig,
                    seed: Optional[int]):
    """Executa otimização (função auxiliar para background)"""
    try:
        # Atualiza status
        running_experiments[experiment_id]["status"] = "running"
        
        # Callback para atualizar progresso
        def progress_callback(generation: int, population):
            best = population.get_best(1)[0]
            running_experiments[experiment_id].update({
                "current_generation": generation,
                "progress": int((generation / config.generations) * 100),
                "best_fitness": float(best.fitness),
                "best_roi": float(best.roi)
            })
        
        # Cria e executa GA
        ga = GeneticAlgorithm(
            engineer=engineer,
            budget=budget,
            population_size=config.population_size,
            generations=config.generations,
            mutation_rate=config.mutation_rate,
            mutation_strength=config.mutation_strength,
            crossover_rate=config.crossover_rate,
            elitism_rate=config.elitism_rate,
            tournament_size=config.tournament_size,
            simulations=config.simulations,
            convergence_threshold=config.convergence_threshold,
            convergence_patience=config.convergence_generations,
            seed=seed,
            callback=progress_callback
        )
        
        result = ga.evolve()
        
        # Atualiza com resultado
        running_experiments[experiment_id].update({
            "status": "completed",
            "progress": 100,
            "result": result.to_dict()
        })
        
    except Exception as e:
        running_experiments[experiment_id].update({
            "status": "failed",
            "error": str(e)
        })


@router.get("/status/{experiment_id}")
async def get_optimization_status(experiment_id: str):
    """
    Consulta status de otimização
    
    Retorna progresso e melhor fitness atual
    """
    if experiment_id not in running_experiments:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    
    return running_experiments[experiment_id]


@router.get("/result/{experiment_id}")
async def get_optimization_result(experiment_id: str):
    """
    Retorna resultado completo da otimização
    
    Disponível apenas quando status = completed
    """
    if experiment_id not in running_experiments:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    
    experiment = running_experiments[experiment_id]
    
    if experiment["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Experimento ainda não concluído (status: {experiment['status']})"
        )
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "name": experiment["name"],
        "budget": experiment["budget"],
        "result": experiment["result"]
    }


@router.delete("/cancel/{experiment_id}")
async def cancel_optimization(experiment_id: str):
    """
    Cancela otimização em execução
    
    Remove do tracking
    """
    if experiment_id not in running_experiments:
        raise HTTPException(status_code=404, detail="Experimento não encontrado")
    
    experiment = running_experiments[experiment_id]
    
    if experiment["status"] == "completed":
        raise HTTPException(
            status_code=400,
            detail="Experimento já concluído, não pode ser cancelado"
        )
    
    # Remove
    del running_experiments[experiment_id]
    
    return {
        "success": True,
        "message": "Experimento cancelado"
    }


@router.get("/list")
async def list_experiments():
    """Lista todos os experimentos"""
    experiments = []
    
    for exp_id, exp_data in running_experiments.items():
        experiments.append({
            "id": exp_id,
            "name": exp_data["name"],
            "status": exp_data["status"],
            "progress": exp_data.get("progress", 0),
            "current_generation": exp_data.get("current_generation", 0),
            "best_fitness": exp_data.get("best_fitness")
        })
    
    return {
        "success": True,
        "total": len(experiments),
        "experiments": experiments
    }


@router.post("/quick")
async def quick_optimization(
    budget: float = Field(..., gt=0),
    db: Session = Depends(get_db)
):
    """
    Otimização rápida (síncrona)
    
    - População pequena (10)
    - Poucas gerações (10)
    - Poucas simulações (500)
    - Retorna resultado imediatamente
    
    Útil para testes rápidos
    """
    # Busca concursos
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    # Calcula features
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # GA rápido
    ga = GeneticAlgorithm(
        engineer=engineer,
        budget=budget,
        population_size=10,
        generations=10,
        simulations=500,
        seed=42
    )
    
    result = ga.evolve()
    
    return {
        "success": True,
        "budget": budget,
        "result": result.to_dict(),
        "note": "Otimização rápida - use /optimize/start para resultados melhores"
    }


@router.get("/config/default")
async def get_default_config():
    """Retorna configuração padrão"""
    config = ExperimentConfig()
    
    return {
        "config": config.model_dump(),
        "description": {
            "population_size": "Tamanho da população (10-1000)",
            "generations": "Número de gerações (1-10000)",
            "mutation_rate": "Taxa de mutação (0-1)",
            "mutation_strength": "Força da mutação (0-1)",
            "crossover_rate": "Taxa de crossover (0-1)",
            "elitism_rate": "Taxa de elitismo (0-0.5)",
            "tournament_size": "Tamanho do torneio (2-10)",
            "simulations": "Simulações Monte Carlo (100-100000)",
            "convergence_threshold": "Threshold de convergência (0-1)",
            "convergence_generations": "Gerações para convergência (1-100)"
        }
    }


@router.get("/config/presets")
async def get_config_presets():
    """Retorna presets de configuração"""
    return {
        "presets": {
            "fast": {
                "name": "Rápido",
                "description": "Otimização rápida para testes",
                "config": {
                    "population_size": 10,
                    "generations": 10,
                    "simulations": 500
                },
                "estimated_time": "~2 minutos"
            },
            "balanced": {
                "name": "Balanceado",
                "description": "Equilíbrio entre tempo e qualidade",
                "config": {
                    "population_size": 20,
                    "generations": 50,
                    "simulations": 1000
                },
                "estimated_time": "~10 minutos"
            },
            "thorough": {
                "name": "Completo",
                "description": "Otimização completa para melhores resultados",
                "config": {
                    "population_size": 50,
                    "generations": 100,
                    "simulations": 5000
                },
                "estimated_time": "~60 minutos"
            },
            "production": {
                "name": "Produção",
                "description": "Configuração para uso em produção",
                "config": {
                    "population_size": 100,
                    "generations": 200,
                    "simulations": 10000
                },
                "estimated_time": "~4 horas"
            }
        }
    }
