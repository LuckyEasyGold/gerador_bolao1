import csv
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from backend.models.contest import Contest
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.lottery_fetcher import LotteryFetcherService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LotofacilDataImporter:
    """Importador de dados históricos da Lotofácil"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ContestRepository(db)
        self.fetcher = LotteryFetcherService()
    
    async def fetch_contest_from_api(self, contest_id: int) -> Optional[Contest]:
        """Busca um concurso específico da API da Caixa"""
        try:
            result = await self.fetcher.fetch_specific_contest("LOTOFACIL", contest_id)
            
            if not result:
                return None
            
            numbers = result.get("numbers", [])
            if len(numbers) != 15:
                logger.warning(f"Concurso {contest_id} não possui 15 números")
                return None
            
            draw_date = result.get("draw_date")
            if draw_date:
                draw_date = draw_date.date()
            else:
                return None
            
            return Contest(
                contest_id=contest_id,
                draw_date=draw_date,
                numbers=numbers
            )
        except Exception as e:
            logger.error(f"Erro ao buscar concurso {contest_id}: {e}")
            return None
    
    async def fetch_latest_contest(self) -> Optional[Contest]:
        """Busca o concurso mais recente da API"""
        result = await self.fetcher.fetch_latest_result("LOTOFACIL")
        
        if not result:
            return None
        
        contest_id = result.get("contest_number")
        if not contest_id:
            return None
        
        return await self.fetch_contest_from_api(contest_id)
    
    async def import_range(self, start_id: int, end_id: int) -> int:
        """Importa range de concursos da API"""
        contests = []
        
        for contest_id in range(start_id, end_id + 1):
            contest = await self.fetch_contest_from_api(contest_id)
            if contest:
                contests.append(contest)
                print(f"Importado concurso {contest_id}")
            
            # Batch insert a cada 100 concursos
            if len(contests) >= 100:
                self.repository.bulk_create(contests)
                contests = []
        
        # Insere restantes
        if contests:
            self.repository.bulk_create(contests)
        
        return end_id - start_id + 1
    
    def import_from_csv(self, csv_path: Path) -> int:
        """Importa concursos de arquivo CSV"""
        contests = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    contest_id = int(row['concurso'])
                    draw_date = datetime.strptime(row['data'], "%d/%m/%Y").date()
                    
                    # Extrai números (assumindo colunas bola1, bola2, ..., bola15)
                    numbers = []
                    for i in range(1, 16):
                        numbers.append(int(row[f'bola{i}']))
                    
                    contest = Contest(
                        contest_id=contest_id,
                        draw_date=draw_date,
                        numbers=numbers
                    )
                    contests.append(contest)
                    
                except Exception as e:
                    print(f"Erro ao processar linha: {e}")
                    continue
        
        if contests:
            return self.repository.bulk_create(contests)
        
        return 0
    
    async def sync_latest(self) -> int:
        """Sincroniza com os concursos mais recentes"""
        latest_local = self.repository.get_latest()
        latest_remote = await self.fetch_latest_contest()
        
        if not latest_remote:
            return 0
        
        remote_contest_id = latest_remote.contest_id
        
        if not latest_local:
            return await self.import_range(1, remote_contest_id)
        
        if remote_contest_id > latest_local.contest_id:
            return await self.import_range(
                latest_local.contest_id + 1,
                remote_contest_id
            )
        
        return 0
