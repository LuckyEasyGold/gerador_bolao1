#!/usr/bin/env python3
"""
Script de demonstração do Motor de Geração de Jogos
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db
from backend.database.repositories.contest_repository import ContestRepository
from backend.core.feature_engineering import FeatureEngineer
from backend.core.game_generator import TicketGenerator, GameGenerator
from backend.models.dna import DNA, DNAGene
import numpy as np


def print_section(title: str):
    """Imprime seção formatada"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_single_game():
    """Demonstra geração de jogo individual"""
    print_section("GERAÇÃO DE JOGO INDIVIDUAL")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            print("❌ Nenhum concurso encontrado.")
            return
        
        # Calcula features
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        # DNA balanceado
        dna = DNA(genes=DNAGene(
            w15=0.4, w16=0.3, w17=0.3,
            wf=0.4, wa=0.3, wr=0.3, wc_aff=1.0,
            T_base=1.0, kappa=0.3,
            wp=0.3, wl=0.3, ws=0.2, wo=0.2,
            wcov=0.4, wd=0.4, woverlap=0.2,
            pool_size=20, candidates_per_game=50, refine_iterations=100
        ))
        
        # Gera jogo
        generator = GameGenerator(engineer, dna, seed=42)
        game = generator.generate_game(size=15)
        
        print(f"\n🎲 Jogo gerado (15 números):")
        print(f"   Números: {game.numbers}")
        print(f"   Custo: R$ {game.cost:.2f}")
        print(f"   Score estrutural: {game.score:.4f}")
        
        # Análise do jogo
        pares = sum(1 for n in game.numbers if n % 2 == 0)
        impares = len(game.numbers) - pares
        
        print(f"\n📊 Análise:")
        print(f"   Pares: {pares}")
        print(f"   Ímpares: {impares}")
        
        # Distribuição por linha
        lines = [0] * 5
        for num in game.numbers:
            line = (num - 1) // 5
            lines[line] += 1
        
        print(f"   Distribuição por linha:")
        for i, count in enumerate(lines, 1):
            print(f"      Linha {i}: {count} números")


def demo_ticket_generation():
    """Demonstra geração de bolão completo"""
    print_section("GERAÇÃO DE BOLÃO COMPLETO")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        # Calcula features
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        # DNA balanceado
        dna = DNA(genes=DNAGene(
            w15=0.4, w16=0.3, w17=0.3,
            wf=0.4, wa=0.3, wr=0.3, wc_aff=1.0,
            T_base=1.0, kappa=0.3,
            wp=0.3, wl=0.3, ws=0.2, wo=0.2,
            wcov=0.4, wd=0.4, woverlap=0.2,
            pool_size=20, candidates_per_game=50, refine_iterations=100
        ))
        
        # Gera bolão
        budget = 100.0
        generator = TicketGenerator(engineer, dna, seed=42)
        ticket = generator.generate_ticket(budget=budget)
        
        print(f"\n💰 Orçamento: R$ {budget:.2f}")
        print(f"💵 Custo total: R$ {ticket.total_cost:.2f}")
        print(f"🎫 Total de jogos: {ticket.total_games}")
        print(f"📊 Score de diversidade: {ticket.diversity_score:.4f}")
        print(f"🎯 Score de cobertura: {ticket.coverage_score:.4f}")
        
        # Distribuição por tamanho
        by_size = {}
        for game in ticket.games:
            by_size[game.size] = by_size.get(game.size, 0) + 1
        
        print(f"\n📋 Distribuição por tamanho:")
        for size in sorted(by_size.keys()):
            count = by_size[size]
            total_cost = count * (3.0 if size == 15 else 48.0 if size == 16 else 408.0)
            print(f"   {size} números: {count} jogos (R$ {total_cost:.2f})")
        
        # Mostra primeiros 3 jogos
        print(f"\n🎲 Primeiros 3 jogos:")
        for i, game in enumerate(ticket.games[:3], 1):
            print(f"   {i}. {game.numbers} (score: {game.score:.4f})")
        
        # Cobertura de números
        all_numbers = set()
        for game in ticket.games:
            all_numbers.update(game.numbers)
        
        print(f"\n🎯 Cobertura:")
        print(f"   Números únicos cobertos: {len(all_numbers)}/25")
        print(f"   Números: {sorted(all_numbers)}")


