# 📋 Fase 6: Persistência e Reprodutibilidade - Planejamento

## 🎯 Objetivos da Fase 6

Implementar sistema completo de persistência, versionamento e reprodutibilidade para garantir auditoria total e replay de experimentos.

**Status**: 🔄 PRÓXIMA FASE  
**Duração Estimada**: 1-2 semanas  
**Dependências**: Fases 1-5 ✅

---

## 📦 Componentes a Implementar

### 1. CheckpointManager
**Arquivo**: `backend/core/persistence/checkpoint_manager.py`

**Responsabilidades**:
- Salvar estado completo por geração
- Carregar checkpoints para retomar
- Gerenciar armazenamento (DB + filesystem)
- Limpeza de checkpoints antigos

**Interface**:
```python
class CheckpointManager:
    def save_checkpoint(self, experiment_id: str, generation: int, 
                       population: Population, stats: GenerationStats) -> str
    def load_checkpoint(self, checkpoint_id: str) -> CheckpointData
    def list_checkpoints(self, experiment_id: str) -> List[CheckpointInfo]
    def delete_checkpoint(self, checkpoint_id: str) -> bool
    def cleanup_old_checkpoints(self, days: int = 30) -> int
```

**Dados a Persistir**:
- ID do experimento
- Geração atual
- População completa (todos os DNAs)
- Estatísticas da geração
- Timestamp
- Configuração do experimento
- Seeds utilizadas

---

### 2. SeedManager
**Arquivo**: `backend/core/persistence/seed_manager.py`

**Responsabilidades**:
- Versionamento de seeds
- Garantir reprodutibilidade
- Rastreamento de seeds por componente
- Validação de seeds

**Interface**:
```python
class SeedManager:
    def register_seed(self, experiment_id: str, component: str, 
                     seed: int) -> None
    def get_seeds(self, experiment_id: str) -> Dict[str, int]
    def validate_seeds(self, experiment_id: str) -> bool
    def generate_seed_chain(self, master_seed: int, 
                           components: List[str]) -> Dict[str, int]
```

**Seeds a Gerenciar**:
- Master seed (global)
- Population seed
- Selector seed
- Operators seed
- Evaluator seed
- Monte Carlo seed
- Game Generator seed

---

### 3. ExperimentLogger
**Arquivo**: `backend/core/persistence/experiment_logger.py`

**Responsabilidades**:
- Logs estruturados de execução
- Métricas por geração
- Eventos importantes
- Erros e warnings

**Interface**:
```python
class ExperimentLogger:
    def log_start(self, experiment_id: str, config: ExperimentConfig) -> None
    def log_generation(self, experiment_id: str, generation: int, 
                      stats: GenerationStats) -> None
    def log_convergence(self, experiment_id: str, generation: int) -> None
    def log_completion(self, experiment_id: str, result: EvolutionResult) -> None
    def log_error(self, experiment_id: str, error: Exception) -> None
    def get_logs(self, experiment_id: str) -> List[LogEntry]
```

**Logs a Registrar**:
- Início do experimento
- Configuração utilizada
- Estatísticas por geração
- Eventos de convergência
- Conclusão do experimento
- Erros e exceções
- Tempo de execução

---

### 4. ReplayEngine
**Arquivo**: `backend/core/persistence/replay_engine.py`

**Responsabilidades**:
- Replay completo de experimentos
- Validação de reprodutibilidade
- Comparação de resultados
- Debug de experimentos

**Interface**:
```python
class ReplayEngine:
    def replay_experiment(self, experiment_id: str) -> EvolutionResult
    def replay_from_checkpoint(self, checkpoint_id: str) -> EvolutionResult
    def validate_reproducibility(self, experiment_id: str) -> ValidationReport
    def compare_results(self, original_id: str, 
                       replay_id: str) -> ComparisonReport
```

**Funcionalidades**:
- Replay completo usando seeds originais
- Replay parcial a partir de checkpoint
- Validação bit-a-bit de reprodutibilidade
- Comparação de métricas
- Identificação de divergências

---

### 5. ExportManager
**Arquivo**: `backend/core/persistence/export_manager.py`

**Responsabilidades**:
- Exportação de bolões
- Múltiplos formatos
- Validação de exportação
- Metadados completos

**Interface**:
```python
class ExportManager:
    def export_ticket(self, ticket: Ticket, format: str) -> bytes
    def export_experiment(self, experiment_id: str, format: str) -> bytes
    def export_dna(self, dna: DNA, format: str) -> bytes
    def validate_export(self, exported_data: bytes, format: str) -> bool
```

**Formatos de Exportação**:
- JSON (estruturado)
- CSV (planilha)
- PDF (imprimível)
- TXT (simples)
- XML (intercâmbio)

**Dados a Exportar**:
- Jogos do bolão
- Custo total
- DNA utilizado
- Estatísticas de simulação
- Metadados do experimento
- Timestamp de geração

---

## 🗄️ Schema de Banco de Dados

### Tabela: checkpoints
```sql
CREATE TABLE checkpoints (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id),
    generation INT NOT NULL,
    population_data JSONB NOT NULL,
    stats_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    file_path TEXT,
    UNIQUE(experiment_id, generation)
);

CREATE INDEX idx_checkpoints_experiment ON checkpoints(experiment_id);
CREATE INDEX idx_checkpoints_generation ON checkpoints(generation);
```

### Tabela: experiment_logs
```sql
CREATE TABLE experiment_logs (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id),
    log_level VARCHAR(20) NOT NULL,
    log_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_logs_experiment ON experiment_logs(experiment_id);
CREATE INDEX idx_logs_created ON experiment_logs(created_at);
```

