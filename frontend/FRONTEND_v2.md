# Frontend v2 - Interface Simples

## 🎯 Propósito

Interface simples e intuitiva para gerar bolões de Lotofácil.

**Sem:**
- ❌ Gráficos confusos
- ❌ Explicações técnicas
- ❌ Mensagens sobre algoritmos genéticos
- ❌ Visualizações 3D complexas

**Apenas:**
- ✅ Formulário para entrada
- ✅ Botão gerar
- ✅ Resultado claro

---

## 📋 Como Usar

### 1. Preencher Valores

```
Valor Total (R$): 1000.00
Número de Cotas: 5
Valor por Cota (R$): 200.00
```

### 2. Clicar "Gerar Bolão"

O sistema calcula em <100ms

### 3. Ver Resultado

```
Jogos 15 números: 2  (R$ 20.00)
Jogos 16 números: 1  (R$ 20.00)
Jogos 17 números: 1  (R$ 30.00)

Total de Jogos: 4
Custo Total: R$ 70.00
```

---

## 🖥️ Requisitos

### Backend
- [ ] Backend rodando em `http://localhost:8000`
- [ ] Endpoint `/bolao/gerar` ativo
- [ ] Pool em cache disponível (ou usar padrão)

### Frontend
- [ ] Node.js 16+
- [ ] npm ou yarn

---

## ▶️ Rodar 

```bash
# 1. Instalar dependências
cd frontend
npm install

# 2. Rodar dev server
npm run dev

# 3. Acessar
http://localhost:5173
```

---

## 📦 Dependências

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0"
}
```

---

## 🎨 Design

- **Gradiente**: Roxo (#667eea → #764ba2)
- **Cards**: Cores para cada tipo de jogo
  - j15: Azul
  - j16: Roxo
  - j17: Laranja
- **Animações**: Suaves e rápidas
- **Responsive**: Funciona em mobile

---

## 📝 Notas

- Interface é 100% cliente-lado (React)
- Chamadas AJAX ao endpoint `/bolao/gerar`
- CORS habilitado no backend
- Sem estado global (usa useState apenas)

---

## 🔄 Fluxo Simples

```
Usuário digita → Clica "Gerar" → API processa → Resultado exibe
```

Simples, rápido, direto.