def demo_different_strategies():
    """Demonstra diferentes estratégias de geração"""
    print_section("DIFERENTES ESTRATÉGIAS")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        strategies = [
            {
                "name": "Conservadora (foco em frequência)",
                "dna": DNAGene(
                    w15=0.5, w16=0.3, w17=0.2,
                    wf=0.7, wa=0.2, wr=0.1, wc_aff=0.5,
                    T_base=0.5, kappa=0.2,
                    wp=0.3, wl=0.3, ws=0.2, wo=0.2,
                    wcov=0.4, wd=0.4, woverlap=0.2,
                    pool_size=18, candidates_per_game=100, refine_iterations=200
                )
            },
            {
                "name": "Agressiva (foco em atraso)",
                "dna": DNAGene(
                    w15=0.3, w16=0.3, w17=0.4,
                    wf=0.1, wa=0.8, wr=0.1, wc_aff=1.5,
                    T_base=2.0, kappa=0.5,
                    wp=0.3, wl=0.3, ws=0.2, wo=0.2,
                    wcov=0.5, wd=0.5, woverlap=0.0,
                    pool_size=22, candidates_per_game=50, refine_iterations=100
                )
            },
            {
                "name": "Balanceada",
                "dna": DNAGene(
                    w15=0.4, w16=0.3, w17=0.3,
                    wf=0.4, wa=0.3, wr=0.3, wc_aff=1.0,
                    T_base=1.0, kappa=0.3,
                    wp=0.3, wl=0.3, ws=0.2, wo=0.2,
                    wcov=0.4, wd=0.4, woverlap=0.2,
                    pool_size=20, candidates_per_game=50, refine_iterations=100
                )
            }
        ]
        
        budget = 50.0
        
        for strategy in strategies:
            print(f"\n📈 Estratégia: {strategy['name']}")
            
            dna = DNA(genes=strategy['dna'])
            generator = TicketGenerator(engineer, dna, seed=42)
            ticket = generator.generate_ticket(budget=budget)
            
            print(f"   Jogos: {ticket.total_games}")
            print(f"   Custo: R$ {ticket.total_cost:.2f}")
            print(f"   Diversidade: {ticket.diversity_score:.4f}")
            print(f"   Cobertura: {ticket.coverage_score:.4f}")
            
            # Primeiro jogo
            if ticket.games:
                first_game = ticket.games[0]
                print(f"   Exemplo: {first_game.numbers[:10]}...")


def demo_reproducibility():
    """Demonstra reprodutibilidade com seeds"""
    print_section("REPRODUTIBILIDADE")
    
    with get_db() as db:
        repo = ContestRepository(db)
        contests = repo.get_all(limit=100)
        
        if not contests:
            return
        
        engineer = FeatureEngineer()
        engineer.fit(contests)
        
        dna = DNA(genes=DNAGene.random(np.random.default_rng(42)))
        
        # Gera com mesma seed
        gen1 = TicketGenerator(engineer, dna, seed=42)
        gen2 = TicketGenerator(engineer, dna, seed=42)
        
        ticket1 = gen1.generate_ticket(budget=50.0)
        ticket2 = gen2.generate_ticket(budget=50.0)
        
        print(f"\n🔄 Geração 1:")
        print(f"   Jogos: {ticket1.total_games}")
        print(f"   Primeiro jogo: {ticket1.games[0].numbers}")
        
        print(f"\n🔄 Geração 2 (mesma seed):")
        print(f"   Jogos: {ticket2.total_games}")
        print(f"   Primeiro jogo: {ticket2.games[0].numbers}")
        
        identical = ticket1.games[0].numbers == ticket2.games[0].numbers
        print(f"\n✓ Resultados idênticos: {identical}")
        
        # Gera com seed diferente
        gen3 = TicketGenerator(engineer, dna, seed=123)
        ticket3 = gen3.generate_ticket(budget=50.0)
        
        print(f"\n🔄 Geração 3 (seed diferente):")
        print(f"   Jogos: {ticket3.total_games}")
        print(f"   Primeiro jogo: {ticket3.games[0].numbers}")
        
        different = ticket1.games[0].numbers != ticket3.games[0].numbers
        print(f"\n✓ Resultados diferentes: {different}")


def main():
    """Executa todas as demonstrações"""
    print("\n" + "🎲" * 30)
    print("  DEMONSTRAÇÃO - MOTOR DE GERAÇÃO")
    print("  Lotofácil Optimizer")
    print("🎲" * 30)
    
    try:
        demo_single_game()
        demo_ticket_generation()
        demo_different_strategies()
        demo_reproducibility()
        
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
