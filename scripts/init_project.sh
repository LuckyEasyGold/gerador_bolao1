#!/bin/bash

echo "🚀 Inicializando Lotofácil Optimizer..."

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

# Verifica Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
fi

# Cria .env se não existir
if [ ! -f backend/.env ]; then
    echo "${YELLOW}Criando arquivo .env...${NC}"
    cp backend/.env.example backend/.env
    echo "${GREEN}✓ Arquivo .env criado${NC}"
fi

# Inicia containers
echo "${YELLOW}Iniciando PostgreSQL e Redis...${NC}"
docker-compose up -d

# Aguarda serviços
echo "${YELLOW}Aguardando serviços ficarem prontos...${NC}"
sleep 10

# Verifica PostgreSQL
echo "${YELLOW}Verificando PostgreSQL...${NC}"
docker exec lotofacil_postgres pg_isready -U lotofacil_user -d lotofacil
if [ $? -eq 0 ]; then
    echo "${GREEN}✓ PostgreSQL pronto${NC}"
else
    echo "❌ PostgreSQL não está respondendo"
    exit 1
fi

# Verifica Redis
echo "${YELLOW}Verificando Redis...${NC}"
docker exec lotofacil_redis redis-cli ping
if [ $? -eq 0 ]; then
    echo "${GREEN}✓ Redis pronto${NC}"
else
    echo "❌ Redis não está respondendo"
    exit 1
fi

echo ""
echo "${GREEN}✓ Infraestrutura inicializada com sucesso!${NC}"
echo ""
echo "Próximos passos:"
echo "1. cd backend"
echo "2. python -m venv venv"
echo "3. source venv/bin/activate  (Windows: venv\\Scripts\\activate)"
echo "4. pip install -r requirements.txt"
echo "5. python -m backend.main"
echo ""
echo "API estará disponível em: http://localhost:8000"
echo "Documentação: http://localhost:8000/docs"
