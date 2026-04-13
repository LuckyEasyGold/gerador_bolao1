from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.cache.feature_cache import FeatureCache

router = APIRouter(prefix="/features", tags=["features"])


@router.post("/calculate")
async def calculate_features(
    use_cache: bool = Query(True, description="Usar cache se disponível"),
    force_recalculate: bool = Query(False, description="Forçar recálculo"),
    db: Session = Depends(get_db)
):
    """
    Calcula todas as features históricas
    
    - Frequências de cada número
    - Atrasos (delays)
    - Repetições do último concurso
    - Matriz de afinidade
    """
    cache = FeatureCache()
    
    # Verifica cache
    if use_cache and not force_recalculate:
        cached = cache.get_all_features()
        if all(v is not None for v in cached.values()):
            return {
                "success": True,
                "source": "cache",
                "features": cached
            }
    
    # Busca concursos
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    # Calcula features
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # Serializa
    features_dict = engineer.to_dict()
    
    # Cacheia
    if use_cache:
        cache.set_all_features(features_dict)
    
    return {
        "success": True,
        "source": "calculated",
        "total_contests": len(contests),
        "features": features_dict
    }


@router.get("/frequency")
async def get_frequencies(
    use_cache: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Retorna frequências históricas de todos os números"""
    cache = FeatureCache()
    
    # Tenta cache
    if use_cache:
        cached = cache.get_frequency()
        if cached:
            return {
                "success": True,
                "source": "cache",
                "data": cached
            }
    
    # Calcula
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    freq_data = engineer.frequency_calc.to_dict()
    
    # Cacheia
    if use_cache:
        cache.set_frequency(freq_data)
    
    return {
        "success": True,
        "source": "calculated",
        "data": freq_data
    }


@router.get("/delay")
async def get_delays(
    use_cache: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Retorna atrasos (delays) de todos os números"""
    cache = FeatureCache()
    
    # Tenta cache
    if use_cache:
        cached = cache.get_delay()
        if cached:
            return {
                "success": True,
                "source": "cache",
                "data": cached
            }
    
    # Calcula
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    delay_data = engineer.delay_calc.to_dict()
    
    # Cacheia
    if use_cache:
        cache.set_delay(delay_data)
    
    return {
        "success": True,
        "source": "calculated",
        "data": delay_data
    }


@router.get("/affinity")
async def get_affinity_matrix(
    use_cache: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Retorna matriz de afinidade (co-ocorrência) entre números"""
    cache = FeatureCache()
    
    # Tenta cache
    if use_cache:
        cached = cache.get_affinity()
        if cached:
            return {
                "success": True,
                "source": "cache",
                "data": cached
            }
    
    # Calcula
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    affinity_data = engineer.affinity_matrix.to_dict()
    
    # Cacheia
    if use_cache:
        cache.set_affinity(affinity_data)
    
    return {
        "success": True,
        "source": "calculated",
        "data": affinity_data
    }


@router.get("/repetition")
async def get_repetitions(
    use_cache: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Retorna números do último concurso (repetições)"""
    cache = FeatureCache()
    
    # Tenta cache
    if use_cache:
        cached = cache.get("repetition")
        if cached:
            return {
                "success": True,
                "source": "cache",
                "data": cached
            }
    
    # Calcula
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    rep_data = engineer.repetition_detector.to_dict()
    
    # Cacheia
    if use_cache:
        cache.set("repetition", rep_data)
    
    return {
        "success": True,
        "source": "calculated",
        "data": rep_data
    }


@router.get("/scores")
async def compute_scores(
    wf: float = Query(0.5, ge=-1.0, le=1.0, description="Peso frequência"),
    wa: float = Query(0.3, ge=-1.0, le=1.0, description="Peso atraso"),
    wr: float = Query(0.2, ge=-1.0, le=1.0, description="Peso repetição"),
    db: Session = Depends(get_db)
):
    """
    Calcula scores para todos os números usando pesos fornecidos
    
    Útil para testar diferentes combinações de pesos
    """
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    weights = {'wf': wf, 'wa': wa, 'wr': wr}
    scores = engineer.compute_all_scores(weights)
    
    # Cria lista com número e score
    scored_numbers = [
        {"number": i + 1, "score": float(scores[i])}
        for i in range(25)
    ]
    
    # Ordena por score decrescente
    scored_numbers.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "success": True,
        "weights": weights,
        "scores": scored_numbers
    }


@router.get("/number/{number}")
async def get_number_features(
    number: int = Query(..., ge=1, le=25),
    db: Session = Depends(get_db)
):
    """Retorna todas as features de um número específico"""
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # Features do número
    frequency = engineer.frequency_calc.get_frequency(number)
    delay = engineer.delay_calc.get_delay(number)
    repeated = engineer.repetition_detector.is_repeated(number)
    
    # Melhores companheiros
    companions = engineer.affinity_matrix.get_best_companions(number, k=5)
    
    return {
        "number": number,
        "frequency": frequency,
        "delay": delay,
        "is_repeated": repeated,
        "best_companions": [
            {"number": n, "affinity": float(a)}
            for n, a in companions
        ]
    }


@router.delete("/cache")
async def clear_cache(
    feature_type: Optional[str] = Query(None, description="Tipo específico ou None para todos")
):
    """Limpa cache de features"""
    cache = FeatureCache()
    
    count = cache.invalidate_all(feature_type)
    
    return {
        "success": True,
        "deleted_keys": count,
        "message": f"Cache limpo: {count} chaves removidas"
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """Retorna estatísticas do cache"""
    cache = FeatureCache()
    stats = cache.get_cache_stats()
    
    return {
        "success": True,
        "stats": stats
    }
