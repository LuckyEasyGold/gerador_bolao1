"""
Rotas da API - Sistema de Pool e Geração de Bolões v2 (Refatorado)
Processa simplificado e direto
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.pool_genetic_algorithm import PoolGeneticAlgorithm
from backend.core.pool_cache_manager import PoolCacheManager
from backend.core.simple_ticket_generator import calcular_distribuicao_orcamento, SimpleBolao

router = APIRouter(prefix="/bolao", tags=["bolao-v2"])

# Gerenciam tasks em background
pool_finding_tasks: Dict[str, dict] = {}
cache_manager = PoolCacheManager()


class FindOptimalPoolRequest(BaseModel):
    """Request para encontrar pool ótimo"""
    name: str = Field(..., min_length=1, max_length=255, description="Nome da otimização")
    generations: int = Field(default=20, ge=10, le=100, description="Gerações GA")
    population_size: int = Field(default=10, ge=5, le=30, description="Tamanho população")
    simulations: int = Field(default=500, ge=100, le=2000, description="Simulações por pool")
    seed: Optional[int] = Field(None, description="Seed para reprodutibilidade")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Pool Ótimo Lotofácil",
                "generations": 20,
                "population_size": 10,
                "simulations": 500
            }
        }


class GerarBolaoRequest(BaseModel):
    """Request para gerar bolão"""
    valor_total_do_bolao: float = Field(gt=0, description="Valor total em reais")
    cotas: int = Field(gt=0, le=100, description="Número de cotas")
    valor_unitario_do_bolao: float = Field(gt=0, description="Valor por cota")
    usar_pool_cache: bool = Field(default=True, description="Usar pool em cache (True) ou todos números (False)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valor_total_do_bolao": 1000.0,
                "cotas": 5,
                "valor_unitario_do_bolao": 200.0,
                "usar_pool_cache": True
            }
        }


@router.post("/pool/encontrar")
async def encontrar_pool_otimo(
    request: FindOptimalPoolRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Encontra o pool ótimo de números usando GA
    
    Executa em background e retorna ID para acompanhamento
    
    - Evolui apenas UMA coisa: qual pool de números é melhor
    - Muito mais rápido que GA anterior (20-30 gerações, ~2 minutos)
    - Salva resultado em cache para reutilização
    """
    # Busca concursos
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    # Cria ID único para tarefa
    task_id = str(uuid.uuid4())
    
    # Armazena status inicial
    pool_finding_tasks[task_id] = {
        "id": task_id,
        "name": request.name,
        "status": "iniciando",
        "progress": 0,
        "best_pool": None,
        "best_fitness": None,
        "best_roi": None,
        "generation_stats": [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Executa em background
    background_tasks.add_task(
        _executar_busca_pool,
        task_id,
        contests,
        request
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Busca de pool ótimo iniciada em background",
        "config": {
            "generations": request.generations,
            "population_size": request.population_size,
            "simulations": request.simulations
        }
    }


def _executar_busca_pool(task_id: str, contests: List, request: FindOptimalPoolRequest):
    """Executa GA em background"""
    try:
        pool_finding_tasks[task_id]["status"] = "executando"
        
        # Callback para atualizar progresso
        def progress_callback(generation, population, stats):
            best = max(population, key=lambda x: x.fitness)
            pool_finding_tasks[task_id].update({
                "progress": int((generation / request.generations) * 100),
                "current_generation": generation,
                "best_pool": best.pool,
                "best_fitness": float(best.fitness),
                "best_roi": float(best.roi)
            })
        
        # Executa GA
        ga = PoolGeneticAlgorithm(
            contests=contests,
            population_size=request.population_size,
            generations=request.generations,
            simulations=request.simulations,
            mutation_rate=0.3,
            elitism_rate=0.2,
            seed=request.seed,
            callback=progress_callback
        )
        
        result = ga.evolve()
        
        # Salva em cache
        cache_manager.save_pool(
            pool=result.best_pool,
            fitness=result.best_fitness,
            roi=result.best_roi,
            metadata={
                "generations": result.generations_run,
                "total_time": result.total_time,
                "task_id": task_id,
                "name": request.name
            }
        )
        
        # Atualiza resultado
        pool_finding_tasks[task_id].update({
            "status": "concluído",
            "progress": 100,
            "best_pool": result.best_pool,
            "best_fitness": float(result.best_fitness),
            "best_roi": float(result.best_roi),
            "generation_stats": [s.to_dict() for s in result.generation_stats],
            "total_time": result.total_time,
            "completed_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        pool_finding_tasks[task_id].update({
            "status": "erro",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })


@router.get("/pool/status/{task_id}")
async def status_busca_pool(task_id: str):
    """
    Consulta status da busca de pool
    
    Retorna progresso e melhor pool encontrado até agora
    """
    if task_id not in pool_finding_tasks:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    return pool_finding_tasks[task_id]


@router.get("/pool/otimo")
async def obter_pool_otimo():
    """
    Retorna pool ótimo em cache
    
    Se não existir, retorna None com instruções de como encontrar um
    """
    pool_data = cache_manager.load_pool()
    
    if not pool_data:
        return {
            "sucesso": False,
            "pool": None,
            "mensagem": "Nenhum pool em cache. Execute /bolao/pool/encontrar primeiro"
        }
    
    return {
        "sucesso": True,
        "pool": pool_data["pool"],
        "pool_size": pool_data["pool_size"],
        "fitness": pool_data["fitness"],
        "roi": pool_data["roi"],
        "timestamp": pool_data["timestamp"]
    }


@router.post("/gerar")
async def gerar_bolao(request: GerarBolaoRequest):
    """
    Gera bolão com distribuição de j15, j16, j17
    
    ENTRADA:
    - valor_total_do_bolao: Total a investir (ex: R$ 1000)
    - cotas: Número de cotas (ex: 5)
    - valor_unitario_do_bolao: Valor por cota (ex: R$ 200)
    
    SAÍDA:
    - j15: Quantidade de jogos com 15 números
    - j16: Quantidade de jogos com 16 números
    - j17: Quantidade de jogos com 17 números
    
    TEMPO: <100ms (instantâneo)
    """
    # Carrega pool ótimo se usar cache
    pool = None
    if request.usar_pool_cache:
        pool_data = cache_manager.load_pool()
        if pool_data:
            pool = pool_data["pool"]
    
    # Gera bolão
    resultado = calcular_distribuicao_orcamento(
        valor_total=request.valor_total_do_bolao,
        valor_unitario=request.valor_unitario_do_bolao,
        pool=pool
    )
    
    return {
        "sucesso": True,
        "entrada": {
            "valor_total_do_bolao": request.valor_total_do_bolao,
            "cotas": request.cotas,
            "valor_unitario_do_bolao": request.valor_unitario_do_bolao
        },
        "saida": resultado.to_dict(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/pool/historico")
async def listar_historico_pools(limit: int = Query(10, ge=1, le=50)):
    """
    Lista histórico de pools encontrados
    
    Args:
        limit: Quantos registros retornar (máximo 50)
    """
    pools = cache_manager.get_pool_list(limit=limit)
    
    return {
        "total": len(pools),
        "pools": pools
    }


@router.delete("/pool/cache")
async def limpar_cache_pool():
    """Remove pool do cache (força novas buscas)"""
    cache_manager.clear_cache()
    
    return {
        "sucesso": True,
        "mensagem": "Cache de pool removido"
    }
