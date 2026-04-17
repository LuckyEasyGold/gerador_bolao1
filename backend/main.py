from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.database.connection import SessionLocal, init_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.api.routes import contests, features, games, simulate, optimize, persistence, pool_v2
from backend.utils.data_importer import LotofacilDataImporter
from backend.core.lottery_fetcher import LotteryFetcherService

settings = get_settings()

app = FastAPI(
    title="Lotofácil Optimizer API",
    description="Sistema de otimização evolutiva para bolões da Lotofácil",
    version="0.6.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar adequadamente em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(contests.router)
app.include_router(features.router)
app.include_router(games.router)
app.include_router(simulate.router)
app.include_router(optimize.router)
app.include_router(persistence.router)
app.include_router(pool_v2.router)


async def bootstrap_contests_if_needed() -> dict:
    """Sincroniza concursos quando o banco sobe vazio."""
    if not settings.auto_sync_contests_on_startup:
        return {"status": "disabled"}

    db = SessionLocal()

    try:
        repo = ContestRepository(db)
        existing_contests = repo.count()

        if existing_contests > 0:
            return {"status": "skipped", "existing_contests": existing_contests}

        importer = LotofacilDataImporter(db)
        imported = await importer.sync_latest()

        return {"status": "imported", "imported_contests": imported}
    except Exception as exc:
        db.rollback()
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    init_db()
    print("✓ Banco de dados inicializado")

    bootstrap_result = await bootstrap_contests_if_needed()

    if bootstrap_result["status"] == "imported":
        print(
            f"✓ Bootstrap de concursos concluído ({bootstrap_result['imported_contests']} importados)"
        )
    elif bootstrap_result["status"] == "skipped":
        print(
            f"✓ Bootstrap de concursos ignorado ({bootstrap_result['existing_contests']} já existentes)"
        )
    elif bootstrap_result["status"] == "disabled":
        print("• Bootstrap automático de concursos desabilitado")
    else:
        print(
            f"⚠ Falha ao sincronizar concursos automaticamente: {bootstrap_result['error']}"
        )


@app.get("/")
async def root():
    return {
        "name": "Lotofácil Optimizer API",
        "version": "0.6.0",
        "status": "operational",
        "phases_completed": 6,
        "total_phases": 7,
        "progress": "86%"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
