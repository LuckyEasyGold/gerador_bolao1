# STATUS - Lotofácil Gerador de Bolões

**Data:** 15 de abril de 2026  
**Versão:** 2.0 (Refatorada)  
**Status:** ✅ **PRONTO PARA TESTES**

---

## 🎯 Objetivo

Gerar bolões de Lotofácil otimizados baseado no orçamento investido.

**Entrada:** `valor_total, cotas, valor_unitario`  
**Saída:** `{j15, j16, j17}` - Quantidade de jogos em cada categoria  
**Tempo:** <100ms (instantâneo)

---

## ✅ Implementado

### 1. PoolDNA Simplificado
- Arquivo: `backend/models/pool_dna.py`
- Apenas pool de números (15-25)
- Operações: random, mutate, crossover

### 2. PoolGeneticAlgorithm 
- Arquivo: `backend/core/pool_genetic_algorithm.py`
- Evolui apenas 1 coisa: qual pool é melhor
- 20 gerações, população 10
- Tempo: ~2 minutos

### 3. PoolCacheManager
- Arquivo: `backend/core/pool_cache_manager.py`
- Salva pool ótimo em JSON
- Cache em `data/pools/`

### 4. simple_ticket_generator()
- Arquivo: `backend/core/simple_ticket_generator.py`
- Calcula distribuição j15, j16, j17
- Tempo: <100ms

### 5. Rotas API v2
- Arquivo: `backend/api/routes/pool_v2.py`
- 6 endpoints principais

---

## 📚 Documentação Essencial

| Arquivo | Uso |
|---------|-----|
| **README.md** | Visão geral |
| **INSTALL.md** | Como instalar e rodar |
| **PROJECT_STRUCTURE.md** | Estrutura de pastas |
| **SISTEMA_REFATORADO_v2.md** | Documentação técnica + exemplos |
| **ROADMAP.md** | Roadmap futuro |

---

## 🚀 Como Usar

```bash
# 1. Instalar
pip install -r backend/requirements.txt

# 2. Rodar backend
python -m uvicorn backend.main:app --reload

# 3. Encontrar pool (primeira vez, ~2 min)
POST /bolao/pool/encontrar

# 4. Gerar bolões (infinitas vezes, <100ms)
POST /bolao/gerar
```

Ver `SISTEMA_REFATORADO_v2.md` para exemplos completos.

---

## 📊 Estrutura

```
backend/
├── models/
│   ├── pool_dna.py                    ✅ Novo
│   ├── contest.py
│   └── dna.py (legado, pode remover)
├── core/
│   ├── pool_genetic_algorithm.py      ✅ Novo
│   ├── pool_cache_manager.py          ✅ Novo
│   ├── simple_ticket_generator.py     ✅ Novo
│   ├── monte_carlo.py
│   ├── game_generator.py (legado)
│   └── genetic_algorithm.py (legado)
├── api/routes/
│   ├── pool_v2.py                     ✅ Novo
│   └── [outras rotas legadas]
└── main.py (atualizado)
```

---

## ⚠️ Status Backend

- ✅ Nova arquitetura implementada
- ✅ Testes manuais possíveis
- ⏳ Frontend ainda usa API antiga
- ⏳ Sem testes unitários ainda

---

## 🔄 Próximas Ações

1. [ ] Testar endpoints em produção
2. [ ] Refatorar frontend
3. [ ] Remover código legado
4. [ ] Adicionar testes unitários
5. [ ] Deploy