### Tabela: seed_registry
```sql
CREATE TABLE seed_registry (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id),
    component VARCHAR(100) NOT NULL,
    seed BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(experiment_id, component)
);

CREATE INDEX idx_seeds_experiment ON seed_registry(experiment_id);
```

### Tabela: exports
```sql
CREATE TABLE exports (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id),
    export_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_exports_experiment ON exports(experiment_id);
```

---

## 🔌 API REST Endpoints

### Checkpoints
- `POST /checkpoints/save` - Salvar checkpoint
- `GET /checkpoints/{id}` - Obter checkpoint
- `GET /checkpoints/experiment/{id}` - Listar checkpoints
- `DELETE /checkpoints/{id}` - Deletar checkpoint
- `POST /checkpoints/cleanup` - Limpar antigos

### Seeds
- `GET /seeds/experiment/{id}` - Obter seeds
- `POST /seeds/validate/{id}` - Validar seeds
- `POST /seeds/generate` - Gerar chain de seeds

### Logs
- `GET /logs/experiment/{id}` - Obter logs
- `GET /logs/experiment/{id}/errors` - Obter erros
- `GET /logs/experiment/{id}/stats` - Obter estatísticas

### Replay
- `POST /replay/experiment/{id}` - Replay completo
- `POST /replay/checkpoint/{id}` - Replay de checkpoint
- `POST /replay/validate/{id}` - Validar reprodutibilidade
- `POST /replay/compare` - Comparar resultados

### Export
- `POST /export/ticket/{id}` - Exportar bolão
- `POST /export/experiment/{id}` - Exportar experimento
- `POST /export/dna/{id}` - Exportar DNA
- `GET /export/{id}/download` - Download de exportação

---

## 🧪 Testes a Implementar

### test_checkpoint_manager.py
- test_save_checkpoint
- test_load_checkpoint
- test_list_checkpoints
- test_delete_checkpoint
- test_cleanup_old_checkpoints
- test_checkpoint_integrity
- test_checkpoint_compression

### test_seed_manager.py
- test_register_seed
- test_get_seeds
- test_validate_seeds
- test_generate_seed_chain
- test_seed_uniqueness
- test_seed_reproducibility

### test_experiment_logger.py
- test_log_start
- test_log_generation
- test_log_convergence
- test_log_completion
- test_log_error
- test_get_logs
- test_log_filtering

### test_replay_engine.py
- test_replay_experiment
- test_replay_from_checkpoint
- test_validate_reproducibility
- test_compare_results
- test_replay_with_errors
- test_partial_replay

### test_export_manager.py
- test_export_ticket_json
- test_export_ticket_csv
- test_export_ticket_pdf
- test_export_experiment
- test_export_dna
- test_validate_export
- test_export_formats

---

## 📝 Scripts de Demonstração

### demo_persistence.py
```python
# Demo 1: Checkpoints
# - Salvar checkpoint
# - Carregar checkpoint
# - Retomar execução

# Demo 2: Seeds
# - Registrar seeds
# - Validar reprodutibilidade
# - Gerar chain de seeds

# Demo 3: Logs
# - Registrar eventos
# - Consultar logs
# - Filtrar por tipo

# Demo 4: Replay
# - Replay completo
# - Validar reprodutibilidade
# - Comparar resultados

# Demo 5: Export
# - Exportar bolão (JSON, CSV, PDF)
# - Exportar experimento
# - Exportar DNA
```

---

## 📊 Critérios de Aceite

### Funcionalidade
- [ ] Checkpoints salvos e carregados corretamente
- [ ] Seeds versionadas e reproduzíveis
- [ ] Logs completos e estruturados
- [ ] Replay 100% reproduzível
- [ ] Exportação em múltiplos formatos

### Performance
- [ ] Checkpoint < 1s para salvar
- [ ] Checkpoint < 1s para carregar
- [ ] Replay com mesma performance do original
- [ ] Exportação < 5s

### Qualidade
- [ ] 40+ testes unitários
- [ ] Cobertura > 90%
- [ ] Documentação completa
- [ ] API REST funcional

### Integração
- [ ] Integra com Fase 5 (GA)
- [ ] Integra com Fase 4 (Monte Carlo)
- [ ] Integra com Fase 3 (Game Generator)
- [ ] Schema DB atualizado

---

## 🎯 Ordem de Implementação

1. **Semana 1**:
   - CheckpointManager (2 dias)
   - SeedManager (1 dia)
   - ExperimentLogger (1 dia)
   - Testes unitários (1 dia)

2. **Semana 2**:
   - ReplayEngine (2 dias)
   - ExportManager (2 dias)
   - API REST (1 dia)
   - Script de demo (1 dia)
   - Documentação (1 dia)

---

## 📚 Referências

- Fase 5: `PHASE5_COMPLETE.md`
- Guia MCP: `mcp_guia_implementacao_otimizador_lotofacil.md`
- Roadmap: `ROADMAP.md`
- Status: `STATUS.md`

---

## ✅ Checklist de Início

Antes de começar a Fase 6:
- [x] Fase 5 100% completa
- [x] Testes da Fase 5 passando
- [x] Documentação da Fase 5 completa
- [x] API da Fase 5 funcional
- [ ] Schema DB revisado
- [ ] Estrutura de pastas criada
- [ ] Dependências instaladas

---

**Próximo Passo**: Criar estrutura de pastas e iniciar CheckpointManager

```bash
mkdir -p backend/core/persistence
touch backend/core/persistence/__init__.py
touch backend/core/persistence/checkpoint_manager.py
```

---

**Planejamento criado**: 2024  
**Status**: 🔄 PRONTO PARA INICIAR  
**Fase Anterior**: Fase 5 ✅  
**Próxima Fase**: Fase 7
