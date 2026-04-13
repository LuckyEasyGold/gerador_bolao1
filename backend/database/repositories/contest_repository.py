from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models.contest import Contest


class ContestRepository:
    """Repositório para operações com concursos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, contest: Contest) -> Contest:
        """Insere novo concurso"""
        query = text("""
            INSERT INTO contests (contest_id, draw_date, numbers)
            VALUES (:contest_id, :draw_date, :numbers)
            ON CONFLICT (contest_id) DO NOTHING
            RETURNING contest_id, draw_date, numbers
        """)
        
        result = self.db.execute(
            query,
            {
                "contest_id": contest.contest_id,
                "draw_date": contest.draw_date,
                "numbers": contest.numbers
            }
        )
        self.db.commit()
        return contest
    
    def bulk_create(self, contests: List[Contest]) -> int:
        """Insere múltiplos concursos"""
        if not contests:
            return 0
        
        query = text("""
            INSERT INTO contests (contest_id, draw_date, numbers)
            VALUES (:contest_id, :draw_date, :numbers)
            ON CONFLICT (contest_id) DO NOTHING
        """)
        
        data = [
            {
                "contest_id": c.contest_id,
                "draw_date": c.draw_date,
                "numbers": c.numbers
            }
            for c in contests
        ]
        
        self.db.execute(query, data)
        self.db.commit()
        return len(contests)
    
    def get_by_id(self, contest_id: int) -> Optional[Contest]:
        """Busca concurso por ID"""
        query = text("""
            SELECT contest_id, draw_date, numbers
            FROM contests
            WHERE contest_id = :contest_id
        """)
        
        result = self.db.execute(query, {"contest_id": contest_id}).fetchone()
        
        if result:
            return Contest(
                contest_id=result[0],
                draw_date=result[1],
                numbers=result[2]
            )
        return None
    
    def get_all(self, limit: Optional[int] = None) -> List[Contest]:
        """Retorna todos os concursos ordenados por data"""
        query = text("""
            SELECT contest_id, draw_date, numbers
            FROM contests
            ORDER BY draw_date DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(
            query,
            {"limit": limit if limit else 999999}
        ).fetchall()
        
        return [
            Contest(contest_id=r[0], draw_date=r[1], numbers=r[2])
            for r in results
        ]
    
    def get_latest(self) -> Optional[Contest]:
        """Retorna o concurso mais recente"""
        query = text("""
            SELECT contest_id, draw_date, numbers
            FROM contests
            ORDER BY draw_date DESC
            LIMIT 1
        """)
        
        result = self.db.execute(query).fetchone()
        
        if result:
            return Contest(
                contest_id=result[0],
                draw_date=result[1],
                numbers=result[2]
            )
        return None
    
    def count(self) -> int:
        """Conta total de concursos"""
        query = text("SELECT COUNT(*) FROM contests")
        result = self.db.execute(query).fetchone()
        return result[0] if result else 0
    
    def get_date_range(self) -> tuple[Optional[date], Optional[date]]:
        """Retorna range de datas dos concursos"""
        query = text("""
            SELECT MIN(draw_date), MAX(draw_date)
            FROM contests
        """)
        
        result = self.db.execute(query).fetchone()
        return (result[0], result[1]) if result else (None, None)
