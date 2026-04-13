# Guia Mestre MCP — Implementação Completa do Otimizador de Bolões Lotofácil

## Objetivo
Este documento orienta agentes MCP no gerenciamento integral do projeto até a primeira versão funcional (MVP) do sistema de otimização de bolões Lotofácil descrito no artigo técnico principal.

---

## 1. Meta do Projeto
Construir um sistema capaz de:
- processar histórico de concursos da Lotofácil;
- gerar bolões otimizados automaticamente;
- evoluir estratégias via algoritmo genético;
- avaliar desempenho estatístico via Monte Carlo;
- expor interface/API para geração de bolões comerciais.

Entregável final da Fase 1:
> Sistema funcional capaz de gerar bolões otimizados parametrizados, reproduzíveis e estatisticamente avaliáveis.

---

## 2. Arquitetura Macro Obrigatória

### Backend Principal
Responsável por:
- motor evolutivo;
- simulação Monte Carlo;
- geração estrutural de jogos;
- persistência de experimentos;
- API pública/interna.

### Banco de Dados
Responsável por:
- concursos históricos;
- checkpoints evolutivos;
- resultados de simulações;
- DNA de estratégias;
- auditoria/logs.

### Frontend / Painel Operacional
Responsável por:
- configuração de campanhas de otimização;
- visualização de convergência;
- exportação de bolões;
- monitoramento de performance.

---

## 3. Schema Formal do DNA Evolutivo
Cada indivíduo deve conter os seguintes genes:

| Gene | Tipo | Range | Descrição |
|------|------|-------|-----------|
| w15 | float | [0,1] | Peso orçamento jogo 15 |
| w16 | float | [0,1] | Peso orçamento jogo 16 |
| w17 | float | [0,1] | Peso orçamento jogo 17 |
| wf | float | [-1,1] | Peso frequência histórica |
| wa | float | [-1,1] | Peso atraso |
| wr | float | [-1,1] | Peso repetição concurso anterior |
| wc_aff | float | [0,2] | Peso afinidade combinatória |
| T_base | float | [0.1,5] | Temperatura base |
| kappa | float | [0,1] | Modulação dinâmica temperatura |
| wp | float | [0,1] | Peso paridade |
| wl | float | [0,1] | Peso linhas/colunas |
| ws | float | [0,1] | Peso sequências |
| wo | float | [0,1] | Peso overlap local |
| wcov | float | [0,1] | Peso cobertura global |
| wd | float | [0,1] | Peso diversidade frequência |
| woverlap | float | [0,1] | Peso overlap global |
| pool_size | int | [18,25] | Tamanho do pool de dezenas |
| candidates_per_game | int | [10,200] | Candidatos por jogo |
| refine_iterations | int | [10,2000] | Iterações busca local |

---

## 4. Ordem Obrigatória de Implementação

### Fase 1 — Base de Dados e Ingestão
1. Criar schema relacional para concursos históricos.
2. Implementar importador CSV/API Caixa.
3. Validar integridade histórica.
4. Criar camada de versionamento de datasets.

### Fase 2 — Feature Engineering
1. Frequência histórica.
2. Atraso.
3. Repetição último concurso.
4. Matriz de afinidade Φ.
5. Cache incremental de features.

### Fase 3 — Motor de Geração Estrutural
1. Seleção gulosa do pool.
2. Softmax com temperatura dinâmica.
3. Geração estrutural de jogos.
4. Score estrutural por jogo.
5. Otimização global de diversidade.

### Fase 4 — Simulador Estatístico
1. Gerador de sorteios pseudoaleatórios.
2. Common Random Numbers.
3. Avaliação de premiações.
4. Agregação de retorno.
5. Penalização por risco.

### Fase 5 — Algoritmo Genético
1. Inicialização população.
2. Seleção por torneio.
3. Crossover uniforme.
4. Mutação gaussiana.
5. Elitismo.
6. Critérios de convergência.

### Fase 6 — Persistência e Reprodutibilidade
1. Checkpoints por geração.
2. Versionamento de seeds aleatórias.
3. Snapshot de hiperparâmetros.
4. Logs completos de execução.

### Fase 7 — API/Frontend MVP
1. Endpoint iniciar otimização.
2. Endpoint consultar progresso.
3. Endpoint exportar bolão.
4. Dashboard de convergência.
5. Dashboard de métricas estatísticas.

---

## 5. Regras de Implementação Obrigatórias

### Determinismo/Reprodutibilidade
- Toda execução deve aceitar seed global.
- Monte Carlo deve ser reproduzível.
- AG deve permitir replay integral.

### Performance
- Paralelizar avaliação Monte Carlo.
- Cachear features históricas.
- Reutilizar CRN por geração.
- Vetorizar operações sempre que possível.

### Segurança Algorítmica
- Clamp em todos genes após mutação.
- Validar ranges antes de avaliar indivíduo.
- Rejeitar bolões inválidos.

---

## 6. Critérios de Aceite do MVP
O sistema será considerado funcional quando:

1. Gerar bolão completo a partir de orçamento informado.
2. Executar otimização evolutiva fim-a-fim.
3. Produzir métricas estatísticas reproduzíveis.
4. Permitir exportação estruturada dos jogos.
5. Persistir histórico completo de execução.
6. Expor API operacional funcional.

---

## 7. Roadmap Pós-MVP
Somente após MVP estável:
- Otimização multiobjetivo ROI/Risco;
- Clusterização de estratégias por perfil;
- Ensemble de estratégias;
- Meta-learning de hiperparâmetros;
- Expansão para outras loterias.

---

## 8. Diretriz para Agentes MCP
Os agentes devem:

1. Seguir rigorosamente a ordem de implementação definida.
2. Não pular etapas arquiteturais.
3. Não alterar fórmulas sem aprovação explícita.
4. Documentar decisões de implementação.
5. Validar cada módulo isoladamente antes de integração.
6. Priorizar corretude matemática antes de otimização prematura.
7. Encerrar cada fase com testes unitários e integração.

---

## 9. Definição de Pronto
Projeto considerado concluído quando:
- backend executa pipeline completo sem intervenção manual;
- frontend permite operação comercial básica;
- resultados são reproduzíveis;
- arquitetura suporta evolução futura sem refactor estrutural.

---

## Status Final Esperado
> Primeira versão funcional pronta para testes reais, benchmark estatístico e preparação para ambiente de produção.

