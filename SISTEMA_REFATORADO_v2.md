# Sistema Refatorado - Pool + Geração de Bolões

## 📋 Resumo das Mudanças

Este documento descreve as 5 mudanças principais implementadas para simplificar o sistema:

1. **✅ DNA Simples** - Apenas pool de números
2. **✅ GA Rápido** - Evolui apenas 1 coisa (20-30 gerações, <2 minutos)
3. **✅ Cache** - Salva pool ótimo para reutilização
4. **✅ Função Simples** - `gerar_bolao()` instantânea (<100ms)
5. **✅ Rotas Claras** - API com endpoints bem definidos

---

## 🚀 Como Usar

### Fluxo de Uso

```
1. PRIMEIRA VEZ: Encontrar pool ótimo
   POST /bolao/pool/encontrar
   → Executa GA em background
   → Salva em cache
   → Tempo: ~2 minutos

2. DEPOIS: Gerar bolões (infinitas vezes)
   POST /bolao/gerar
   → Usa pool do cache
   → Retorna j15, j16, j17
   → Tempo: <100ms
```

---

## 📚 API Endpoints

### 1️⃣ Encontrar Pool Ótimo

```bash
POST /bolao/pool/encontrar
```

**Request Body:**
```json
{
  "name": "Pool Ótimo Lotofácil",
  "generations": 20,
  "population_size": 10,
  "simulations": 500,
  "seed": null
}
```

**Response:**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Busca de pool ótimo iniciada em background",
  "config": {
    "generations": 20,
    "population_size": 10,
    "simulations": 500
  }
}
```

**Tempo esperado:** 90-120 segundos


### 2️⃣ Consultar Status da Busca

```bash
GET /bolao/pool/status/{task_id}
```

**Response (em execução):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Pool Ótimo Lotofácil",
  "status": "executando",
  "progress": 45,
  "current_generation": 9,
  "best_pool": [2, 4, 7, 9, 11, 13, 15, 17, 19, 21, 23, 24],
  "best_fitness": 0.67,
  "best_roi": 0.34
}
```

**Response (concluído):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Pool Ótimo Lotofácil",
  "status": "concluído",
  "progress": 100,
  "best_pool": [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 24],
  "best_fitness": 0.89,
  "best_roi": 0.45,
  "total_time": 105.34,
  "completed_at": "2026-04-15T10:35:00"
}
```


### 3️⃣ Obter Pool Ótimo em Cache

```bash
GET /bolao/pool/otimo
```

**Response:**
```json
{
  "sucesso": true,
  "pool": [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 24],
  "pool_size": 11,
  "fitness": 0.89,
  "roi": 0.45,
  "timestamp": "2026-04-15T10:35:00"
}
```


### 4️⃣ Gerar Bolão (A FUNÇÃO PRINCIPAL)

```bash
POST /bolao/gerar
```

**Request Body:**
```json
{
  "valor_total_do_bolao": 1000.0,
  "cotas": 5,
  "valor_unitario_do_bolao": 200.0,
  "usar_pool_cache": true
}
```

**Response:**
```json
{
  "sucesso": true,
  "entrada": {
    "valor_total_do_bolao": 1000.0,
    "cotas": 5,
    "valor_unitario_do_bolao": 200.0
  },
  "saida": {
    "j15": 2,
    "j16": 1,
    "j17": 1,
    "custo_total": 90.0,
    "valor_por_cota": 200.0,
    "total_cotas": 5,
    "total_jogos": 4,
    "pool_usado": [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 24]
  },
  "timestamp": "2026-04-15T10:36:00"
}
```

**Tempo esperado:** <100ms


### 5️⃣ Listar Histórico de Pools

```bash
GET /bolao/pool/historico?limit=10
```

**Response:**
```json
{
  "total": 3,
  "pools": [
    {
      "timestamp": "2026-04-15T10:35:00",
      "pool": [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 24],
      "pool_size": 11,
      "fitness": 0.89,
      "roi": 0.45
    },
    ...
  ]
}
```


### 6️⃣ Limpar Cache

```bash
DELETE /bolao/pool/cache
```

**Response:**
```json
{
  "sucesso": true,
  "mensagem": "Cache de pool removido"
}
```

---

## 📊 Exemplo Completo (Python)

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Encontrar pool ótimo (executa UMA VEZ)
print("1️⃣ Iniciando busca de pool ótimo...")
response = requests.post(
    f"{BASE_URL}/bolao/pool/encontrar",
    json={
        "name": "Pool Ótimo Lotofácil",
        "generations": 20,
        "population_size": 10,
        "simulations": 500
    }
)
task_id = response.json()["task_id"]
print(f"   Task ID: {task_id}")

# 2. Aguardar conclusão
print("2️⃣ Aguardando conclusão do GA...")
while True:
    response = requests.get(f"{BASE_URL}/bolao/pool/status/{task_id}")
    status = response.json()
    print(f"   Progresso: {status['progress']}% (Geração {status.get('current_generation', 0)})")
    
    if status["status"] == "concluído":
        print(f"   ✓ Pool ótimo encontrado: {status['best_pool']}")
        print(f"   ✓ Fitness: {status['best_fitness']:.4f}")
        break
    
    time.sleep(2)

# 3. Gerar bolão (executa INFINITAS VEZES, instantâneo)
print("\n3️⃣ Gerando bolões (usando pool do cache)...")
for i in range(3):
    response = requests.post(
        f"{BASE_URL}/bolao/gerar",
        json={
            "valor_total_do_bolao": 1000.0,
            "cotas": 5,
            "valor_unitario_do_bolao": 200.0,
            "usar_pool_cache": True
        }
    )
    result = response.json()["saida"]
    print(f"\n   Resultado {i+1}:")
    print(f"   - j15: {result['j15']} jogos (R$ {result['j15'] * 10:.2f})")
    print(f"   - j16: {result['j16']} jogos (R$ {result['j16'] * 20:.2f})")
    print(f"   - j17: {result['j17']} jogos (R$ {result['j17'] * 30:.2f})")
    print(f"   - Total: {result['total_jogos']} jogos (R$ {result['custo_total']:.2f})")
```

