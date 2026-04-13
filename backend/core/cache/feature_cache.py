"""
Sistema de cache de features usando Redis
"""
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import timedelta
from backend.database.connection import get_redis
from backend.config import get_settings

settings = get_settings()


class FeatureCache:
    """Cache Redis para features calculadas"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis()
        self.prefix = "lotofacil:features:"
        self.default_ttl = settings.cache_ttl
    
    def _make_key(self, feature_type: str, contest_id: Optional[int] = None, 
                  version: int = 1) -> str:
        """Gera chave única para o cache"""
        if contest_id is not None:
            return f"{self.prefix}{feature_type}:contest_{contest_id}:v{version}"
        return f"{self.prefix}{feature_type}:latest:v{version}"
    
    def _make_hash_key(self, data: Dict[str, Any]) -> str:
        """Gera hash MD5 dos dados para versionamento"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def set(self, feature_type: str, data: Dict[str, Any], 
            contest_id: Optional[int] = None, ttl: Optional[int] = None) -> bool:
        """
        Armazena features no cache
        
        Args:
            feature_type: Tipo da feature (frequency, delay, affinity, etc)
            data: Dados a cachear
            contest_id: ID do concurso (None para latest)
            ttl: Time to live em segundos (None usa default)
        """
        try:
            key = self._make_key(feature_type, contest_id)
            value = json.dumps(data)
            
            if ttl is None:
                ttl = self.default_ttl
            
            self.redis.setex(key, ttl, value)
            
            # Armazena hash para validação
            hash_key = f"{key}:hash"
            data_hash = self._make_hash_key(data)
            self.redis.setex(hash_key, ttl, data_hash)
            
            return True
        except Exception as e:
            print(f"Erro ao cachear {feature_type}: {e}")
            return False
    
    def get(self, feature_type: str, contest_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Recupera features do cache
        
        Args:
            feature_type: Tipo da feature
            contest_id: ID do concurso (None para latest)
        
        Returns:
            Dados cacheados ou None se não encontrado
        """
        try:
            key = self._make_key(feature_type, contest_id)
            value = self.redis.get(key)
            
            if value is None:
                return None
            
            return json.loads(value)
        except Exception as e:
            print(f"Erro ao recuperar cache {feature_type}: {e}")
            return None
    
    def exists(self, feature_type: str, contest_id: Optional[int] = None) -> bool:
        """Verifica se feature está cacheada"""
        key = self._make_key(feature_type, contest_id)
        return self.redis.exists(key) > 0
    
    def delete(self, feature_type: str, contest_id: Optional[int] = None) -> bool:
        """Remove feature do cache"""
        try:
            key = self._make_key(feature_type, contest_id)
            hash_key = f"{key}:hash"
            
            self.redis.delete(key)
            self.redis.delete(hash_key)
            return True
        except Exception as e:
            print(f"Erro ao deletar cache {feature_type}: {e}")
            return False
    
    def invalidate_all(self, feature_type: Optional[str] = None) -> int:
        """
        Invalida todo o cache de um tipo ou todos os tipos
        
        Args:
            feature_type: Tipo específico ou None para todos
        
        Returns:
            Número de chaves deletadas
        """
        try:
            if feature_type:
                pattern = f"{self.prefix}{feature_type}:*"
            else:
                pattern = f"{self.prefix}*"
            
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Erro ao invalidar cache: {e}")
            return 0
    
    def get_ttl(self, feature_type: str, contest_id: Optional[int] = None) -> int:
        """Retorna TTL restante em segundos (-1 se não existe)"""
        key = self._make_key(feature_type, contest_id)
        return self.redis.ttl(key)
    
    def set_frequency(self, data: Dict[str, Any], contest_id: Optional[int] = None) -> bool:
        """Atalho para cachear frequências"""
        return self.set("frequency", data, contest_id)
    
    def get_frequency(self, contest_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Atalho para recuperar frequências"""
        return self.get("frequency", contest_id)
    
    def set_delay(self, data: Dict[str, Any], contest_id: Optional[int] = None) -> bool:
        """Atalho para cachear atrasos"""
        return self.set("delay", data, contest_id)
    
    def get_delay(self, contest_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Atalho para recuperar atrasos"""
        return self.get("delay", contest_id)
    
    def set_affinity(self, data: Dict[str, Any], contest_id: Optional[int] = None) -> bool:
        """Atalho para cachear matriz de afinidade"""
        return self.set("affinity", data, contest_id)
    
    def get_affinity(self, contest_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Atalho para recuperar matriz de afinidade"""
        return self.get("affinity", contest_id)
    
    def set_all_features(self, features: Dict[str, Any], 
                        contest_id: Optional[int] = None) -> bool:
        """Cacheia todas as features de uma vez"""
        success = True
        
        if "frequency" in features:
            success &= self.set_frequency(features["frequency"], contest_id)
        
        if "delay" in features:
            success &= self.set_delay(features["delay"], contest_id)
        
        if "affinity" in features:
            success &= self.set_affinity(features["affinity"], contest_id)
        
        if "repetition" in features:
            success &= self.set("repetition", features["repetition"], contest_id)
        
        return success
    
    def get_all_features(self, contest_id: Optional[int] = None) -> Dict[str, Any]:
        """Recupera todas as features cacheadas"""
        return {
            "frequency": self.get_frequency(contest_id),
            "delay": self.get_delay(contest_id),
            "affinity": self.get_affinity(contest_id),
            "repetition": self.get("repetition", contest_id)
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        feature_types = ["frequency", "delay", "affinity", "repetition"]
        
        stats = {
            "total_keys": 0,
            "by_type": {}
        }
        
        for ftype in feature_types:
            pattern = f"{self.prefix}{ftype}:*"
            keys = self.redis.keys(pattern)
            count = len(keys) if keys else 0
            stats["by_type"][ftype] = count
            stats["total_keys"] += count
        
        return stats
