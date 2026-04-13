#!/bin/bash

# Script de validação da instalação
# Verifica se todos os componentes estão funcionando corretamente

echo "🔍 Validando Instalação do Lotofácil Optimizer"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Função para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ((ERRORS++))
    fi
}

# 1. Verificar Docker
echo "1. Verificando Docker..."
docker --version > /dev/null 2>&1
check "Docker instalado"

docker-compose --version > /dev/null 2>&1
check "Docker Compose instalado"

# 2. Verificar containers
echo ""
echo "2. Verificando containers..."
docker ps | grep lotofacil_postgres > /dev/null 2>&1
check "PostgreSQL rodando"

docker ps | grep lotofacil_redis > /dev/null 2>&1
check "Redis rodando"

# 3. Verificar PostgreSQL
echo ""
echo "3. Verificando PostgreSQL..."
docker exec lotofacil_postgres pg_isready -U lotofacil_user -d lotofacil > /dev/null 2>&1
check "PostgreSQL respondendo"

# Verificar tabelas
TABLES=$(docker exec lotofacil_postgres psql -U lotofacil_user -d lotofacil -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
if [ "$TABLES" -ge 7 ]; then
    echo -e "${GREEN}✓${NC} Tabelas criadas ($TABLES tabelas)"
else
    echo -e "${RED}✗${NC} Tabelas não criadas"
    ((ERRORS++))
fi

# 4. Verificar Redis
echo ""
echo "4. Verificando Redis..."
docker exec lotofacil_redis redis-cli ping > /dev/null 2>&1
check "Redis respondendo"

# 5. Verificar Python
echo ""
echo "5. Verificando Python..."
python3 --version > /dev/null 2>&1
check "Python 3 instalado"

# 6. Verificar estrutura de arquivos
echo ""
echo "6. Verificando estrutura de arquivos..."

FILES=(
    "backend/main.py"
    "backend/config.py"
    "backend/models/dna.py"
    "backend/models/contest.py"
    "backend/models/experiment.py"
    "backend/database/init.sql"
    "backend/database/connection.py"
    "backend/api/routes/contests.py"
    "docker-compose.yml"
    "README.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file não encontrado"
        ((ERRORS++))
    fi
done

# 7. Verificar dependências Python (se venv ativo)
echo ""
echo "7. Verificando dependências Python..."
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate 2>/dev/null || source backend/venv/Scripts/activate 2>/dev/null
    
    python -c "import fastapi" 2>/dev/null
    check "FastAPI instalado"
    
    python -c "import sqlalchemy" 2>/dev/null
    check "SQLAlchemy instalado"
    
    python -c "import redis" 2>/dev/null
    check "Redis client instalado"
    
    python -c "import numpy" 2>/dev/null
    check "NumPy instalado"
    
    python -c "import pydantic" 2>/dev/null
    check "Pydantic instalado"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment não encontrado (execute: python -m venv backend/venv)"
fi

# 8. Testar API (se estiver rodando)
echo ""
echo "8. Testando API..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$API_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} API respondendo (HTTP 200)"
else
    echo -e "${YELLOW}⚠${NC} API não está rodando (inicie com: python -m backend.main)"
fi

# Resumo
echo ""
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Instalação validada com sucesso!${NC}"
    echo ""
    echo "Próximos passos:"
    echo "1. Iniciar API: cd backend && python -m backend.main"
    echo "2. Importar dados: python scripts/import_historical_data.py"
    echo "3. Acessar docs: http://localhost:8000/docs"
else
    echo -e "${RED}✗ Encontrados $ERRORS erros${NC}"
    echo ""
    echo "Corrija os erros acima e execute novamente."
    exit 1
fi
