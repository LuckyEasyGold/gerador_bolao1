#!/usr/bin/env python3
"""
Demo: Sistema de Persistência
Demonstra checkpoints, seeds, logs, replay e exportação
"""
import sys
from pathlib import Path

# Adiciona backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import SessionLocal
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.genetic_algorithm import GeneticAlgorithm, GenerationStats
from backend.core.persistence import (
    CheckpointManager,
    SeedManager,
    ExperimentLogger,
    ReplayEngine,
    ExportManager
)
from backend.models.experiment import ExperimentConfig


def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_checkpoints():
    """Demonstra sistema de checkpoints"""
    print_header("DEMO 1: Checkpoints")
    
    print("\n1. Criando CheckpointManager...")
    manager = CheckpointManager(base_path="data/demo/checkpoints")
    print("✓ CheckpointManager criado")
    
    print("\n2. Simulando salvamento de checkpoints...")
    experiment_id = "demo_exp_001"
    
    # Simula 3 gerações
    from backend.core.genetic_algorithm import Population
    
    for gen in range(1, 4):
        pop = Population(size=5, seed=42)
        pop.initialize_random()
        
        stats = GenerationStats(
            generation=gen,
            best_fitness=1.0 + gen * 0.5,
            avg_fitness=1.0,
            worst_fitness=0.5,
            std_fitness=0.3,
            best_roi=0.1 + gen * 0.05,
            avg_roi=0.1,
            diversity=5.0,
            elapsed_time=10.0
        )
        
        checkpoint_id = manager.save_checkpoint(
            experiment_id=experiment_id,
            generation=gen,
            population=pop,
            stats=stats,
            config={"population_size": 5, "generations": 10},
            seeds={"master": 42}
        )
        
        print(f"   Geração {gen}: checkpoint {checkpoint_id[:8]}... salvo")
    
    print("\n3. Listando checkpoints...")
    checkpoints = manager.list_checkpoints(experiment_id)
    print(f"   Total: {len(checkpoints)} checkpoints")
    
    for cp in checkpoints:
        print(f"   - Geração {cp.generation}: {cp.file_size / 1024:.2f} KB")
    
    print("\n4. Carregando checkpoint mais recente...")
    latest = manager.get_latest_checkpoint(experiment_id)
    print(f"   ✓ Geração {latest.generation} carregada")
    print(f"   ✓ Melhor fitness: {latest.stats.best_fitness:.4f}")
    print(f"   ✓ População: {len(latest.population.individuals)} indivíduos")
    
    print("\n5. Estatísticas de armazenamento...")
    stats = manager.get_storage_stats()
    print(f"   Total de experimentos: {stats['total_experiments']}")
    print(f"   Total de checkpoints: {stats['total_checkpoints']}")
    print(f"   Espaço usado: {stats['total_size_mb']:.2f} MB")


def demo_seeds():
    """Demonstra gerenciamento de seeds"""
    print_header("DEMO 2: Gerenciamento de Seeds")
    
    print("\n1. Criando SeedManager...")
    manager = SeedManager(base_path="data/demo/seeds")
    print("✓ SeedManager criado")
    
    print("\n2. Gerando chain de seeds...")
    master_seed = 42
    seeds = manager.generate_seed_chain(master_seed)
    
    print(f"   Master seed: {master_seed}")
    for component, seed in seeds.items():
        if component != "master":
            print(f"   {component:20s}: {seed}")
    
    print("\n3. Registrando seeds para experimento...")
    experiment_id = "demo_exp_002"
    manager.register_seed_chain(experiment_id, master_seed)
    print(f"   ✓ Seeds registradas para {experiment_id}")
    
    print("\n4. Validando seeds...")
    is_valid = manager.validate_seeds(experiment_id)
    print(f"   Válido: {'✓ Sim' if is_valid else '✗ Não'}")
    
    print("\n5. Hash das seeds...")
    seed_hash = manager.get_seed_hash(experiment_id)
    print(f"   Hash: {seed_hash[:16]}...")
    
    print("\n6. Comparando com outro experimento...")
    experiment_id2 = "demo_exp_003"
    manager.register_seed_chain(experiment_id2, 123)  # Seed diferente
    
    comparison = manager.compare_seeds(experiment_id, experiment_id2)
    matches = sum(1 for v in comparison.values() if v)
    print(f"   Componentes iguais: {matches}/{len(comparison)}")


