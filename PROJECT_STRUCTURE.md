# Estrutura do Projeto - Lotofácil Gerador de Bolões v2

## 📁 Visão Geral - Nova Arquitetura

```
gerador_bolao/
├── 📄 Documentação Essencial
├── 🐳 Infraestrutura
├── 🔧 Backend (API v2)
├── 🎨 Frontend (React)
├── 🧪 Testes
└── 📊 Data
```

---

## 📂 Estrutura Completa

```
gerador_bolao/
│
├── 📄 README.md                          # Visão geral
├── 📄 INSTALL.md                         # Como instalar
├── 📄 ROADMAP.md                         # Futuro
├── 📄 STATUS.md                          # Status atual
├── 📄 SISTEMA_REFATORADO_v2.md          # 📌 Documentação Técnica
├── 📄 PROJECT_STRUCTURE.md               # Este arquivo
│
├── 🐳 docker-compose.yml                 # Docker Compose
├── 📄 Makefile                           # Comandos
├── 📄 pytest.ini                         # Testes
│
├── 🔧 backend/                           # Backend FastAPI
│   │
│   ├── main.py                           # ✅ App FastAPI (atualizado)
│   ├── config.py                         # Configurações
│   ├── requirements.txt                  # Dependências
│   │
│   ├── 📁 models/                        # Modelos Pydantic
│   │   ├── pool_dna.py                   # ✅ NOVO: DNA simplificado
│   │   ├── contest.py
│   │   └── dna.py                        # Legado
│   │
│   ├── 📁 core/                          # Lógica de Negócio
│   │   ├── pool_genetic_algorithm.py     # ✅ NOVO: GA rápido
│   │   ├── pool_cache_manager.py         # ✅ NOVO: Cache em JSON
│   │   ├── simple_ticket_generator.py    # ✅ NOVO: gerar_bolao()
│   │   ├── monte_carlo.py
│   │   ├── game_generator.py             # Legado
│   │   └── genetic_algorithm.py          # Legado
│   │
│   ├── 📁 database/                      # Persistência
│   │   ├── connection.py
│   │   ├── init.sql
│   │   └── repositories/
│   │       └── contest_repository.py
│   │
│   ├── 📁 api/routes/                    # Endpoints
│   │   ├── pool_v2.py                    # ✅ NOVO: API v2
│   │   ├── games.py
│   │   ├── optimize.py                   # Legado
│   │   └── [outros]
│   │
│   └── 📁 utils/
│       └── data_importer.py
│
├── 🎨 frontend/                          # React + TypeScript
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── 📁 components/
│       └── 📁 services/
│
├── 📊 data/                              # Dados e Cache
│   ├── 📁 pools/
│   │   ├── pool_otimo.json              # ⭐ Pool ótimo em cache
│   │   └── 📁 history/
│   ├── 📁 checkpoints/
│   ├── 📁 logs/
│   └── 📁 seeds/
│
├── 🧪 tests/                             # Testes
│   ├── test_dna.py
│   ├── test_features.py
│   └── [outros]
│
└── 📜 scripts/                           # Utilitários
    ├── init_project.sh
    ├── start_app.ps1
    └── stop_app.ps1
```

---

## 🆕 Componentes Principais v2.0

### 1. PoolDNA (`backend/models/pool_dna.py`)

**O que é:**  
Representação simplificada do cromossomo - apenas um pool de números (15-25).

**Métodos:**
- `PoolDNA.random()` - Gera DNA aleatório
- `mutate()` - Remove/adiciona números
- `crossover(parent1, parent2)` - Combina 2 pools

**Exemplo:**
```python
dna = PoolDNA(pool=[3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 24])
mutated = dna.mutate(mutation_rate=0.3)
child = PoolDNA.crossover(dna, mutated)
```

---

### 2. PoolGeneticAlgorithm (`backend/core/pool_genetic_algorithm.py`)

**O que faz:**  
Evolui pool ótimo em 20-30 gerações (~2 minutos).

