"""
Pool Cache Manager
Gerencia persistência do pool ótimo encontrado pelo GA
Evita recalcular o que já foi otimizado
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from backend.config import get_settings

settings = get_settings()


class PoolCacheManager:
    """
    Gerencia cache do pool ótimo
    
    Salva em JSON para fácil leitura e reutilização
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Args:
            cache_dir: Diretório para salvar cache (usa data/pools se None)
        """
        if cache_dir is None:
            cache_dir = os.path.join(settings.base_dir, "data", "pools")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.current_pool_file = self.cache_dir / "pool_otimo.json"
        self.history_dir = self.cache_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
    
    def save_pool(self, pool: List[int], fitness: float, roi: float, 
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Salva pool ótimo
        
        Args:
            pool: Lista de números do pool
            fitness: Score de fitness
            roi: ROI médio
            metadata: Dados adicionais (timestamps, gerações, etc)
        
        Returns:
            Caminho do arquivo salvo
        """
        now = datetime.now()
        
        # Metadados padrão
        if metadata is None:
            metadata = {}
        
        pool_data = {
            "timestamp": now.isoformat(),
            "pool": sorted(pool),
            "pool_size": len(pool),
            "fitness": float(fitness),
            "roi": float(roi),
            **metadata
        }
        
        # Salva em arquivo atual
        with open(self.current_pool_file, "w", encoding="utf-8") as f:
            json.dump(pool_data, f, indent=2)
        
        # Também salva em histórico
        history_filename = self.history_dir / f"pool_{now.strftime('%Y%m%d_%H%M%S')}.json"
        with open(history_filename, "w", encoding="utf-8") as f:
            json.dump(pool_data, f, indent=2)
        
        print(f"✓ Pool salvo: {self.current_pool_file}")
        print(f"  Pool: {sorted(pool)}")
        print(f"  Fitness: {fitness:.4f}, ROI: {roi:.4f}")
        
        return str(self.current_pool_file)
    
    def load_pool(self) -> Optional[Dict[str, Any]]:
        """
        Carrega pool ótimo em cache
        
        Returns:
            Dicionário com pool e metadata, ou None se não existir
        """
        if not self.current_pool_file.exists():
            return None
        
        try:
            with open(self.current_pool_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            print(f"✓ Pool carregado do cache")
            print(f"  Pool: {data['pool']}")
            print(f"  Fitness: {data['fitness']:.4f}, ROI: {data['roi']:.4f}")
            
            return data
        except Exception as e:
            print(f"✗ Erro ao carregar pool: {e}")
            return None
    
    def has_cached_pool(self) -> bool:
        """Verifica se existe pool em cache"""
        return self.current_pool_file.exists()
    
    def clear_cache(self) -> None:
        """Remove cache atual"""
        if self.current_pool_file.exists():
            self.current_pool_file.unlink()
            print(f"✓ Cache removido")
    
    def get_pool_list(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Lista histórico de pools salvos
        
        Args:
            limit: Quantos arquivos mais recentes retornar
        
        Returns:
            Lista de pools ordenada por timestamp (mais recentes primeiro)
        """
        pool_files = sorted(self.history_dir.glob("pool_*.json"), reverse=True)[:limit]
        pools = []
        
        for file in pool_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pools.append(data)
            except Exception as e:
                print(f"Erro ao ler {file}: {e}")
        
        return pools
