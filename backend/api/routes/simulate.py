from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from backend.core.monte_carlo import (
    MonteCarloSimulator, ParallelSimulator
)
from backend.core.game_generator import Game, Ticket

router = APIRouter(prefix="/simulate", tags=["simulate"])


class SimulateGameRequest(BaseModel):
    """Request para simular jogo"""
    numbers: List[int] = Field(..., min_length=15, max_length=20)
    cost: float = Field(gt=0)
    simulations: int = Field(default=10000, ge=100, le=100000)
    seed: Optional[int] = None
    use_parallel: bool = Field(default=False)


class SimulateTicketRequest(BaseModel):
    """Request para simular bolão"""
    games: List[dict] = Field(..., min_length=1)
    simulations: int = Field(default=10000, ge=100, le=100000)
    seed: Optional[int] = None
    use_parallel: bool = Field(default=False)
    calculate_risk: bool = Field(default=False)


@router.post("/game")
async def simulate_game(request: SimulateGameRequest):
    """
    Simula jogo individual via Monte Carlo
    
    - Executa N simulações de sorteios
    - Calcula ROI, Sharpe Ratio, Win Rate
    - Retorna distribuição de prêmios
    - Reproduzível com seed
    """
    # Valida números
    if len(request.numbers) != len(set(request.numbers)):
        raise HTTPException(status_code=400, detail="Números duplicados")
    
    if not all(1 <= n <= 25 for n in request.numbers):
        raise HTTPException(status_code=400, detail="Números devem estar entre 1 e 25")
    
    # Cria jogo
    game = Game(
        numbers=sorted(request.numbers),
        size=len(request.numbers),
        cost=request.cost
    )
    
    # Simula
    if request.use_parallel:
        simulator = ParallelSimulator(seed=request.seed)
        ticket = Ticket(games=[game], total_cost=game.cost, total_games=1)
        result = simulator.simulate_ticket_parallel(ticket, request.simulations)
    else:
        simulator = MonteCarloSimulator(seed=request.seed)
        result = simulator.simulate_game(game, request.simulations)
    
    return {
        "success": True,
        "game": game.to_dict(),
        "simulation": result.to_dict(),
        "seed": request.seed
    }


@router.post("/ticket")
async def simulate_ticket(request: SimulateTicketRequest):
    """
    Simula bolão completo via Monte Carlo
    
    - Avalia todos os jogos do bolão
    - Calcula métricas agregadas
    - Opcionalmente calcula métricas de risco detalhadas
    """
    # Valida e cria jogos
    games = []
    total_cost = 0.0
    
    for game_data in request.games:
        try:
            numbers = game_data["numbers"]
            size = len(numbers)
            cost = game_data.get("cost", 3.0)
            
            if len(numbers) != len(set(numbers)):
                raise ValueError("Números duplicados")
            
            if not all(1 <= n <= 25 for n in numbers):
                raise ValueError("Números devem estar entre 1 e 25")
            
            game = Game(numbers=sorted(numbers), size=size, cost=cost)
            games.append(game)
            total_cost += cost
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Jogo inválido: {str(e)}"
            )
    
    # Cria ticket
    ticket = Ticket(
        games=games,
        total_cost=total_cost,
        total_games=len(games)
    )
    
    # Simula
    if request.use_parallel:
        simulator = ParallelSimulator(seed=request.seed)
        result = simulator.simulate_ticket_parallel(ticket, request.simulations)
    else:
        simulator = MonteCarloSimulator(seed=request.seed)
        result = simulator.simulate_ticket(ticket, request.simulations)
    
    response = {
        "success": True,
        "ticket": ticket.to_dict(),
        "simulation": result.to_dict(),
        "seed": request.seed
    }
    
    # Calcula métricas de risco se solicitado
    if request.calculate_risk:
        simulator_risk = MonteCarloSimulator(seed=request.seed)
        risk_metrics = simulator_risk.calculate_risk_metrics(
            ticket, request.simulations
        )
        response["risk_metrics"] = risk_metrics
    
    return response