**Principais Componentes:**
- Population - Gerencia população de DNAs
- PoolGenerationStats - Estatísticas por geração
- PoolEvolutionResult - Resultado final

**Uso:**
```python
ga = PoolGeneticAlgorithm(
    contests=contests,
    population_size=10,
    generations=20,
    simulations=500
)
result = ga.evolve()
```

---

### 3. PoolCacheManager (`backend/core/pool_cache_manager.py`)

**O que faz:**  
Persiste pool ótimo em JSON para reutilização.

**Estrutura:**
```
data/pools/
├── pool_otimo.json              # Pool atual
└── history/
    └── pool_20260415_103500.json # Histórico
```

**Métodos:**
- `save_pool(pool, fitness, roi)` - Salva
- `load_pool()` - Carrega
- `has_cached_pool()` - Verifica
- `clear_cache()` - Remove

---

### 4. simple_ticket_generator (`backend/core/simple_ticket_generator.py`)

**O que faz:**  
Calcula distribuição de j15, j16, j17 em <100ms.

**Função Principal:**
```python
def calcular_distribuicao_orcamento(
    valor_total: float,
    valor_unitario: float,
    pool: Optional[List[int]] = None
) -> SimpleBolao
```

**Retorna:**
```python
SimpleBolao(
    j15=2, j16=1, j17=1,
    custo_total=90.0,
    total_jogos=4,
    pool_usado=[3, 5, 7, ...]
)
```

---

### 5. API Routes v2 (`backend/api/routes/pool_v2.py`)

**Endpoints:**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/bolao/pool/encontrar` | Inicia busca GA |
| GET | `/bolao/pool/status/{task_id}` | Status da busca |
| GET | `/bolao/pool/otimo` | Pool do cache |
| POST | `/bolao/gerar` | Gera bolão |
| GET | `/bolao/pool/historico` | Histórico |
| DELETE | `/bolao/pool/cache` | Limpa cache |

---

## 📊 Fluxo de Dados

```
PRIMEIRA VEZ:
┌─────────────────────┐
│ POST /pool/encontrar│ ← Usuário inicia
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PoolGeneticAlgorithm│ ← GA executa
│  20 gerações ~2min  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PoolCacheManager    │ ← Salva pool
│ data/pools/         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Pool otimizado!     │ ← Retorna task_id
└─────────────────────┘

