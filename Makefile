.PHONY: help setup start stop test clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make setup    - Configura ambiente inicial"
	@echo "  make start    - Sobe a aplicação completa"
	@echo "  make stop     - Para a aplicação"
	@echo "  make test     - Executa testes"
	@echo "  make clean    - Limpa arquivos temporários"

setup:
	@echo "Configurando ambiente..."
	@if not exist backend\.env copy backend\.env.example backend\.env >nul
	powershell -ExecutionPolicy Bypass -File scripts\start_app.ps1
	@echo "✓ Ambiente configurado!"

start:
	powershell -ExecutionPolicy Bypass -File scripts\start_app.ps1

stop:
	powershell -ExecutionPolicy Bypass -File scripts\stop_app.ps1

test:
	cd backend && pytest tests/ -v --cov=backend

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "✓ Arquivos temporários removidos"
