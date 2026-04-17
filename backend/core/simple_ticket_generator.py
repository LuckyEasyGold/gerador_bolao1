"""
Gerador Simples de Bolões
Usa pool ótimo para gerar bolões com distribuição de orçamento
"""
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass

from backend.config import get_settings

settings = get_settings()


@dataclass
class SimpleBolao:
    """Resultado simples de geração de bolão"""
    j15: int  # Quantidade de jogos com 15 números
    j16: int  # Quantidade de jogos com 16 números
    j17: int  # Quantidade de jogos com 17 números
    
    custo_total: float
    valor_por_cota: float
    total_cotas: int
    total_jogos: int
    
    pool_usado: List[int]
    
    def to_dict(self) -> Dict:
        return {
            "j15": self.j15,
            "j16": self.j16,
            "j17": self.j17,
            "custo_total": float(self.custo_total),
            "valor_por_cota": float(self.valor_por_cota),
            "total_cotas": self.total_cotas,
            "total_jogos": self.total_jogos,
            "pool_usado": self.pool_usado
        }


def calcular_distribuicao_orcamento(
    valor_total: float,
    valor_unitario: float,
    pool: Optional[List[int]] = None,
    seed: Optional[int] = None
) -> SimpleBolao:
    """
    Calcula melhor distribuição de j15, j16, j17 baseado no orçamento
    
    ENTRADA:
    - valor_total_do_bolao: Total a investir (ex: R$ 1000)
    - valor_unitario_do_bolao: Valor por cota (ex: R$ 200)
    - pool: Lista de números ótimos para usar (1-25)
    
    SAÍDA:
    - j15: quantidade de jogos 15 números
    - j16: quantidade de jogos 16 números
    - j17: quantidade de jogos 17 números
    
    Args:
        valor_total: Valor total a investir
        valor_unitario: Valor por cota (para informação)
        pool: Pool ótimo de números (usa todos 1-25 se None)
        seed: Seed para reprodutibilidade
    
    Returns:
        SimpleBolao com distribuição
    """
    rng = np.random.default_rng(seed)
    
    # Pool padrão se não fornecido
    if pool is None:
        pool = list(range(1, 26))
    
    # Custos
    cost_15 = settings.cost_15  # R$ 10
    cost_16 = settings.cost_16  # R$ 20
    cost_17 = settings.cost_17  # R$ 30
    
    # Estratégia: distribuir proporcionalmente
    # Dar mais peso a j15 (mais barato), menos a j17
    
    # Proporção ideal: 40% j15, 35% j16, 25% j17
    # Mas vai variar com o valor disponível
    
    if valor_total < cost_15:
        # Orçamento insuficiente
        return SimpleBolao(
            j15=0, j16=0, j17=0,
            custo_total=0,
            valor_por_cota=valor_unitario,
            total_cotas=0,
            total_jogos=0,
            pool_usado=pool
        )
    
    # Distribuição proporcional
    # Quanto mais dinheiro, mais diversidade
    if valor_total <= cost_15 * 5:
        # Muito pouco: só j15
        count_15 = int(valor_total / cost_15)
        count_16 = 0
        count_17 = 0
    
    elif valor_total <= cost_15 * 10:
        # Pouco: principalmente j15 com alguns j16
        count_15 = int(valor_total * 0.7 / cost_15)
        remaining = valor_total - (count_15 * cost_15)
        count_16 = int(remaining / cost_16)
        count_17 = 0
    
    elif valor_total <= cost_15 * 50:
        # Médio: mistura os 3
        budget_15 = valor_total * 0.4
        budget_16 = valor_total * 0.35
        budget_17 = valor_total * 0.25
        
        count_15 = int(budget_15 / cost_15)
        count_16 = int(budget_16 / cost_16)
        count_17 = int(budget_17 / cost_17)
    
    else:
        # Grande: equilibrado
        budget_15 = valor_total * 0.35
        budget_16 = valor_total * 0.35
        budget_17 = valor_total * 0.30
        
        count_15 = int(budget_15 / cost_15)
        count_16 = int(budget_16 / cost_16)
        count_17 = int(budget_17 / cost_17)
    
    # Ajusta para usar todo (ou máximo) do orçamento
    custo_atual = count_15 * cost_15 + count_16 * cost_16 + count_17 * cost_17
    resta = valor_total - custo_atual
    
    # Adiciona jogos de 15 com o restante (mais barato)
    if resta >= cost_15:
        count_15 += int(resta / cost_15)
    elif resta >= cost_16:
        count_16 += int(resta / cost_16)
    
    # Recalcula custo total
    custo_total = count_15 * cost_15 + count_16 * cost_16 + count_17 * cost_17
    
    # Calcula cotas
    total_cotas = int(valor_total / valor_unitario) if valor_unitario > 0 else 1
    
    total_jogos = count_15 + count_16 + count_17
    
    return SimpleBolao(
        j15=count_15,
        j16=count_16,
        j17=count_17,
        custo_total=float(custo_total),
        valor_por_cota=float(valor_unitario),
        total_cotas=total_cotas,
        total_jogos=total_jogos,
        pool_usado=pool
    )
