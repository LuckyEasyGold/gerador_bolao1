.PHONY: help setup start stop test clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make setup    - Configura ambiente inicial"
	@echo "  make start    - Inicia infraestrutura (Docker)"
	@echo "  make stop     - Para infraestrutura"
	@echo "  make test     - Executa testes"
	@echo "  make clean    - Limpa arquivos temporários"

setup:
	@echo "Configurando ambiente..."
	cp backend/.env.example backend/.env
	docker-compose up -d
	@echo "Aguardando banco de dados..."
	sleep 5
	@echo "✓ Ambiente configurado!"

start:
	docker-compose up -d
	@echo "✓ Infraestrutura iniciada"

stop:
	docker-compose down
	@echo "✓ Infraestrutura parada"

test:
	cd backend && pytest tests/ -v --cov=backend

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "✓ Arquivos temporários removidos"
