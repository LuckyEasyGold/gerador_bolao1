from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.models.contest import Contest
from backend.utils.data_importer import LotofacilDataImporter

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("/", response_model=List[Contest])
def list_contests(
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    """Lista concursos históricos"""
    repo = ContestRepository(db)
    return repo.get_all(limit=limit)


@router.get("/latest", response_model=Contest)
def get_latest_contest(db: Session = Depends(get_db)):
    """Retorna o concurso mais recente"""
    repo = ContestRepository(db)
    contest = repo.get_latest()
    
    if not contest:
        raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
    
    return contest


@router.get("/{contest_id}", response_model=Contest)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    """Busca concurso por ID"""
    repo = ContestRepository(db)
    contest = repo.get_by_id(contest_id)
    
    if not contest:
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    
    return contest


@router.get("/stats/summary")
def get_stats(db: Session = Depends(get_db)):
    """Retorna estatísticas dos concursos"""
    repo = ContestRepository(db)
    count = repo.count()
    date_range = repo.get_date_range()
    
    return {
        "total_contests": count,
        "first_date": date_range[0],
        "last_date": date_range[1]
    }


@router.post("/import/sync")
async def sync_contests(db: Session = Depends(get_db)):
    """Sincroniza com concursos mais recentes da API Caixa"""
    importer = LotofacilDataImporter(db)
    
    try:
        imported = await importer.sync_latest()
        return {
            "success": True,
            "imported": imported,
            "message": f"{imported} concursos importados"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
