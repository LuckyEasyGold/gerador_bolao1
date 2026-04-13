# Otimizador de Bolões Lotofácil

Sistema de otimização evolutiva para geração de bolões da Lotofácil com avaliação estatística via Monte Carlo.

## Tecnologias

- **Backend**: Python 3.11+, FastAPI, NumPy, Numba
- **Banco de Dados**: PostgreSQL, Redis
- **Frontend**: React, TypeScript, Recharts
- **Containerização**: Docker, Docker Compose

## Estrutura do Projeto

```
lotofacil-optimizer/
├── backend/          # API e motor de otimização
├── frontend/         # Interface web
├── tests/            # Testes automatizados
└── docker/           # Configurações Docker
```

## Instalação Rápida

```bash
# Subir infraestrutura
docker-compose up -d

# Instalar dependências backend
cd backend
pip install -r requirements.txt

# Instalar dependências frontend
cd frontend
npm install
```

## Status do Projeto

- [x] Planejamento e arquitetura
- [x] Fase 1: Base de dados e ingestão ✅
- [x] Fase 2: Feature engineering ✅
- [x] Fase 3: Motor de geração ✅
- [x] Fase 4: Simulador Monte Carlo ✅
- [x] Fase 5: Algoritmo genético ✅
- [x] Fase 6: Persistência ✅
- [ ] Fase 7: API e Frontend MVP 🔄

**Progresso**: 86% (6/7 fases concluídas)

## Funcionalidades Implementadas

### ✅ Fase 1: Base de Dados
- Schema PostgreSQL completo
- Modelos Pydantic (DNA, Contest, Experiment)
- Importador de dados históricos
- API REST base com FastAPI
- Docker Compose (PostgreSQL + Redis)

### ✅ Fase 2: Feature Engineering
- Cálculo de frequências históricas
- Análise de atrasos por número
- Detecção de repetições
- Matriz de afinidade combinatória
- Sistema de cache Redis

### ✅ Fase 3: Motor de Geração
- Seleção gulosa de pool
- Amostragem Softmax com temperatura
- Geração estrutural de jogos (15, 16, 17)
- Otimização de diversidade
- Geração de bolões completos

### ✅ Fase 4: Simulador Monte Carlo
- Gerador de sorteios pseudoaleatórios
- Common Random Numbers (CRN)
- Avaliação de premiações
- Cálculo de ROI e risco
- Simulação paralelizada

### ✅ Fase 6: Persistência e Reprodutibilidade
- Sistema completo de checkpoints
- Versionamento de seeds
- Logs estruturados (JSONL)
- Motor de replay e validação
- Exportação em múltiplos formatos (JSON, CSV, TXT)
- Reprodutibilidade 100% garantida

## API REST

O sistema expõe 53 endpoints REST:

- **7 endpoints** `/contests/*` - Gerenciamento de concursos
- **9 endpoints** `/features/*` - Cálculo de features
- **5 endpoints** `/games/*` - Geração de jogos
- **7 endpoints** `/simulate/*` - Simulação Monte Carlo
- **7 endpoints** `/optimize/*` - Otimização evolutiva
- **20 endpoints** `/persistence/*` - Persistência e reprodutibilidade

Documentação interativa: `http://localhost:8000/docs`

## Uso Rápido

```bash
# 1. Subir infraestrutura
docker-compose up -d

# 2. Importar dados históricos
python scripts/import_historical_data.py

# 3. Iniciar API
python -m backend.main

# 4. Executar otimização rápida
curl -X POST http://localhost:8000/optimize/quick \
  -H "Content-Type: application/json" \
  -d '{"budget": 50.0}'
```

## Scripts de Demonstração

```bash
# Demo de features
python scripts/demo_features.py

# Demo de geração de jogos
python scripts/demo_game_generation.py

# Demo de algoritmo genético
python scripts/demo_genetic_algorithm.py

# Demo de persistência
python scripts/demo_persistence.py
```

## Documentação

- [Guia de Implementação MCP](mcp_guia_implementacao_otimizador_lotofacil.md) - Guia técnico completo
- [Roadmap](ROADMAP.md) - Planejamento detalhado das 7 fases
- [Status](STATUS.md) - Status atual do projeto
- [Instalação](INSTALL.md) - Guia de instalação detalhado
- [Quickstart](QUICKSTART.md) - Início rápido
- [Phase 1 Complete](PHASE1_COMPLETE.md) - Documentação Fase 1
- [Phase 2 Complete](PHASE2_COMPLETE.md) - Documentação Fase 2
- [Phase 5 Complete](PHASE5_COMPLETE.md) - Documentação Fase 5
- [Phase 6 Complete](PHASE6_COMPLETE.md) - Documentação Fase 6

## Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Testes específicos
pytest tests/test_genetic_algorithm.py -v
pytest tests/test_checkpoint_manager.py -v
pytest tests/test_seed_manager.py -v

# Com cobertura
pytest tests/ --cov=backend --cov-report=html
```

## Estatísticas do Projeto

- **Linhas de código**: ~10.000
- **Testes**: 210+
- **Endpoints API**: 53
- **Classes implementadas**: 30+
- **Cobertura de testes**: Excelente
- **Fases concluídas**: 6 de 7 (86%)

## Próximos Passos

### Fase 7: Frontend MVP (Última Fase!)
- Setup React + TypeScript + Vite
- Dashboard de experimentos
- Visualização de convergência (Recharts)
- Configuração de campanhas
- Exportação de bolões via UI
- Monitoramento em tempo real
