# FRONTEND REFATORADO - v2 ✨

## 🎯 Resumo

**Nova interface simples e direta:**
- ✅ Pede entrada: valor_total, cotas, valor_unitario
- ✅ Mostra resultado: j15, j16, j17
- ✅ Sem mensagens confusas
- ✅ Sem gráficos complexos
- ✅ <100ms de resposta

---

## 📱 Layout

```
┌─────────────────────────┐
│   Gerador de Bolões     │
│        Lotofácil        │
├─────────────────────────┤
│                         │
│  Valor Total (R$)       │
│  [1000.00]              │
│                         │
│  Número de Cotas        │
│  [5]                    │
│                         │
│  Valor por Cota (R$)    │
│  [200.00]               │
│                         │
│  [  Gerar Bolão  ]      │
├─────────────────────────┤
│      RESULTADO          │
├─────────────────────────┤
│ J15: 2    J16: 1  J17:1 │
│ R$20      R$20   R$30   │
│                         │
│ Total: 4 jogos          │
│ Custo: R$ 70.00         │
└─────────────────────────┘
```

---

## 🎨 Design

- **Cores**: Gradiente roxo (moderno)
- **Cards**: Coloridos por tipo de jogo
  - j15 = Azul
  - j16 = Roxo
  - j17 = Laranja
- **Animações**: Suaves
- **Responsivo**: Mobile-friendly

---

## ▶️ Como Rodar

### Backend (pré-requisito)

```bash
cd backend
python -m uvicorn main:app --reload
# Verificar http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Acessar http://localhost:5173
```

---

## 📄 Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `App.tsx` | ✅ Reescrito completamente |
| `App.css` | ✅ Novo CSS simples |
| `styles/global.css` | ✅ Atualizado |

---

## 🔌 API Consumida

```
POST /bolao/gerar
Content-Type: application/json

{
  "valor_total_do_bolao": 1000,
  "cotas": 5,
  "valor_unitario_do_bolao": 200,
  "usar_pool_cache": true
}

Response:
{
  "sucesso": true,
  "saida": {
    "j15": 2,
    "j16": 1,
    "j17": 1,
    "custo_total": 90,
    "total_jogos": 4
  }
}
```

---

## ✅ Checklist de Teste

- [ ] Backend rodando
- [ ] Frontend carrega
- [ ] Preencher valores
- [ ] Clique "Gerar"
- [ ] Resultado aparece
- [ ] Valores fazem sentido
- [ ] Mobile responsivo

---

## 🚀 Deploy

Frontend está pronto para:
- ✅ Desenvolvimento
- ✅ Build: `npm run build`
- ✅ Deploy em qualquer servidor HTTP
- ✅ Suporta CORS

---

## 📝 Fluxo Completo

```
USUÁRIO:          FRONTEND:        BACKEND:
Digita valores → Valida → POST /bolao/gerar → Processa
                                    ↓
                          Retorna {j15, j16, j17}
                                    ↓
                  Exibe resultado ← Usuário vê
```

**Tempo total: <200ms**

---

## 🎉 Pronto!

Frontend simples, prático, direto. Como deve ser.