def demo_logs():
    """Demonstra sistema de logs"""
    print_header("DEMO 3: Sistema de Logs")
    
    print("\n1. Criando ExperimentLogger...")
    logger = ExperimentLogger(base_path="data/demo/logs")
    print("✓ ExperimentLogger criado")
    
    print("\n2. Registrando eventos...")
    experiment_id = "demo_exp_004"
    
    # Início
    logger.log_start(experiment_id, {"population_size": 20, "generations": 50})
    print("   ✓ Início registrado")
    
    # Gerações
    for gen in range(1, 4):
        logger.log_generation(
            experiment_id,
            gen,
            {"best_fitness": 1.0 + gen * 0.5, "avg_fitness": 1.0}
        )
    print("   ✓ 3 gerações registradas")
    
    # Convergência
    logger.log_convergence(experiment_id, 3, "Threshold atingido")
    print("   ✓ Convergência registrada")
    
    # Conclusão
    logger.log_completion(experiment_id, {"best_fitness": 2.5, "generations_run": 3})
    print("   ✓ Conclusão registrada")
    
    print("\n3. Consultando logs...")
    logs = logger.get_logs(experiment_id)
    print(f"   Total de logs: {len(logs)}")
    
    print("\n4. Resumo dos logs...")
    summary = logger.get_summary(experiment_id)
    print(f"   Total: {summary['total_logs']}")
    print(f"   Erros: {summary['errors']}")
    print(f"   Por tipo:")
    for log_type, count in summary['by_type'].items():
        print(f"     {log_type:20s}: {count}")


def demo_export():
    """Demonstra exportação"""
    print_header("DEMO 4: Exportação")
    
    print("\n1. Criando ExportManager...")
    manager = ExportManager(base_path="data/demo/exports")
    print("✓ ExportManager criado")
    
    print("\n2. Criando DNA de exemplo...")
    from backend.models.dna import DNA, DNAGene
    import numpy as np
    
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    dna.fitness = 1.5
    dna.roi = 0.25
    dna.risk = 0.1
    print("✓ DNA criado")
    
    print("\n3. Exportando DNA em múltiplos formatos...")
    
    # JSON
    json_data = manager.export_dna(dna, format="json")
    print(f"   JSON: {len(json_data)} bytes")
    
    # CSV
    csv_data = manager.export_dna(dna, format="csv")
    print(f"   CSV:  {len(csv_data)} bytes")
    
    # TXT
    txt_data = manager.export_dna(dna, format="txt")
    print(f"   TXT:  {len(txt_data)} bytes")
    
    print("\n4. Validando exportações...")
    json_valid = manager.validate_export(json_data, "json")
    csv_valid = manager.validate_export(csv_data, "csv")
    txt_valid = manager.validate_export(txt_data, "txt")
    
    print(f"   JSON: {'✓ Válido' if json_valid else '✗ Inválido'}")
    print(f"   CSV:  {'✓ Válido' if csv_valid else '✗ Inválido'}")
    print(f"   TXT:  {'✓ Válido' if txt_valid else '✗ Inválido'}")
    
    print("\n5. Salvando exportações...")
    json_path = manager.save_export(json_data, "dna.json", "demo_exp_005")
    csv_path = manager.save_export(csv_data, "dna.csv", "demo_exp_005")
    txt_path = manager.save_export(txt_data, "dna.txt", "demo_exp_005")
    
    print(f"   ✓ JSON salvo em: {json_path}")
    print(f"   ✓ CSV salvo em: {csv_path}")
    print(f"   ✓ TXT salvo em: {txt_path}")


