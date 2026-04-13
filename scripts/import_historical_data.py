#!/usr/bin/env python3
"""
Script para importar dados históricos da Lotofácil
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db
from backend.utils.data_importer import LotofacilDataImporter


async def main():
    print("🎲 Importador de Dados Históricos - Lotofácil")
    print("=" * 50)
    
    with get_db() as db:
        importer = LotofacilDataImporter(db)
        
        # Verifica quantos concursos já existem
        from backend.database.repositories.contest_repository import ContestRepository
        repo = ContestRepository(db)
        count = repo.count()
        
        print(f"\n📊 Concursos já importados: {count}")
        
        if count > 0:
            latest = repo.get_latest()
            print(f"📅 Último concurso: {latest.contest_id} ({latest.draw_date})")
        
        print("\nOpções:")
        print("1. Sincronizar com API Caixa (importa apenas novos)")
        print("2. Importar range específico")
        print("3. Sair")
        
        choice = input("\nEscolha uma opção: ")
        
        if choice == "1":
            print("\n🔄 Sincronizando com API Caixa...")
            imported = await importer.sync_latest()
            print(f"✓ {imported} concursos importados")
            
        elif choice == "2":
            start = int(input("Concurso inicial: "))
            end = int(input("Concurso final: "))
            
            print(f"\n📥 Importando concursos {start} a {end}...")
            imported = await importer.import_range(start, end)
            print(f"✓ {imported} concursos processados")
        
        # Estatísticas finais
        count = repo.count()
        date_range = repo.get_date_range()
        
        print("\n" + "=" * 50)
        print("📊 Estatísticas Finais:")
        print(f"   Total de concursos: {count}")
        print(f"   Período: {date_range[0]} a {date_range[1]}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
