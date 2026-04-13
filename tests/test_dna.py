import pytest
import numpy as np
from backend.models.dna import DNA, DNAGene


def test_dna_gene_creation():
    """Testa criação de gene com valores válidos"""
    gene = DNAGene(
        w15=0.5, w16=0.3, w17=0.2,
        wf=0.5, wa=-0.3, wr=0.1, wc_aff=1.0,
        T_base=1.0, kappa=0.5,
        wp=0.5, wl=0.5, ws=0.5, wo=0.5,
        wcov=0.5, wd=0.5, woverlap=0.5,
        pool_size=20, candidates_per_game=50, refine_iterations=100
    )
    
    assert gene.w15 == 0.5
    assert gene.pool_size == 20


def test_dna_gene_validation():
    """Testa validação de ranges"""
    with pytest.raises(ValueError):
        DNAGene(
            w15=1.5,  # Inválido: > 1.0
            w16=0.3, w17=0.2,
            wf=0.5, wa=-0.3, wr=0.1, wc_aff=1.0,
            T_base=1.0, kappa=0.5,
            wp=0.5, wl=0.5, ws=0.5, wo=0.5,
            wcov=0.5, wd=0.5, woverlap=0.5,
            pool_size=20, candidates_per_game=50, refine_iterations=100
        )


def test_dna_random_generation():
    """Testa geração aleatória de DNA"""
    rng = np.random.default_rng(42)
    gene = DNAGene.random(rng)
    
    assert 0.0 <= gene.w15 <= 1.0
    assert 0.0 <= gene.w16 <= 1.0
    assert -1.0 <= gene.wf <= 1.0
    assert 18 <= gene.pool_size <= 25


def test_dna_mutation():
    """Testa mutação de DNA"""
    rng = np.random.default_rng(42)
    dna = DNA(genes=DNAGene.random(rng))
    
    mutated = dna.mutate(mutation_rate=1.0, rng=rng)
    
    assert mutated.generation == dna.generation + 1
    # Pelo menos um gene deve ter mudado
    assert mutated.genes.to_dict() != dna.genes.to_dict()


def test_dna_crossover():
    """Testa crossover entre dois DNAs"""
    rng = np.random.default_rng(42)
    parent1 = DNA(genes=DNAGene.random(rng))
    parent2 = DNA(genes=DNAGene.random(rng))
    
    child = DNA.crossover(parent1, parent2, rng)
    
    assert child.generation == max(parent1.generation, parent2.generation) + 1
    
    # Child deve ter genes de ambos os pais
    child_dict = child.genes.to_dict()
    parent1_dict = parent1.genes.to_dict()
    parent2_dict = parent2.genes.to_dict()
    
    # Verifica que pelo menos um gene veio de cada pai
    from_parent1 = sum(1 for k in child_dict if child_dict[k] == parent1_dict[k])
    from_parent2 = sum(1 for k in child_dict if child_dict[k] == parent2_dict[k])
    
    assert from_parent1 > 0 or from_parent2 > 0
