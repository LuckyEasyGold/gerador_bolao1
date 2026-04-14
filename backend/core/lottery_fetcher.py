import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


GAME_TYPE_MAPPING = {
    "LOTOFACIL": "lotofacil",
    "MEGASENA": "megasena",
    "QUINA": "quina",
    "LOTOMANIA": "lotomania",
}


class LotteryFetcherService:
    """Cliente para API da Caixa Econômica Federal"""
    
    def __init__(self):
        self.base_url = settings.caixa_api_base_url
        self.timeout = settings.caixa_api_timeout
    
    async def fetch_latest_result(self, game_type: str) -> Optional[Dict[str, Any]]:
        """
        Busca o último resultado de uma loteria
        
        Args:
            game_type: Tipo do jogo (LOTOFACIL, MEGASENA, QUINA, LOTOMANIA)
            
        Returns:
            Dicionário com dados do resultado ou None se falhar
        """
        endpoint = GAME_TYPE_MAPPING.get(game_type.upper())
        if not endpoint:
            logger.error(f"Tipo de jogo não suportado: {game_type}")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Buscando último resultado de {game_type} em {url}")
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_result(data, game_type)
                
        except httpx.TimeoutException:
            logger.error(f"Timeout ao buscar {game_type}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar {game_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao processar {game_type}: {e}")
            return None
    
    async def fetch_specific_contest(self, game_type: str, contest_number: int) -> Optional[Dict[str, Any]]:
        """
        Busca resultado de um concurso específico
        
        Args:
            game_type: Tipo do jogo
            contest_number: Número do concurso
            
        Returns:
            Dicionário com dados do resultado ou None se falhar
        """
        endpoint = GAME_TYPE_MAPPING.get(game_type.upper())
        if not endpoint:
            logger.error(f"Tipo de jogo não suportado: {game_type}")
            return None
        
        url = f"{self.base_url}/{endpoint}/{contest_number}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Buscando concurso {contest_number} de {game_type}")
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_result(data, game_type)
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Concurso {contest_number} de {game_type} não encontrado")
            else:
                logger.error(f"Erro HTTP ao buscar concurso {contest_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar concurso {contest_number}: {e}")
            return None
    
    async def fetch_range(self, game_type: str, start_contest: int, end_contest: int) -> List[Dict[str, Any]]:
        """
        Busca múltiplos concursos em um intervalo
        
        Args:
            game_type: Tipo do jogo
            start_contest: Número do primeiro concurso
            end_contest: Número do último concurso
            
        Returns:
            Lista de resultados encontrados
        """
        results = []
        
        for contest_num in range(start_contest, end_contest + 1):
            result = await self.fetch_specific_contest(game_type, contest_num)
            if result:
                results.append(result)
            else:
                logger.warning(f"Pulando concurso {contest_num} (não encontrado ou erro)")
        
        logger.info(f"Buscados {len(results)} de {end_contest - start_contest + 1} concursos")
        return results
    
    def _parse_result(self, data: Dict[str, Any], game_type: str) -> Dict[str, Any]:
        """
        Converte formato da API da Caixa para formato interno
        
        Args:
            data: JSON retornado pela API
            game_type: Tipo do jogo
            
        Returns:
            Dicionário padronizado
        """
        # Detectar o tipo de loteria para saber quantos números esperar
        numbers_per_draw = self._get_numbers_per_draw(game_type)
        
        # Converter strings de números para inteiros
        numbers = self._extract_numbers(data, numbers_per_draw)
        
        # Converter data do formato DD/MM/YYYY para datetime
        date_str = data.get("dataApuracao", "")
        draw_date = self._parse_date(date_str)
        
        return {
            "game_type": game_type.upper(),
            "contest_number": data.get("numeroConcurso") or data.get("numero"),
            "draw_date": draw_date,
            "numbers": numbers,
            "is_latest": data.get("ultimoConcurso", False)
        }
    
    def _get_numbers_per_draw(self, game_type: str) -> int:
        """Retorna a quantidade de números por sorteio para cada jogo"""
        mapping = {
            "LOTOFACIL": 15,
            "MEGASENA": 6,
            "QUINA": 5,
            "LOTOMANIA": 20,
        }
        return mapping.get(game_type.upper(), 15)
    
    def _extract_numbers(self, data: Dict[str, Any], count: int) -> List[int]:
        """Extrai os números do resultado"""
        numbers = []
        
        # Tentar formato com prefixo "dezena"
        for i in range(1, count + 1):
            key = f"dezena{i}"
            if key in data:
                numbers.append(int(data[key]))
        
        # Se não encontrou, tentar formato "listaDezenas"
        if not numbers and "listaDezenas" in data:
            numbers = [int(n) for n in data["listaDezenas"]]
        
        # Tentar formato alternativo "dezenas"
        if not numbers and "dezenas" in data:
            dezenas = data["dezenas"]
            if isinstance(dezenas, str):
                numbers = [int(n.strip()) for n in dezenas.split(",")]
            elif isinstance(dezenas, list):
                numbers = [int(n) for n in dezenas]
        
        return numbers
    
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string de data para datetime"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            logger.warning(f"Data inválida: {date_str}, usando data atual")
            return datetime.now()
    
    async def get_latest_contest_number(self, game_type: str) -> Optional[int]:
        """
        Retorna apenas o número do último concurso disponível
        
        Args:
            game_type: Tipo do jogo
            
        Returns:
            Número do último concurso ou None
        """
        result = await self.fetch_latest_result(game_type)
        return result.get("contest_number") if result else None
