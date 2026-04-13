# Otimizador de Bolões Lotofácil

<p align="center">
  Plataforma de otimização evolutiva para geração, simulação e análise visual de bolões da Lotofácil.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-mvp%20visual-1f8f5f" alt="status" />
  <img src="https://img.shields.io/badge/backend-FastAPI-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/frontend-React%20%2B%20Three.js-1e3a8a" alt="React Three" />
  <img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-informational" alt="license" />
</p>

## Sobre o projeto

O **Otimizador de Bolões Lotofácil** é um sistema que combina:

- ingestão e análise de concursos históricos;
- engenharia de features estatísticas;
- geração estrutural de jogos;
- simulação Monte Carlo;
- algoritmo genético para evolução de estratégias;
- persistência e reprodutibilidade;
- frontend visual para acompanhar a evolução dos indivíduos.

O objetivo é permitir que o usuário não apenas execute otimizações, mas também **entenda visualmente como a população evolui**, quão perto está do alvo desejado e como o melhor DNA se comporta ao longo das gerações.

## Status

### Fases concluídas

- [x] Fase 1: Base de dados e ingestão
- [x] Fase 2: Feature engineering
- [x] Fase 3: Motor de geração estrutural
- [x] Fase 4: Simulador Monte Carlo
- [x] Fase 5: Algoritmo genético
- [x] Fase 6: Persistência e reprodutibilidade
- [x] Fase 7: Frontend MVP visual

### Entregue no MVP atual

- API FastAPI com rotas de concursos, features, jogos, simulação, otimização e persistência
- rastreamento de experimentos em execução
- snapshots visuais por geração
- endpoint dedicado para visualização evolutiva
- frontend React + TypeScript + Vite
- visualização 3D dos indivíduos com alvo evolutivo
- timeline de gerações
- gráfico de convergência
- resumo do melhor DNA

## Arquitetura

```text
gerador_bolao/
├── backend/                  # API, domínio e motor evolutivo
│   ├── api/routes/           # Endpoints REST
│   ├── core/                 # Features, geração, simulação, GA e persistência
│   ├── database/             # Conexão e repositórios
│   └── models/               # Modelos Pydantic
├── frontend/                 # Dashboard React + cena 3D
├── scripts/                  # Utilitários e demos
├── tests/                    # Testes automatizados
└── PHASE7_FRONTEND_IMPLEMENTATION_PLAN.md
```

## Stack

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- NumPy / SciPy / Pandas / Numba

### Frontend

- React
- TypeScript
- Vite
- Recharts
- Three.js
- React Three Fiber
- Drei

## Visualização evolutiva

O frontend introduz uma leitura visual do algoritmo genético:

- cada indivíduo é representado como um elemento 3D;
- a posição no espaço reflete métricas da solução;
- cor, escala e opacidade indicam qualidade e proximidade do objetivo;
- o alvo visual representa o perfil desejado de alto fitness, alto ROI e risco reduzido;
- a timeline permite navegar pela evolução geração por geração.

### Mapeamento visual do MVP

- `x`: fitness normalizado
- `y`: ROI normalizado
- `z`: risco invertido
- cor: distância até o objetivo
- escala: destaque para indivíduos elite

## Endpoints principais

### Otimização

- `POST /optimize/start`
- `GET /optimize/status/{experiment_id}`
- `GET /optimize/result/{experiment_id}`
- `GET /optimize/visual/{experiment_id}`
- `GET /optimize/list`
- `DELETE /optimize/cancel/{experiment_id}`
- `POST /optimize/quick`

### Outros módulos

- `/contests/*`
- `/features/*`
- `/games/*`
- `/simulate/*`
- `/persistence/*`

Documentação interativa:

- [http://localhost:8000/docs](http://localhost:8000/docs)

## Como rodar localmente

### 1. Suba a infraestrutura

```bash
docker-compose up -d
```

### 2. Instale o backend

```bash
cd backend
pip install -r requirements.txt
```

### 3. Instale o frontend

```bash
cd ../frontend
npm install
```

### 4. Importe os dados históricos

```bash
cd ..
python scripts/import_historical_data.py
```

### 5. Inicie a API

```bash
python -m backend.main
```

### 6. Inicie o frontend

```bash
cd frontend
npm run dev
```

### Endereços locais

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend: [http://localhost:5173](http://localhost:5173)

## Fluxo de uso

1. O usuário inicia um experimento pelo frontend.
2. O frontend chama `POST /optimize/start`.
3. O progresso é acompanhado por polling com `GET /optimize/status/{id}`.
4. A timeline visual é consumida em `GET /optimize/visual/{id}`.
5. Ao final, o frontend busca `GET /optimize/result/{id}`.
6. O dashboard exibe convergência, melhor DNA e evolução da população.

## Desenvolvimento

### Validar backend

```bash
pytest tests/ -v
```

### Build do frontend

```bash
cd frontend
npm run build
```

## Documentação do projeto

- [PHASE7_FRONTEND_IMPLEMENTATION_PLAN.md](PHASE7_FRONTEND_IMPLEMENTATION_PLAN.md)
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- [ROADMAP.md](ROADMAP.md)
- [STATUS.md](STATUS.md)
- [INSTALL.md](INSTALL.md)
- [QUICKSTART.md](QUICKSTART.md)
- [PHASE5_COMPLETE.md](PHASE5_COMPLETE.md)
- [PHASE6_COMPLETE.md](PHASE6_COMPLETE.md)

## Próximas melhorias

- WebSocket para progresso em tempo real
- persistência dos snapshots visuais em banco/Redis
- comparação visual entre experimentos
- exportação visual dos resultados
- redução do bundle do frontend com code splitting

## Observações

- o MVP atual usa polling, não WebSocket;
- os experimentos em execução ficam em memória no backend;
- a camada visual já está funcional e pronta para evoluções.