DEPOIS (INFINITAS VEZES):
┌─────────────────────┐
│ POST /bolao/gerar   │ ← Usuário chama
│ {valor, cotas, ...} │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PoolCacheManager    │ ← Carrega pool
│ (disk ou mem)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ simple_ticket_...   │ ← Calcula em <100ms
│ {j15, j16, j17}    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SimpleBolao retorno │ ← Resposta
└─────────────────────┘
```

---

## 📋 Dependências Principais

```python
# backend/requirements.txt
fastapi           # Web framework
sqlalchemy        # ORM
pydantic          # Validação
numpy             # Computação
redis             # Cache (opcional)
uvicorn           # Server
```

---

## 🏗️ Como Estruturar Novo Código

### Adicionar Novo Endpoint

1. Criar função em `backend/api/routes/pool_v2.py`
2. Usar decorador `@router.post("rota")`
3. Retornar `dict` JSON

### Adicionar Novo Core Module

1. Criar em `backend/core/novo_modulo.py`
2. Implementar classe(s) principal(ais)
3. Atualizar imports em `main.py`

### Modificar Models

1. Editar em `backend/models/novo_model.py`
2. Usar Pydantic BaseModel
3. Adicionar validators se necessário

---

## 📝 Notas

- **v2.0 = Simplificação:** Apenas 5 componentes novos focados
- **Legado mantido:** Codes antigos podem ser removidos depois
- **Cache: Arquivo JSON** (pode migrar para Redis depois)
- **DB: SQLAlchemy** (pode evoluir para async depois)
│
├── 📄 README.md                          # Visão geral do projeto
├── 📄 INSTALL.md                         # Guia de instalação
├── 📄 QUICKSTART.md                      # Setup rápido
├── 📄 ROADMAP.md                         # Planejamento de fases
├── 📄 STATUS.md                          # Status atual
├── 📄 IMPLEMENTATION_SUMMARY.md          # Resumo técnico
├── 📄 EXECUTIVE_SUMMARY.md               # Resumo executivo
├── 📄 PROJECT_STRUCTURE.md               # Este arquivo
│
├── 🐳 docker-compose.yml                 # Infraestrutura Docker
├── 📄 Makefile                           # Comandos úteis
├── 📄 .gitignore                         # Arquivos ignorados
├── 📄 pytest.ini                         # Config de testes
│
├── 📚 Documentos de Referência
│   ├── Artigo Lotofacil Extendido Corrigido (1).pdf
│   └── mcp_guia_implementacao_otimizador_lotofacil.md
│
├── 🔧 backend/                           # Backend Python
│   │
│   ├── 📄 __init__.py
│   ├── 📄 main.py                        # Aplicação FastAPI
│   ├── 📄 config.py                      # Configurações
│   ├── 📄 requirements.txt               # Dependências
│   ├── 📄 .env.example                   # Template de variáveis
│   │
│   ├── 📁 models/                        # Modelos de dados
│   │   ├── __init__.py
│   │   ├── dna.py                        # DNA evolutivo (19 genes)
│   │   ├── contest.py                    # Modelo de concurso
│   │   └── experiment.py                 # Modelo de experimento
│   │
│   ├── 📁 database/                      # Camada de dados
│   │   ├── __init__.py
│   │   ├── init.sql                      # Schema PostgreSQL
│   │   ├── connection.py                 # Conexões DB + Redis
│   │   │
│   │   └── 📁 repositories/              # Repositórios
│   │       ├── __init__.py
│   │       └── contest_repository.py     # CRUD de concursos
│   │
│   ├── 📁 api/                           # API REST
│   │   ├── __init__.py
│   │   │
│   │   └── 📁 routes/                    # Rotas
│   │       ├── __init__.py
│   │       └── contests.py               # Endpoints de concursos
│   │
│   ├── 📁 core/                          # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── feature_engineering.py        # [Fase 2] Features
│   │   ├── game_generator.py             # [Fase 3] Geração
│   │   ├── monte_carlo.py                # [Fase 4] Simulação
│   │   └── genetic_algorithm.py          # [Fase 5] AG
│   │
│   └── 📁 utils/                         # Utilitários
│       ├── __init__.py
│       └── data_importer.py              # Importador de dados
│
├── 🎨 frontend/                          # [Fase 7] Frontend React
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   │
│   └── 📁 src/
│       ├── 📁 components/                # Componentes React
│       │   ├── Dashboard.tsx
│       │   ├── ExperimentForm.tsx
│       │   ├── ConvergenceChart.tsx
│       │   └── TicketExport.tsx
│       │
│       ├── 📁 pages/                     # Páginas
│       │   ├── Home.tsx
│       │   ├── Experiments.tsx
│       │   └── Results.tsx
│       │
│       └── 📁 services/                  # Serviços
│           ├── api.ts
│           └── websocket.ts
│
├── 🧪 tests/                             # Testes
│   ├── __init__.py
│   ├── test_dna.py                       # Testes DNA
│   ├── test_contest.py                   # [Fase 1] Testes Contest
│   ├── test_features.py                  # [Fase 2] Testes Features
│   ├── test_generator.py                 # [Fase 3] Testes Geração
│   ├── test_monte_carlo.py               # [Fase 4] Testes MC
│   └── test_genetic_algorithm.py         # [Fase 5] Testes AG
│
└── 📜 scripts/                           # Scripts utilitários
    ├── init_project.sh                   # Setup inicial
    ├── validate_installation.sh          # Validação
    └── import_historical_data.py         # Importação de dados
```

## 🗂️ Detalhamento por Módulo