def demo_integration():
    """Demonstra integração completa"""
    print_header("DEMO 5: Integração Completa")
    
    print("\n1. Preparando componentes...")
    checkpoint_mgr = CheckpointManager(base_path="data/demo/checkpoints")
    seed_mgr = SeedManager(base_path="data/demo/seeds")
    logger = ExperimentLogger(base_path="data/demo/logs")
    
    experiment_id = "demo_exp_integration"
    master_seed = 42
    
    print("\n2. Registrando seeds...")
    seeds = seed_mgr.register_seed_chain(experiment_id, master_seed)
    print(f"   ✓ {len(seeds)} seeds registradas")
    
    print("\n3. Iniciando experimento (log)...")
    config = {"population_size": 5, "generations": 3}
    logger.log_start(experiment_id, config)
    print("   ✓ Início registrado")
    
    print("\n4. Simulando evolução com checkpoints...")
    from backend.core.genetic_algorithm import Population
    
    for gen in range(1, 4):
        # População
        pop = Population(size=5, seed=seeds["population"])
        pop.initialize_random()
        
        # Stats
        stats = GenerationStats(
            generation=gen,
            best_fitness=1.0 + gen * 0.5,
            avg_fitness=1.0,
            worst_fitness=0.5,
            std_fitness=0.3,
            best_roi=0.1 + gen * 0.05,
            avg_roi=0.1,
            diversity=5.0,
            elapsed_time=10.0
        )
        
        # Checkpoint
        checkpoint_id = checkpoint_mgr.save_checkpoint(
            experiment_id=experiment_id,
            generation=gen,
            population=pop,
            stats=stats,
            config=config,
            seeds=seeds
        )
        
        # Log
        logger.log_generation(experiment_id, gen, stats.to_dict())
        logger.log_checkpoint(experiment_id, checkpoint_id, gen)
        
        print(f"   Geração {gen}: checkpoint e log salvos")
    
    print("\n5. Finalizando experimento...")
    logger.log_completion(experiment_id, {"best_fitness": 2.5})
    print("   ✓ Conclusão registrada")
    
    print("\n6. Resumo final...")
    checkpoints = checkpoint_mgr.list_checkpoints(experiment_id)
    log_summary = logger.get_summary(experiment_id)
    seed_hash = seed_mgr.get_seed_hash(experiment_id)
    
    print(f"   Checkpoints: {len(checkpoints)}")
    print(f"   Logs: {log_summary['total_logs']}")
    print(f"   Seed hash: {seed_hash[:16]}...")
    print(f"   ✓ Experimento completo e auditável!")


def main():
    """Executa todas as demos"""
    print("\n" + "=" * 70)
    print("  DEMONSTRAÇÃO: SISTEMA DE PERSISTÊNCIA")
    print("=" * 70)
    print("\n  Este script demonstra o sistema completo de persistência:")
    print("  - Checkpoints (salvar/carregar estado)")
    print("  - Seeds (reprodutibilidade)")
    print("  - Logs (auditoria)")
    print("  - Exportação (múltiplos formatos)")
    print("  - Integração completa")
    
    input("\n  Pressione ENTER para continuar...")
    
    try:
        # Executa demos
        demo_checkpoints()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_seeds()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_logs()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_export()
        input("\n  Pressione ENTER para próxima demo...")
        
        demo_integration()
        
        # Finalização
        print_header("DEMONSTRAÇÃO CONCLUÍDA")
        print("\n  ✓ Todas as demos executadas com sucesso!")
        print("\n  Arquivos criados em:")
        print("  - data/demo/checkpoints/")
        print("  - data/demo/seeds/")
        print("  - data/demo/logs/")
        print("  - data/demo/exports/")
        print("\n  Próximos passos:")
        print("  1. Testar API: python -m backend.main")
        print("  2. Executar testes: pytest tests/test_checkpoint_manager.py")
        print("  3. Explorar endpoints: http://localhost:8000/docs")
        
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
