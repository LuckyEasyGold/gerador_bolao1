from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.game_generator import TicketGenerator, GameGenerator
from backend.models.dna import DNA, DNAGene

router = APIRouter(prefix="/games", tags=["games"])


class GenerateRequest(BaseModel):
    """Request para geração de bolão"""
    budget: float = Field(gt=0, description="Orçamento em reais")
    dna: Optional[dict] = Field(None, description="DNA customizado (opcional)")
    seed: Optional[int] = Field(None, description="Seed para reprodutibilidade")
    
    class Config:
        json_schema_extra = {
            "example": {
                "budget": 100.0,
                "seed": 42
            }
        }


class GenerateGameRequest(BaseModel):
    """Request para geração de jogo individual"""
    size: int = Field(ge=15, le=20, description="Tamanho do jogo")
    dna: Optional[dict] = Field(None, description="DNA customizado (opcional)")
    pool: Optional[list[int]] = Field(None, description="Pool de números (opcional)")
    seed: Optional[int] = Field(None, description="Seed para reprodutibilidade")


@router.post("/generate")
async def generate_ticket(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Gera bolão completo otimizado
    
    - Respeita orçamento fornecido
    - Usa DNA evolutivo (padrão ou customizado)
    - Otimiza diversidade e cobertura
    - Reproduzível com seed
    """
    # Busca concursos
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    # Calcula features
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # Cria DNA
    if request.dna:
        try:
            dna = DNA(genes=DNAGene(**request.dna))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DNA inválido: {str(e)}")
    else:
        # DNA padrão balanceado
        dna = DNA(genes=DNAGene(
            w15=0.4, w16=0.3, w17=0.3,
            wf=0.4, wa=0.3, wr=0.3, wc_aff=1.0,
            T_base=1.0, kappa=0.3,
            wp=0.3, wl=0.3, ws=0.2, wo=0.2,
            wcov=0.4, wd=0.4, woverlap=0.2,
            pool_size=20, candidates_per_game=50, refine_iterations=100
        ))
    
    # Gera ticket
    generator = TicketGenerator(engineer, dna, seed=request.seed)
    ticket = generator.generate_ticket(budget=request.budget)
    
    return {
        "success": True,
        "ticket": ticket.to_dict(),
        "dna_used": dna.genes.to_dict(),
        "seed": request.seed
    }


@router.post("/generate/game")
async def generate_single_game(
    request: GenerateGameRequest,
    db: Session = Depends(get_db)
):
    """
    Gera um jogo individual
    
    Útil para testar geração ou criar jogos customizados
    """
    # Busca concursos
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    # Calcula features
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # Cria DNA
    if request.dna:
        try:
            dna = DNA(genes=DNAGene(**request.dna))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DNA inválido: {str(e)}")
    else:
        dna = DNA(genes=DNAGene.random())
    
    # Valida pool se fornecido
    if request.pool:
        if len(request.pool) < request.size:
            raise HTTPException(
                status_code=400,
                detail=f"Pool deve ter pelo menos {request.size} números"
            )
        if not all(1 <= n <= 25 for n in request.pool):
            raise HTTPException(
                status_code=400,
                detail="Números do pool devem estar entre 1 e 25"
            )
    
    # Gera jogo
    generator = GameGenerator(engineer, dna, seed=request.seed)
    game = generator.generate_game(size=request.size, pool=request.pool)
    
    return {
        "success": True,
        "game": game.to_dict(),
        "dna_used": dna.genes.to_dict()
    }


@router.get("/simulate/budget")
async def simulate_budget_distribution(
    budget: float = Query(..., gt=0, description="Orçamento em reais"),
    w15: float = Query(0.4, ge=0, le=1, description="Peso jogos de 15"),
    w16: float = Query(0.3, ge=0, le=1, description="Peso jogos de 16"),
    w17: float = Query(0.3, ge=0, le=1, description="Peso jogos de 17")
):
    """
    Simula distribuição de orçamento sem gerar jogos
    
    Útil para planejar estratégia antes de gerar
    """
    from backend.config import get_settings
    settings = get_settings()
    
    # Normaliza pesos
    total_weight = w15 + w16 + w17
    if total_weight == 0:
        w15 = w16 = w17 = 1/3
    else:
        w15 /= total_weight
        w16 /= total_weight
        w17 /= total_weight
    
    # Distribui orçamento
    budget_15 = budget * w15
    budget_16 = budget * w16
    budget_17 = budget * w17
    
    # Calcula quantidades
    count_15 = int(budget_15 / settings.cost_15)
    count_16 = int(budget_16 / settings.cost_16)
    count_17 = int(budget_17 / settings.cost_17)
    
    # Custo real
    cost_15 = count_15 * settings.cost_15
    cost_16 = count_16 * settings.cost_16
    cost_17 = count_17 * settings.cost_17
    total_cost = cost_15 + cost_16 + cost_17
    
    # Restante
    remaining = budget - total_cost
    extra_15 = int(remaining / settings.cost_15)
    
    if extra_15 > 0:
        count_15 += extra_15
        cost_15 += extra_15 * settings.cost_15
        total_cost += extra_15 * settings.cost_15
        remaining = budget - total_cost
    
    return {
        "budget": budget,
        "distribution": {
            "size_15": {
                "count": count_15,
                "cost": cost_15,
                "percentage": (cost_15 / total_cost * 100) if total_cost > 0 else 0
            },
            "size_16": {
                "count": count_16,
                "cost": cost_16,
                "percentage": (cost_16 / total_cost * 100) if total_cost > 0 else 0
            },
            "size_17": {
                "count": count_17,
                "cost": cost_17,
                "percentage": (cost_17 / total_cost * 100) if total_cost > 0 else 0
            }
        },
        "total_games": count_15 + count_16 + count_17,
        "total_cost": total_cost,
        "remaining": remaining
    }


@router.get("/costs")
async def get_game_costs():
    """Retorna custos de jogos por tamanho"""
    from backend.config import get_settings
    settings = get_settings()
    
    return {
        "costs": {
            15: settings.cost_15,
            16: settings.cost_16,
            17: settings.cost_17,
            18: settings.cost_18,
            19: settings.cost_19,
            20: settings.cost_20
        },
        "currency": "BRL"
    }


@router.post("/validate")
async def validate_game(
    numbers: list[int] = Query(..., description="Números do jogo")
):
    """
    Valida um jogo
    
    Verifica:
    - Quantidade de números
    - Range válido (1-25)
    - Sem duplicatas
    """
    errors = []
    
    # Quantidade
    if len(numbers) < 15 or len(numbers) > 20:
        errors.append(f"Jogo deve ter entre 15 e 20 números (tem {len(numbers)})")
    
    # Range
    invalid = [n for n in numbers if n < 1 or n > 25]
    if invalid:
        errors.append(f"Números inválidos (fora de 1-25): {invalid}")
    
    # Duplicatas
    if len(numbers) != len(set(numbers)):
        duplicates = [n for n in numbers if numbers.count(n) > 1]
        errors.append(f"Números duplicados: {set(duplicates)}")
    
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "errors": errors if not is_valid else None,
        "numbers": sorted(numbers) if is_valid else None,
        "size": len(numbers)
    }