### 📊 Backend - Models

```python
backend/models/
├── dna.py              # DNA com 19 genes + operações genéticas
├── contest.py          # Concurso com validação de números
└── experiment.py       # Experimento com configurações AG
```

**Responsabilidades**:
- Validação de dados via Pydantic
- Operações genéticas (mutação, crossover)
- Serialização/deserialização

### 💾 Backend - Database

```python
backend/database/
├── init.sql            # Schema: 7 tabelas + índices + views
├── connection.py       # SessionLocal, Redis client
└── repositories/
    └── contest_repository.py  # CRUD otimizado
```

**Responsabilidades**:
- Gerenciamento de conexões
- Operações CRUD
- Queries otimizadas
- Cache Redis

### 🌐 Backend - API

```python
backend/api/routes/
└── contests.py         # 7 endpoints REST
```

**Endpoints Atuais**:
- `GET /` - Info da API
- `GET /health` - Health check
- `GET /contests` - Lista concursos
- `GET /contests/latest` - Último concurso
- `GET /contests/{id}` - Concurso específico
- `GET /contests/stats/summary` - Estatísticas
- `POST /contests/import/sync` - Sincronização

**Endpoints Futuros** (Fases 2-7):
- `POST /features/calculate` - Calcular features
- `POST /games/generate` - Gerar bolão
- `POST /simulate` - Simular bolão
- `POST /optimize/start` - Iniciar otimização
- `GET /optimize/{id}/progress` - Progresso
- `GET /optimize/{id}/result` - Resultado
- `POST /tickets/export` - Exportar bolão

### 🧠 Backend - Core (Lógica de Negócio)

```python
backend/core/
├── feature_engineering.py    # [Fase 2]
│   ├── FrequencyCalculator
│   ├── DelayCalculator
│   ├── RepetitionDetector
│   └── AffinityMatrix
│
├── game_generator.py          # [Fase 3]
│   ├── PoolSelector
│   ├── SoftmaxSampler
│   ├── GameGenerator
│   ├── StructuralScorer
│   └── DiversityOptimizer
│
├── monte_carlo.py             # [Fase 4]
│   ├── DrawSimulator
│   ├── CommonRandomNumbers
│   ├── PrizeEvaluator
│   ├── ROICalculator
│   └── RiskAnalyzer
│
└── genetic_algorithm.py       # [Fase 5]
    ├── Population
    ├── TournamentSelector
    ├── UniformCrossover
    ├── GaussianMutation
    ├── Elitism
    └── ConvergenceDetector
```

### 🛠️ Backend - Utils

```python
backend/utils/
└── data_importer.py
    ├── fetch_contest_from_api()
    ├── import_range()
    ├── import_from_csv()
    └── sync_latest()
```

## 🗄️ Estrutura do Banco de Dados

### Tabelas Principais

```sql
contests                    # Histórico de concursos
├── contest_id (PK)
├── draw_date
├── numbers (array)
└── created_at

experiments                 # Experimentos evolutivos
├── id (PK)
├── name
├── budget
├── config (JSONB)
├── status
└── best_fitness

individuals                 # População de DNAs
├── id (PK)
├── experiment_id (FK)
├── generation
├── dna (JSONB)
├── fitness
├── roi
└── risk

tickets                     # Bolões gerados
├── id (PK)
├── experiment_id (FK)
├── individual_id (FK)
├── games (JSONB)
└── total_cost

simulation_results          # Resultados Monte Carlo
├── id (PK)
├── individual_id (FK)
├── simulations
├── avg_return
├── std_return
└── prize_distribution (JSONB)

feature_cache              # Cache de features
├── id (PK)
├── feature_type
├── contest_id
├── data (JSONB)
└── version

execution_logs             # Logs de execução
├── id (PK)
├── experiment_id (FK)
├── level
├── message
└── metadata (JSONB)
```

### Índices Otimizados

