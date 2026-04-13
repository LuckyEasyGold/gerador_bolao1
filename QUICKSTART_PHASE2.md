# Quickstart - Fase 2: Feature Engineering

Guia rápido para testar as features implementadas na Fase 2.

## 🚀 Testar Features via API

### 1. Calcular Todas as Features
```bash
curl -X POST http://localhost:8000/features/calculate
```

### 2. Obter Frequências
```bash
curl http://localhost:8000/features/frequency
```

### 3. Obter Atrasos
```bash
curl http://localhost:8000/features/delay
```

### 4. Obter Matriz de Afinidade
```bash
curl http://localhost:8000/features/affinity
```

### 5. Obter Repetições do Último Concurso
```bash
curl http://localhost:8000/features/repetition
```

### 6. Calcular Scores com Pesos Personalizados
```bash
# Balanceado
curl "http://localhost:8000/features/scores?wf=0.33&wa=0.33&wr=0.34"

# Foco em frequência
curl "http://localhost:8000/features/scores?wf=0.7&wa=0.2&wr=0.1"

# Foco em atraso
curl "http://localhost:8000/features/scores?wf=0.1&wa=0.8&wr=0.1"
```

### 7. Features de um Número Específico
```bash
curl http://localhost:8000/features/number/10
```

### 8. Estatísticas do Cache
```bash
curl http://localhost:8000/features/cache/stats
```

### 9. Limpar Cache
```bash
curl -X DELETE http://localhost:8000/features/cache
```

## 🐍 Testar Features via Python

```python
from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer

# Buscar concursos
with get_db() as db:
    repo = ContestRepository(db)
    contests = repo.get_all(limit=100)

# Calcular features
engineer = FeatureEngineer()
engineer.fit(contests)

# 1. Frequências
freq_10 = engineer.frequency_calc.get_frequency(10)
print(f"Frequência do 10: {freq_10:.2%}")

top_10 = engineer.frequency_calc.get_top_k(10)
print("Top 10 mais frequentes:", top_10)

# 2. Atrasos
delay_10 = engineer.delay_calc.get_delay(10)
print(f"Atraso do 10: {delay_10} concursos")

most_delayed = engineer.delay_calc.get_most_delayed(10)
print("Top 10 mais atrasados:", most_delayed)

# 3. Repetições
is_repeated = engineer.repetition_detector.is_repeated(10)
print(f"Número 10 repetido: {is_repeated}")

repeated_nums = engineer.repetition_detector.get_repeated_numbers()
print(f"Números do último concurso: {repeated_nums}")

# 4. Afinidade
aff_1_2 = engineer.affinity_matrix.get_affinity(1, 2)
print(f"Afinidade 1-2: {aff_1_2:.2%}")

companions = engineer.affinity_matrix.get_best_companions(10, k=5)
print(f"Melhores companheiros do 10: {companions}")

# 5. Scores ponderados
weights = {'wf': 0.5, 'wa': 0.3, 'wr': 0.2}
scores = engineer.compute_all_scores(weights)
print(f"Scores calculados: {len(scores)} números")

# Top 5
import numpy as np
top_5_idx = np.argsort(scores)[-5:][::-1]
top_5 = [(i+1, scores[i]) for i in top_5_idx]
print(f"Top 5 números: {top_5}")
```

## 🎬 Script de Demonstração

```bash
python scripts/demo_features.py
```

Este script mostra:
- ✅ Frequências históricas
- ✅ Atrasos (delays)
- ✅ Repetições do último concurso
- ✅ Matriz de afinidade
- ✅ Scores com diferentes pesos
- ✅ Sistema de cache

## 🧪 Executar Testes

```bash
# Todos os testes da Fase 2
pytest tests/test_features.py tests/test_cache.py -v

# Apenas testes de features
pytest tests/test_features.py -v

# Apenas testes de cache
pytest tests/test_cache.py -v

# Com coverage
pytest tests/test_features.py tests/test_cache.py --cov=backend.core
```

