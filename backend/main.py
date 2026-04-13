from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.database.connection import init_db
from backend.api.routes import contests, features, games, simulate, optimize, persistence

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


@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    init_db()
    print("✓ Banco de dados inicializado")


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
