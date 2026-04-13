# Guia de Instalação - Lotofácil Optimizer

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Git

## Instalação Rápida

### 1. Clone o repositório

```bash
git clone <repository-url>
cd lotofacil-optimizer
```

### 2. Configure o ambiente

```bash
make setup
```

Este comando irá:
- Criar arquivo `.env` a partir do exemplo
- Iniciar PostgreSQL e Redis via Docker
- Aguardar inicialização dos serviços

### 3. Instale as dependências Python

```bash
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Inicie a API

```bash
python -m backend.main
```

A API estará disponível em: http://localhost:8000

Documentação interativa: http://localhost:8000/docs

## Importação de Dados Históricos

### Via API (Recomendado)

```bash
curl -X POST http://localhost:8000/contests/import/sync
```

### Via Script Python

```python
from backend.database.connection import get_db
from backend.utils.data_importer import LotofacilDataImporter

with get_db() as db:
    importer = LotofacilDataImporter(db)
    await importer.import_range(1, 3000)  # Importa concursos 1 a 3000
```

## Verificação da Instalação

### 1. Teste a API

```bash
curl http://localhost:8000/health
```

Resposta esperada: `{"status":"healthy"}`

### 2. Execute os testes

```bash
make test
```

### 3. Verifique os dados

```bash
curl http://localhost:8000/contests/stats/summary
```

## Comandos Úteis

```bash
# Iniciar infraestrutura
make start

# Parar infraestrutura
make stop

# Executar testes
make test

# Limpar arquivos temporários
make clean
```

## Troubleshooting

### Erro de conexão com PostgreSQL

Verifique se o container está rodando:
```bash
docker ps | grep lotofacil_postgres
```

Teste a conexão:
```bash
docker exec -it lotofacil_postgres psql -U lotofacil_user -d lotofacil
```

### Erro de conexão com Redis

Verifique se o container está rodando:
```bash
docker ps | grep lotofacil_redis
```

Teste a conexão:
```bash
docker exec -it lotofacil_redis redis-cli ping
```

### Porta já em uso

Altere as portas no `docker-compose.yml` se necessário.

## Próximos Passos

Após a instalação bem-sucedida:

1. Importe dados históricos da Lotofácil
2. Execute testes de validação
3. Explore a documentação da API em `/docs`
4. Configure parâmetros no arquivo `.env`

## Suporte

Para problemas ou dúvidas, consulte a documentação completa ou abra uma issue no repositório.