## 💾 Testar Cache Redis

```python
from backend.core.cache.feature_cache import FeatureCache

cache = FeatureCache()

# Cachear dados
data = {"test": "value", "numbers": [1, 2, 3]}
cache.set("frequency", data)

# Recuperar
cached = cache.get("frequency")
print(cached)

# Verificar existência
exists = cache.exists("frequency")
print(f"Existe: {exists}")

# TTL
ttl = cache.get_ttl("frequency")
print(f"TTL: {ttl} segundos")

# Estatísticas
stats = cache.get_cache_stats()
print(stats)

# Limpar
cache.invalidate_all("frequency")
```

## 📊 Exemplos de Saída

### Frequências
```json
{
  "success": true,
  "source": "calculated",
  "data": {
    "frequencies": {
      "1": 0.65,
      "2": 0.62,
      "3": 0.58
    },
    "total_contests": 100,
    "normalized": [0.026, 0.025, 0.023, ...]
  }
}
```

### Scores
```json
{
  "success": true,
  "weights": {"wf": 0.5, "wa": 0.3, "wr": 0.2},
  "scores": [
    {"number": 10, "score": 0.8523},
    {"number": 15, "score": 0.7891},
    {"number": 3, "score": 0.7654}
  ]
}
```

### Features de um Número
```json
{
  "number": 10,
  "frequency": 0.65,
  "delay": 2,
  "is_repeated": true,
  "best_companions": [
    {"number": 11, "affinity": 0.85},
    {"number": 9, "affinity": 0.82},
    {"number": 12, "affinity": 0.78}
  ]
}
```

## 🔍 Explorar API Interativa

Abra no navegador: http://localhost:8000/docs

Você verá:
- 📁 **contests** - 7 endpoints (Fase 1)
- 📁 **features** - 9 endpoints (Fase 2)

Teste diretamente na interface Swagger!

## 💡 Dicas

1. **Use cache**: Adicione `?use_cache=true` para usar cache Redis
2. **Force recálculo**: Use `?force_recalculate=true` para ignorar cache
3. **Teste pesos**: Experimente diferentes combinações em `/features/scores`
4. **Monitore cache**: Use `/features/cache/stats` para ver uso
5. **Limpe cache**: Use `DELETE /features/cache` quando atualizar dados

## 🎯 Casos de Uso

### 1. Encontrar Números "Quentes"
```bash
# Números mais frequentes + menos atrasados
curl "http://localhost:8000/features/scores?wf=0.6&wa=0.4&wr=0.0"
```

### 2. Encontrar Números "Frios"
```bash
# Números mais atrasados
curl "http://localhost:8000/features/scores?wf=0.0&wa=1.0&wr=0.0"
```

### 3. Evitar Repetições
```bash
# Baixo peso para repetições
curl "http://localhost:8000/features/scores?wf=0.5&wa=0.5&wr=-0.5"
```

### 4. Análise de Afinidade
```python
# Encontrar grupos de números que aparecem juntos
engineer.fit(contests)
for num in range(1, 26):
    companions = engineer.affinity_matrix.get_best_companions(num, k=3)
    print(f"{num}: {companions}")
```

## 🚀 Próximos Passos

Após validar as features:
1. ✅ Testar todos os endpoints
2. ✅ Executar testes unitários
3. ✅ Validar cache Redis
4. 🔄 Iniciar Fase 3: Motor de Geração

## 🆘 Troubleshooting

### Erro "Nenhum concurso encontrado"
```bash
# Importar dados primeiro
python scripts/import_historical_data.py
```

### Erro de conexão Redis
```bash
# Verificar se Redis está rodando
docker ps | grep redis

# Reiniciar se necessário
docker-compose restart redis
```

### Cache não funciona
```bash
# Verificar conexão Redis
docker exec -it lotofacil_redis redis-cli ping

# Limpar cache
curl -X DELETE http://localhost:8000/features/cache
```

---

**Fase 2 Completa**: ✅  
**Próxima Fase**: Motor de Geração 🔄