---

## 📈 Performance

| Operação | Tempo |  Frequência |
|----------|-------|-----------|
| Encontrar pool ótimo | ~2 min | 1× (primeira vez) |
| Gerar bolão | <100ms | ∞ (reutilizar sempre) |
| **Total primeira vez** | ~2 min | - |
| **Total próximas vezes** | <100ms | - |

---

## 📁 Estrutura de Arquivos Criados

```
backend/
├── models/
│   └── pool_dna.py                    # PoolDNA simplificado
├── core/
│   ├── pool_genetic_algorithm.py       # GA que evolui apenas pool
│   ├── pool_cache_manager.py          # Persistência em cache
│   └── simple_ticket_generator.py     # Função gerar_bolao() simples
├── api/
│   └── routes/
│       └── pool_v2.py                 # Novas rotas da API
└── main.py                            # (modificado para registrar rota)
```

---

## 🔧 Configuração

Adicione ao `.env` se necessário:

```env
# Custos dos jogos
COST_15=10.0
COST_16=20.0
COST_17=30.0
COST_18=40.0
COST_19=50.0
COST_20=60.0

# Diretório de cache
POOL_CACHE_DIR=./data/pools
```

---

## ✅ Checklist de Validação

- [x] DNA simplificado (apenas pool)
- [x] GA rápido (20-30 gerações)
- [x] Cache funcionando
- [x] `gerar_bolao()` instantâneo
- [x] Rotas da API claras e testáveis
- [x] Entrada: `(valor_total, cotas, valor_unitario)`
- [x] Saída: `{j15: x, j16: y, j17: z}`
- [x] Sem API da Caixa Econômica (removida)
- [x] Compreensível e manutenível

---

## 🚨 Próximos Passos

1. **Testar** endpoints no Postman/Thunder Client
2. **Validar** se performance condiz com expectativa (<2 min)
3. **Refatorar frontend** para usar nova API simples
4. **Documentar** casos de uso específicos
5. **Deploy** em produção

---

## ❓ Dúvidas Frequentes

**P: Por que removemos o GA anterior?**
R: Porque tentava evoluir 20+ parâmetros aleatoriamente, o que era ineficiente e incompreensível.

**P: O novo sistema encontra números melhores?**
R: Não necessariamente. Encontra a melhor COMBINAÇÃO de números. A diferença é que é muito mais rápido.

**P: Posso usar sem encontrar o pool?**
R: Sim! Se não houver pool em cache, a função usa todos os 25 números (padrão).

**P: Posso rodrigir o GA quantas vezes quiser?**
R: Sim! Toda vez que executa, sobrescreve o cache com o melhor encontrado.

---

**Data:** 15 de abril de 2026  
**Status:** ✅ Implementado e Pronto para Testes
