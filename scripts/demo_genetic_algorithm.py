#!/usr/bin/env python3
"""
Demo: Algoritmo Genético para Lotofácil
Demonstra evolução de estratégias de bolões
"""
import sys
from pathlib import Path

# Adiciona backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import SessionLocal
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.genetic_algorithm import GeneticAlgorithm, MultiObjectiveGA
from backend.models.experiment import ExperimentConfig


def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_evolution():
    """Demonstra evolução básica"""
    print_header("DEMO 1: Evolução Básica")
    
    # Carrega dados
    print("\n1. Carregando dados históricos...")
    db = SessionLocal()
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        print("❌ Nenhum concurso encontrado. Execute import_historical_data.py primeiro.")
        return
    
    print(f"✓ {len(contests)} concursos carregados")
    
    # Calcula features
    print("\n2. Calculando features...")
    engineer = FeatureEngineer()
    engineer.fit(contests)
    print("✓ Features calculadas")
    
    # Configura GA
    print("\n3. Configurando Algoritmo Genético...")
    config = ExperimentConfig(
        population_size=10,
        generations=5,
        simulations=500
    )
    
    print(f"   População: {config.population_size}")
    print(f"   Gerações: {config.generations}")
    print(f"   Simulações: {config.simulations}")
    
    # Executa evolução
    print("\n4. Executando evolução...")
    print("-" * 70)
    
    ga = GeneticAlgorithm(
        engineer=engineer,
        budget=50.0,
        population_size=config.population_size,
        generations=config.generations,
        simulations=config.simulations,
        seed=42
    )
    
    result = ga.evolve()
    
    # Resultados
    print("-" * 70)
    print("\n5. Resultados:")
    print(f"   Gerações executadas: {result.generations_run}")
    print(f"   Tempo total: {result.total_time:.2f}s")
    print(f"   Melhor fitness: {result.best_fitness:.4f}")
    print(f"   Melhor ROI: {result.best_dna.roi:.4f}")
    print(f"   Risco: {result.best_dna.risk:.4f}")
    
    if result.convergence_generation:
        print(f"   Convergiu na geração: {result.convergence_generation}")
    
    # Evolução por geração
    print("\n6. Evolução por geração:")
    print(f"   {'Gen':<5} {'Melhor':<10} {'Médio':<10} {'ROI':<10} {'Diversidade':<12}")
    print("   " + "-" * 55)
    
    for stats in result.generation_stats:
        print(f"   {stats.generation:<5} "
              f"{stats.best_fitness:<10.4f} "
              f"{stats.avg_fitness:<10.4f} "
              f"{stats.best_roi:<10.4f} "
              f"{stats.diversity:<12.4f}")
    
    db.close()


def demo_multi_objective():
    """Demonstra otimização multi-objetivo"""
    print_header("DEMO 2: Otimização Multi-Objetivo (ROI vs Risco)")
    
    # Carrega dados
    print("\n1. Carregando dados...")
    db = SessionLocal()
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        print("❌ Nenhum concurso encontrado.")
        return
    
    print(f"✓ {len(contests)} concursos carregados")
    
    # Features
    print("\n2. Calculando features...")
    engineer = FeatureEngineer()
    engineer.fit(contests)
    print("✓ Features calculadas")
    
    # GA Multi-Objetivo
    print("\n3. Configurando GA Multi-Objetivo...")
    print("   ROI weight: 0.7")
    print("   Risk weight: 0.3")
    
    print("\n4. Executando evolução...")
    print("-" * 70)
    
    ga = MultiObjectiveGA(
        engineer=engineer,
        budget=50.0,
        population_size=10,
        generations=5,
        simulations=500,
        roi_weight=0.7,
        risk_weight=0.3,
        seed=42
    )
    
    result = ga.evolve()
    
    # Resultados
    print("-" * 70)
    print("\n5. Resultados Multi-Objetivo:")
    print(f"   Melhor fitness: {result.best_fitness:.4f}")
    print(f"   ROI: {result.best_dna.roi:.4f}")
    print(f"   Risco: {result.best_dna.risk:.4f}")
    print(f"   Tempo: {result.total_time:.2f}s")
    
    db.close()


