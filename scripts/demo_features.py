#!/usr/bin/env python3
"""
Script de demonstração das features de Feature Engineering
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.cache.feature_cache import FeatureCache
import numpy as np


def print_section(title: str):
    """Imprime seção formatada"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_frequencies():
    """Demonstra cálculo de frequências"""
    print_section("FREQUÊNCIAS HISTÓRICAS")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            print("❌ Nenhum concurso encontrado. Execute import_historical_data.py primeiro.")
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        print(f"\n📊 Analisando {len(contests)} concursos")
        
        # Top 10 mais frequentes
        top_10 = engineer.frequency_calc.get_top_k(10)
        print("\n🔝 Top 10 números mais frequentes:")
        for i, (num, freq) in enumerate(top_10, 1):
            print(f"   {i:2d}. Número {num:2d}: {freq:.2%}")


def demo_delays():
    """Demonstra cálculo de atrasos"""
    print_section("ATRASOS (DELAYS)")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        # Top 10 mais atrasados
        most_delayed = engineer.delay_calc.get_most_delayed(10)
        print("\n⏰ Top 10 números mais atrasados:")
        for i, (num, delay) in enumerate(most_delayed, 1):
            print(f"   {i:2d}. Número {num:2d}: {delay} concursos")


def demo_repetitions():
    """Demonstra detecção de repetições"""
    print_section("REPETIÇÕES DO ÚLTIMO CONCURSO")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        repeated = engineer.repetition_detector.get_repeated_numbers()
        last_contest = engineer.repetition_detector.last_contest
        
        print(f"\n🎲 Último concurso: {last_contest.contest_id}")
        print(f"📅 Data: {last_contest.draw_date}")
        print(f"\n🔢 Números sorteados ({len(repeated)}):")
        
        # Imprime em linhas de 5
        for i in range(0, len(repeated), 5):
            nums = repeated[i:i+5]
            print(f"   {' '.join(f'{n:2d}' for n in nums)}")


def demo_affinity():
    """Demonstra matriz de afinidade"""
    print_section("MATRIZ DE AFINIDADE")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        # Testa alguns números
        test_numbers = [1, 10, 20]
        
        for num in test_numbers:
            companions = engineer.affinity_matrix.get_best_companions(num, k=5)
            print(f"\n🤝 Melhores companheiros do número {num}:")
            for i, (comp, aff) in enumerate(companions, 1):
                print(f"   {i}. Número {comp:2d}: {aff:.2%} de afinidade")


def demo_scores():
    """Demonstra cálculo de scores"""
    print_section("SCORES PONDERADOS")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        # Testa diferentes combinações de pesos
        weight_configs = [
            {"name": "Balanceado", "wf": 0.33, "wa": 0.33, "wr": 0.34},
            {"name": "Foco Frequência", "wf": 0.7, "wa": 0.2, "wr": 0.1},
            {"name": "Foco Atraso", "wf": 0.1, "wa": 0.8, "wr": 0.1},
        ]
        
        for config in weight_configs:
            name = config.pop("name")
            scores = engineer.compute_all_scores(config)
            
            # Top 5
            top_indices = np.argsort(scores)[-5:][::-1]
            
            print(f"\n📈 Estratégia: {name}")
            print(f"   Pesos: wf={config['wf']:.2f}, wa={config['wa']:.2f}, wr={config['wr']:.2f}")
            print("   Top 5 números:")
            for i, idx in enumerate(top_indices, 1):
                num = idx + 1
                score = scores[idx]
                print(f"      {i}. Número {num:2d}: score {score:.4f}")


def demo_cache():
    """Demonstra uso do cache"""
    print_section("SISTEMA DE CACHE")
    
    cache = FeatureCache()
    
    # Estatísticas
    stats = cache.get_cache_stats()
    print(f"\n📦 Estatísticas do cache:")
    print(f"   Total de chaves: {stats['total_keys']}")
    print(f"   Por tipo:")
    for ftype, count in stats['by_type'].items():
        print(f"      {ftype}: {count} chaves")
    
    # Testa cache
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        # Cacheia features
        print("\n💾 Cacheando features...")
        features_dict = engineer.to_dict()
        success = cache.set_all_features(features_dict)
        
        if success:
            print("   ✓ Features cacheadas com sucesso")
            
            # Recupera do cache
            print("\n📥 Recuperando do cache...")
            cached = cache.get_all_features()
            
            cached_count = sum(1 for v in cached.values() if v is not None)
            print(f"   ✓ {cached_count} tipos de features recuperadas")
        else:
            print("   ✗ Erro ao cachear features")


def main():
    """Executa todas as demonstrações"""
    print("\n" + "🎲" * 30)
    print("  DEMONSTRAÇÃO - FEATURE ENGINEERING")
    print("  Lotofácil Optimizer")
    print("🎲" * 30)
    
    try:
        demo_frequencies()
        demo_delays()
        demo_repetitions()
        demo_affinity()
        demo_scores()
        demo_cache()
        
        print("\n" + "=" * 60)
        print("  ✅ Demonstração concluída com sucesso!")
        print("=" * 60)
        print("\n💡 Dica: Acesse http://localhost:8000/docs para testar a API")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