```sql
-- Contests
CREATE INDEX idx_contests_date ON contests(draw_date DESC);
CREATE INDEX idx_contests_numbers ON contests USING GIN(numbers);

-- Experiments
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);

-- Individuals
CREATE INDEX idx_individuals_experiment ON individuals(experiment_id, generation);
CREATE INDEX idx_individuals_fitness ON individuals(fitness DESC);

-- Feature Cache
CREATE INDEX idx_feature_cache_type ON feature_cache(feature_type, contest_id);
```

## 📜 Scripts Utilitários

```bash
scripts/
├── init_project.sh              # Setup completo automático
├── validate_installation.sh     # Validação de instalação
└── import_historical_data.py    # Importação interativa
```

### Uso dos Scripts

```bash
# Setup inicial
bash scripts/init_project.sh

# Validar instalação
bash scripts/validate_installation.sh

# Importar dados
python scripts/import_historical_data.py
```

## 🧪 Estrutura de Testes

```python
tests/
├── test_dna.py                  # ✅ Implementado
│   ├── test_dna_gene_creation()
│   ├── test_dna_gene_validation()
│   ├── test_dna_random_generation()
│   ├── test_dna_mutation()
│   └── test_dna_crossover()
│
├── test_contest.py              # [Fase 1]
├── test_features.py             # [Fase 2]
├── test_generator.py            # [Fase 3]
├── test_monte_carlo.py          # [Fase 4]
└── test_genetic_algorithm.py    # [Fase 5]
```

## 📚 Documentação

```
Documentos/
├── README.md                    # Visão geral
├── INSTALL.md                   # Instalação detalhada
├── QUICKSTART.md                # Setup rápido
├── ROADMAP.md                   # Planejamento
├── STATUS.md                    # Status atual
├── IMPLEMENTATION_SUMMARY.md    # Resumo técnico
├── EXECUTIVE_SUMMARY.md         # Resumo executivo
└── PROJECT_STRUCTURE.md         # Este arquivo
```

## 🔄 Fluxo de Dados

```
1. Importação
   API Caixa → data_importer.py → PostgreSQL

2. Feature Engineering [Fase 2]
   PostgreSQL → feature_engineering.py → Redis Cache

3. Geração de Bolão [Fase 3]
   Features + DNA → game_generator.py → Bolão

4. Simulação [Fase 4]
   Bolão → monte_carlo.py → Métricas (ROI, Risco)

5. Otimização [Fase 5]
   População → genetic_algorithm.py → Melhor DNA

6. Persistência [Fase 6]
   Resultados → PostgreSQL → Checkpoints

7. Interface [Fase 7]
   Frontend → API → Backend → Database
```

## 🎯 Convenções de Código

### Python
- **Style**: PEP 8
- **Type hints**: Obrigatório
- **Docstrings**: Google style
- **Imports**: Ordenados (stdlib, third-party, local)

### SQL
- **Naming**: snake_case
- **Constraints**: Sempre nomeados
- **Índices**: Prefixo `idx_`

### API
- **Endpoints**: REST, plural
- **Status codes**: Padrão HTTP
- **Responses**: JSON
- **Docs**: OpenAPI automático

## 📊 Métricas de Código

| Métrica | Valor Atual | Meta Final |
|---------|-------------|------------|
| Arquivos | 30 | ~100 |
| LOC | 1.5k | ~10k |
| Cobertura | Base | >80% |
| Endpoints | 7 | ~20 |
| Modelos | 3 | ~10 |
| Testes | 6 | ~100 |

## 🚀 Evolução da Estrutura

### Fase 1 (Atual) ✅
- Base de dados
- Modelos core
- API básica
- Importação de dados

### Fase 2 (Próxima) 🔄
- `feature_engineering.py`
- `cache/feature_cache.py`
- Testes de features

### Fases 3-7 ⏳
- Módulos core completos
- Frontend React
- Testes completos
- Documentação expandida

---

**Última Atualização**: Fase 1 concluída  
**Versão**: 0.1.0  
**Total de Arquivos**: 30