def demo_convergence():
    """Demonstra detecção de convergência"""
    print_header("DEMO 3: Detecção de Convergência")
    
    # Carrega dados
    print("\n1. Preparando dados...")
    db = SessionLocal()
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        print("❌ Nenhum concurso encontrado.")
        return
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    print("✓ Dados preparados")
    
    # GA com convergência agressiva
    print("\n2. Configurando convergência agressiva...")
    print("   Threshold: 0.01")
    print("   Patience: 3 gerações")
    
    print("\n3. Executando...")
    print("-" * 70)
    
    ga = GeneticAlgorithm(
        engineer=engineer,
        budget=50.0,
        population_size=10,
        generations=20,  # Máximo
        simulations=500,
        convergence_threshold=0.01,
        convergence_patience=3,
        seed=42
    )
    
    result = ga.evolve()
    
    # Resultados
    print("-" * 70)
    print("\n4. Análise de Convergência:")
    print(f"   Gerações máximas: 20")
    print(f"   Gerações executadas: {result.generations_run}")
    
    if result.convergence_generation:
        print(f"   ✓ Convergiu na geração: {result.convergence_generation}")
        print(f"   Economia: {20 - result.generations_run} gerações")
    else:
        print("   ✗ Não convergiu (melhoria contínua)")
    
    db.close()


def demo_dna_comparison():
    """Demonstra comparação de DNAs"""
    print_header("DEMO 4: Comparação de Estratégias")
    
    # Carrega dados
    print("\n1. Preparando...")
    db = SessionLocal()
    repo = ContestRepository(db)
    contests = repo.get_all()
    
    if not contests:
        print("❌ Nenhum concurso encontrado.")
        return
    
    engineer = FeatureEngineer()
    engineer.fit(contests)
    
    # Evolui 2 estratégias com seeds diferentes
    print("\n2. Evoluindo 2 estratégias diferentes...")
    
    print("\n   Estratégia A (seed=42):")
    ga_a = GeneticAlgorithm(
        engineer=engineer,
        budget=50.0,
        population_size=8,
        generations=5,
        simulations=500,
        seed=42
    )
    result_a = ga_a.evolve()
    
    print(f"   ✓ Fitness: {result_a.best_fitness:.4f}, ROI: {result_a.best_dna.roi:.4f}")
    
    print("\n   Estratégia B (seed=123):")
    ga_b = GeneticAlgorithm(
        engineer=engineer,
        budget=50.0,
        population_size=8,
        generations=5,
        simulations=500,
        seed=123
    )
    result_b = ga_b.evolve()
    
    print(f"   ✓ Fitness: {result_b.best_fitness:.4f}, ROI: {result_b.best_dna.roi:.4f}")
    
    # Comparação
    print("\n3. Comparação:")
    print(f"   {'Métrica':<20} {'Estratégia A':<15} {'Estratégia B':<15}")
    print("   " + "-" * 50)
    print(f"   {'Fitness':<20} {result_a.best_fitness:<15.4f} {result_b.best_fitness:<15.4f}")
    print(f"   {'ROI':<20} {result_a.best_dna.roi:<15.4f} {result_b.best_dna.roi:<15.4f}")
    print(f"   {'Risco':<20} {result_a.best_dna.risk:<15.4f} {result_b.best_dna.risk:<15.4f}")
    print(f"   {'Tempo (s)':<20} {result_a.total_time:<15.2f} {result_b.total_time:<15.2f}")
    
    # Melhor
    if result_a.best_fitness > result_b.best_fitness:
        print("\n   🏆 Estratégia A é superior")
    else:
        print("\n   🏆 Estratégia B é superior")
    
    db.close()


def main():
    """Executa todas as demos"""
    print("\n" + "=" * 70)
    print("  DEMONSTRAÇÃO: ALGORITMO GENÉTICO LOTOFÁCIL")
    print("=" * 70)
    print("\n  Este script demonstra o funcionamento do algoritmo genético")
    print("  para otimização de estratégias de bolões da Lotofácil.")
    print("\n  Certifique-se de ter:")
    print("  1. PostgreSQL rodando")
    print("  2. Redis rodando")
    print("  3. Dados históricos importados")
    
    input("\n  Pressione ENTER para continuar...")
    
    try:
        # Executa demos
        demo_basic_evolution()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_multi_objective()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_convergence()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_dna_comparison()
        
        # Finalização
        print_header("DEMONSTRAÇÃO CONCLUÍDA")
        print("\n  ✓ Todas as demos executadas com sucesso!")
        print("\n  Próximos passos:")
        print("  1. Testar API: python -m backend.main")
        print("  2. Executar testes: pytest tests/test_genetic_algorithm.py")
        print("  3. Explorar endpoints: http://localhost:8000/docs")
        
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
