# Quickstart - Lotofácil Optimizer

Guia rápido para colocar o sistema no ar em 5 minutos.

## 🚀 Setup em 1 Comando

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_app.ps1
```

✅ Frontend rodando em: http://localhost:5173  
✅ API rodando em: http://localhost:8000  
📚 Documentação: http://localhost:8000/docs

## 🖱️ Setup em 1 Clique

No Windows, dê duplo clique em [Iniciar Lotofacil Optimizer.bat](/C:/projetos/gerador_bolao/Iniciar%20Lotofacil%20Optimizer.bat).

## 🎲 Importar Dados Históricos

### Opção 1: Via Script Interativo
```bash
python scripts/import_historical_data.py
```

### Opção 2: Via API
```bash
curl -X POST http://localhost:8000/contests/import/sync
```

### Opção 3: Via Python
```python
import asyncio
from backend.database.connection import get_db
from backend.utils.data_importer import LotofacilDataImporter

async def import_data():
    with get_db() as db:
        importer = LotofacilDataImporter(db)
        await importer.import_range(1, 100)  # Primeiros 100 concursos

asyncio.run(import_data())
```

## 🧪 Testar a API

### Health Check
```bash
curl http://localhost:8000/health
# Resposta: {"status":"healthy"}
```

### Listar Concursos
```bash
curl http://localhost:8000/contests?limit=5
```

### Último Concurso
```bash
curl http://localhost:8000/contests/latest
```

### Estatísticas
```bash
curl http://localhost:8000/contests/stats/summary
```

## 🧬 Testar DNA Evolutivo

```python
from backend.models.dna import DNA, DNAGene
import numpy as np

# Criar DNA aleatório
rng = np.random.default_rng(42)
dna = DNA(genes=DNAGene.random(rng))

print(f"Pool size: {dna.genes.pool_size}")
print(f"Temperatura: {dna.genes.T_base}")

# Mutação
mutated = dna.mutate(mutation_rate=0.2, rng=rng)
print(f"Geração: {mutated.generation}")

# Crossover
dna2 = DNA(genes=DNAGene.random(rng))
child = DNA.crossover(dna, dna2, rng)
print(f"Child geração: {child.generation}")
```

## 🐳 Comandos Docker

```bash
# Ver logs PostgreSQL
docker logs lotofacil_postgres

# Ver logs Redis
docker logs lotofacil_redis

# Conectar ao PostgreSQL
docker exec -it lotofacil_postgres psql -U lotofacil_user -d lotofacil

# Conectar ao Redis
docker exec -it lotofacil_redis redis-cli

# Parar tudo
powershell -ExecutionPolicy Bypass -File .\scripts\stop_app.ps1

# Reiniciar
powershell -ExecutionPolicy Bypass -File .\scripts\start_app.ps1
```

## 🧪 Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=backend --cov-report=html

# Apenas testes rápidos
pytest tests/ -m "not slow"
```

## 📊 Queries SQL Úteis

```sql
-- Total de concursos
SELECT COUNT(*) FROM contests;

-- Últimos 10 concursos
SELECT contest_id, draw_date, numbers 
FROM contests 
ORDER BY draw_date DESC 
LIMIT 10;

-- Frequência de cada número
SELECT 
    num,
    COUNT(*) as frequency
FROM contests, unnest(numbers) as num
GROUP BY num
ORDER BY frequency DESC;

-- Números mais atrasados
WITH last_appearance AS (
    SELECT 
        num,
        MAX(contest_id) as last_contest
    FROM contests, unnest(numbers) as num
    GROUP BY num
)
SELECT 
    num,
    (SELECT MAX(contest_id) FROM contests) - last_contest as delay
FROM last_appearance
ORDER BY delay DESC;
```

## 🔧 Troubleshooting Rápido

### Porta 5432 já em uso
```bash
# Alterar porta no docker-compose.yml
ports:
  - "5433:5432"  # Usar 5433 no host
```

### Erro de conexão com banco
```bash
# Verificar se está rodando
docker ps | grep postgres

# Reiniciar
docker-compose restart postgres
```

### Limpar tudo e recomeçar
```bash
docker-compose down -v  # Remove volumes
make clean              # Limpa arquivos temporários
bash scripts/init_project.sh  # Reinicia
```

## 📱 Acessar Documentação Interativa

Abra no navegador: http://localhost:8000/docs

Você poderá:
- Ver todos os endpoints
- Testar requisições diretamente
- Ver schemas de dados
- Baixar especificação OpenAPI

## 🎯 Próximos Passos

Após validar que tudo está funcionando:

1. ✅ Importar dados históricos completos
2. ✅ Explorar a API via /docs
3. ✅ Executar testes
4. 🔄 Aguardar Fase 2: Feature Engineering

## 💡 Dicas

- Use `make` para comandos comuns (ver `Makefile`)
- Logs da API aparecem no terminal
- Redis é usado para cache (ainda não implementado)
- PostgreSQL persiste dados entre restarts

## 🆘 Precisa de Ajuda?

1. Verifique `INSTALL.md` para detalhes
2. Consulte `STATUS.md` para progresso
3. Leia `IMPLEMENTATION_SUMMARY.md` para arquitetura
4. Abra issue no repositório
