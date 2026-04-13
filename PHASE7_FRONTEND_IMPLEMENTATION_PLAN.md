# Fase 7 - Plano de Implementacao do Frontend Evolutivo

## Objetivo

Implementar a Fase 7 do projeto com foco em uma interface operacional para:

- iniciar e acompanhar experimentos evolutivos;
- visualizar a evolucao das geracoes;
- representar individuos como elementos graficos na tela;
- mostrar proximidade de um objetivo visual;
- consultar resultados, exportacao e dados auxiliares.

## Estado Inicial do Projeto

Na data de inicio desta implementacao, o workspace possui:

- backend FastAPI funcional;
- rotas para concursos, features, geracao, simulacao, otimizacao e persistencia;
- ausencia da pasta `frontend/` no repositorio;
- algoritmo genetico com estatisticas por geracao, mas sem snapshot visual detalhado por individuo.

## Estrategia Geral

### 1. Backend

Estender a API para expor um modelo visual da evolucao:

- snapshots de individuos por geracao;
- metricas normalizadas para mapeamento grafico;
- definicao de objetivo visual;
- resumo visual pronto para consumo pelo frontend.

### 2. Frontend

Criar um app em `React + TypeScript + Vite` com:

- dashboard principal;
- formulario para iniciar experimento;
- monitoramento de progresso;
- visualizacao evolutiva 2D/3D dos individuos;
- graficos auxiliares de convergencia e distribuicao;
- painel de resultados.

## Escopo do MVP

### Backend MVP

- enriquecer o fluxo de `/optimize/start`, `/optimize/status/{id}` e `/optimize/result/{id}`;
- salvar historico visual por geracao em memoria;
- adicionar endpoint dedicado para visualizacao evolutiva;
- manter compatibilidade com os endpoints atuais.

### Frontend MVP

- pagina unica orientada a dashboard;
- timeline de geracoes;
- cena 3D com individuos renderizados como esferas;
- alvo visual representando o objetivo;
- graficos 2D complementares;
- polling de status enquanto o experimento estiver em execucao.

## Modelo Visual Proposto

Cada individuo sera projetado no espaco com base em metricas do experimento:

- `x`: fitness normalizado;
- `y`: ROI normalizado;
- `z`: risco invertido ou diversidade local derivada;
- cor: qualidade geral / proximidade do objetivo;
- escala: destaque para elite ou lideranca;
- brilho/opacidade: distancia ao objetivo.

O objetivo visual sera definido por um perfil-alvo simples:

- fitness alto;
- ROI alto;
- risco baixo.

O frontend exibira:

- a populacao atual;
- o melhor individuo;
- a trajetoria de melhoria entre geracoes;
- quao perto a populacao esta do objetivo.

## Endpoints Planejados

### Ajustes em endpoints existentes

- `POST /optimize/start`
  - continua iniciando experimento;
  - retorna estrutura suficiente para iniciar tela de acompanhamento.

- `GET /optimize/status/{experiment_id}`
  - passa a incluir snapshot resumido da geracao atual;
  - inclui distancia media ao objetivo.

- `GET /optimize/result/{experiment_id}`
  - passa a incluir serie visual historica e resumo pronto para dashboard.

### Novo endpoint

- `GET /optimize/visual/{experiment_id}`
  - retorna payload especifico para visualizacao;
  - suporta timeline completa por geracao.

## Estrutura Prevista do Frontend

```text
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    main.tsx
    App.tsx
    styles/
      global.css
    components/
      ExperimentControlPanel.tsx
      EvolutionScene.tsx
      EvolutionTimeline.tsx
      MetricsBar.tsx
      ConvergencePanel.tsx
      ResultSummary.tsx
    services/
      api.ts
    types/
      api.ts
```

## Ordem de Implementacao

1. Documentar esta estrategia.
2. Estender o backend para capturar snapshots visuais por geracao.
3. Adicionar endpoint visual dedicado.
4. Criar estrutura base do frontend com Vite + React + TypeScript.
5. Implementar dashboard, formulario e polling.
6. Implementar cena 3D com `react-three-fiber`.
7. Integrar graficos 2D e resumo final.
8. Atualizar README e instrucoes de uso.

## Ponto de Retomada

Se a implementacao for interrompida, retomar nesta ordem:

1. verificar se `PHASE7_FRONTEND_IMPLEMENTATION_PLAN.md` existe e esta atualizado;
2. verificar se o backend ja expoe snapshots visuais em `/optimize/visual/{experiment_id}`;
3. verificar se a pasta `frontend/` foi criada;
4. executar validacoes de build do backend e frontend;
5. continuar a partir do primeiro item pendente.

## Criticos Tecnicos

- o backend atual roda experimentos em memoria, entao a visualizacao tambem sera mantida em memoria no MVP;
- o projeto ainda nao possui WebSocket, entao o frontend usara polling inicialmente;
- a visualizacao 3D precisa continuar funcional mesmo sem dados completos, com fallback para estado vazio;
- o build do frontend depende de Node e instalacao de dependencias.

## Criterios de Conclusao

Considerar a Fase 7 MVP concluida quando:

- existir frontend funcional na pasta `frontend/`;
- for possivel iniciar experimento pela UI;
- a UI mostrar progresso e resultados;
- a evolucao dos individuos puder ser visualizada de forma grafica;
- a documentacao refletir como rodar e retomar o sistema.