@router.post("/compare")
async def compare_tickets(
    tickets_data: List[dict],
    simulations: int = Query(10000, ge=100, le=100000),
    seed: Optional[int] = None
):
    """
    Compara múltiplos bolões usando CRN
    
    - Garante que todos são avaliados nos mesmos sorteios
    - Facilita comparação justa entre estratégias
    - Retorna resultados lado a lado
    """
    if len(tickets_data) < 2:
        raise HTTPException(
            status_code=400,
            detail="Forneça pelo menos 2 bolões para comparar"
        )
    
    # Cria tickets
    tickets = []
    for i, ticket_data in enumerate(tickets_data):
        try:
            games = []
            total_cost = 0.0
            
            for game_data in ticket_data["games"]:
                numbers = game_data["numbers"]
                size = len(numbers)
                cost = game_data.get("cost", 3.0)
                
                game = Game(numbers=sorted(numbers), size=size, cost=cost)
                games.append(game)
                total_cost += cost
            
            ticket = Ticket(
                games=games,
                total_cost=total_cost,
                total_games=len(games)
            )
            tickets.append(ticket)
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Bolão {i+1} inválido: {str(e)}"
            )
    
    # Compara usando CRN
    simulator = MonteCarloSimulator(seed=seed, use_crn=True)
    results = simulator.compare_tickets(tickets, simulations)
    
    # Formata resposta
    comparison = []
    for i, (ticket, result) in enumerate(zip(tickets, results)):
        comparison.append({
            "ticket_id": i + 1,
            "total_games": ticket.total_games,
            "total_cost": ticket.total_cost,
            "simulation": result.to_dict()
        })
    
    # Ranking por ROI
    ranking = sorted(
        comparison,
        key=lambda x: x["simulation"]["roi"],
        reverse=True
    )
    
    return {
        "success": True,
        "comparison": comparison,
        "ranking": [r["ticket_id"] for r in ranking],
        "best_ticket": ranking[0]["ticket_id"],
        "seed": seed
    }


@router.get("/benchmark")
async def benchmark_simulation(
    simulations: int = Query(10000, ge=100, le=100000),
    use_parallel: bool = Query(False)
):
    """
    Benchmark de performance do simulador
    
    Útil para estimar tempo de execução
    """
    import time
    
    # Cria ticket de teste
    games = [
        Game(numbers=list(range(1, 16)), size=15, cost=3.0),
        Game(numbers=list(range(11, 26)), size=15, cost=3.0)
    ]
    ticket = Ticket(games=games, total_cost=6.0, total_games=2)
    
    # Mede tempo
    start = time.time()
    
    if use_parallel:
        simulator = ParallelSimulator(seed=42)
        result = simulator.simulate_ticket_parallel(ticket, simulations)
    else:
        simulator = MonteCarloSimulator(seed=42)
        result = simulator.simulate_ticket(ticket, simulations)
    
    elapsed = time.time() - start
    
    return {
        "simulations": simulations,
        "elapsed_seconds": round(elapsed, 3),
        "simulations_per_second": int(simulations / elapsed),
        "use_parallel": use_parallel,
        "avg_return": result.avg_return,
        "roi": result.roi
    }


@router.get("/prize-table")
async def get_prize_table():
    """Retorna tabela de prêmios da Lotofácil"""
    from backend.config import get_settings
    settings = get_settings()
    
    return {
        "prizes": {
            15: {
                "hits": 15,
                "prize": settings.prize_15,
                "description": "15 acertos"
            },
            14: {
                "hits": 14,
                "prize": settings.prize_14,
                "description": "14 acertos"
            },
            13: {
                "hits": 13,
                "prize": settings.prize_13,
                "description": "13 acertos"
            },
            12: {
                "hits": 12,
                "prize": settings.prize_12,
                "description": "12 acertos"
            },
            11: {
                "hits": 11,
                "prize": settings.prize_11,
                "description": "11 acertos"
            }
        },
        "note": "Valores aproximados. Prêmios reais variam por concurso."
    }


@router.post("/expected-value")
async def calculate_expected_value(
    numbers: List[int] = Query(..., min_length=15, max_length=20),
    cost: float = Query(..., gt=0),
    simulations: int = Query(10000, ge=1000, le=100000)
):
    """
    Calcula valor esperado de um jogo
    
    EV = Retorno Médio - Custo
    """
    # Valida
    if len(numbers) != len(set(numbers)):
        raise HTTPException(status_code=400, detail="Números duplicados")
    
    if not all(1 <= n <= 25 for n in numbers):
        raise HTTPException(status_code=400, detail="Números inválidos")
    
    # Simula
    game = Game(numbers=sorted(numbers), size=len(numbers), cost=cost)
    simulator = MonteCarloSimulator(seed=42)
    result = simulator.simulate_game(game, simulations)
    
    ev = result.avg_return - cost
    
    return {
        "numbers": sorted(numbers),
        "cost": cost,
        "avg_return": result.avg_return,
        "expected_value": ev,
        "roi": result.roi,
        "win_rate": result.win_rate,
        "simulations": simulations,
        "interpretation": (
            "Positivo: jogo lucrativo em média" if ev > 0
            else "Negativo: jogo não lucrativo em média"
        )
    }
