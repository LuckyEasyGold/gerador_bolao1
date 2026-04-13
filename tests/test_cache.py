import pytest
from unittest.mock import Mock, MagicMock
from backend.core.cache.feature_cache import FeatureCache


@pytest.fixture
def mock_redis():
    """Mock do cliente Redis"""
    redis_mock = Mock()
    redis_mock.setex = Mock(return_value=True)
    redis_mock.get = Mock(return_value=None)
    redis_mock.exists = Mock(return_value=0)
    redis_mock.delete = Mock(return_value=1)
    redis_mock.keys = Mock(return_value=[])
    redis_mock.ttl = Mock(return_value=-1)
    return redis_mock


@pytest.fixture
def cache(mock_redis):
    """Instância do cache com Redis mockado"""
    return FeatureCache(redis_client=mock_redis)


def test_cache_initialization(cache):
    """Testa inicialização do cache"""
    assert cache.prefix == "lotofacil:features:"
    assert cache.default_ttl > 0


def test_make_key(cache):
    """Testa geração de chaves"""
    key1 = cache._make_key("frequency")
    assert "frequency" in key1
    assert "latest" in key1
    
    key2 = cache._make_key("frequency", contest_id=100)
    assert "frequency" in key2
    assert "contest_100" in key2


def test_set_feature(cache, mock_redis):
    """Testa armazenamento de feature"""
    data = {"test": "value"}
    
    result = cache.set("frequency", data)
    
    assert result is True
    assert mock_redis.setex.called


def test_get_feature(cache, mock_redis):
    """Testa recuperação de feature"""
    import json
    test_data = {"test": "value"}
    mock_redis.get.return_value = json.dumps(test_data)
    
    result = cache.get("frequency")
    
    assert result == test_data
    assert mock_redis.get.called


def test_get_feature_not_found(cache, mock_redis):
    """Testa recuperação quando não existe"""
    mock_redis.get.return_value = None
    
    result = cache.get("frequency")
    
    assert result is None


def test_exists(cache, mock_redis):
    """Testa verificação de existência"""
    mock_redis.exists.return_value = 1
    
    assert cache.exists("frequency") is True
    
    mock_redis.exists.return_value = 0
    assert cache.exists("frequency") is False


def test_delete_feature(cache, mock_redis):
    """Testa remoção de feature"""
    result = cache.delete("frequency")
    
    assert result is True
    assert mock_redis.delete.called


def test_invalidate_all_specific_type(cache, mock_redis):
    """Testa invalidação de tipo específico"""
    mock_redis.keys.return_value = ["key1", "key2"]
    mock_redis.delete.return_value = 2
    
    count = cache.invalidate_all("frequency")
    
    assert count == 2
    assert mock_redis.keys.called


def test_invalidate_all_types(cache, mock_redis):
    """Testa invalidação de todos os tipos"""
    mock_redis.keys.return_value = ["key1", "key2", "key3"]
    mock_redis.delete.return_value = 3
    
    count = cache.invalidate_all()
    
    assert count == 3


def test_get_ttl(cache, mock_redis):
    """Testa recuperação de TTL"""
    mock_redis.ttl.return_value = 3600
    
    ttl = cache.get_ttl("frequency")
    
    assert ttl == 3600


def test_set_frequency_shortcut(cache, mock_redis):
    """Testa atalho para frequências"""
    data = {"frequencies": [0.5, 0.3]}
    
    result = cache.set_frequency(data)
    
    assert result is True


def test_get_frequency_shortcut(cache, mock_redis):
    """Testa atalho para recuperar frequências"""
    import json
    test_data = {"frequencies": [0.5, 0.3]}
    mock_redis.get.return_value = json.dumps(test_data)
    
    result = cache.get_frequency()
    
    assert result == test_data


def test_set_all_features(cache, mock_redis):
    """Testa cache de todas as features"""
    features = {
        "frequency": {"data": "freq"},
        "delay": {"data": "delay"},
        "affinity": {"data": "aff"},
        "repetition": {"data": "rep"}
    }
    
    result = cache.set_all_features(features)
    
    assert result is True
    # Deve ter chamado setex 8 vezes (4 features + 4 hashes)
    assert mock_redis.setex.call_count >= 4


def test_get_all_features(cache, mock_redis):
    """Testa recuperação de todas as features"""
    import json
    mock_redis.get.return_value = json.dumps({"test": "data"})
    
    features = cache.get_all_features()
    
    assert "frequency" in features
    assert "delay" in features
    assert "affinity" in features
    assert "repetition" in features


def test_get_cache_stats(cache, mock_redis):
    """Testa estatísticas do cache"""
    mock_redis.keys.return_value = ["key1", "key2"]
    
    stats = cache.get_cache_stats()
    
    assert "total_keys" in stats
    assert "by_type" in stats
    assert "frequency" in stats["by_type"]


def test_cache_with_contest_id(cache, mock_redis):
    """Testa cache com ID de concurso específico"""
    data = {"test": "value"}
    
    cache.set("frequency", data, contest_id=100)
    
    # Verifica que a chave contém o contest_id
    call_args = mock_redis.setex.call_args
    key = call_args[0][0]
    assert "contest_100" in key


def test_cache_error_handling(cache, mock_redis):
    """Testa tratamento de erros"""
    mock_redis.setex.side_effect = Exception("Redis error")
    
    # Não deve lançar exceção, apenas retornar False
    result = cache.set("frequency", {"test": "data"})
    
    assert result is False
