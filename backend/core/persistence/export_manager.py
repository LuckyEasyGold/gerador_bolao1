"""
ExportManager - Gerenciamento de Exportações
Exporta bolões, experimentos e DNAs em múltiplos formatos
"""
import json
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from io import StringIO, BytesIO

from backend.models.dna import DNA
from backend.core.game_generator import Ticket


class ExportManager:
    """
    Gerencia exportação de dados
    
    Suporta múltiplos formatos:
    - JSON (estruturado)
    - CSV (planilha)
    - TXT (simples)
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: Diretório base para exportações
        """
        self.base_path = Path(base_path or "data/exports")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def export_ticket(self,
                     ticket: Ticket,
                     format: str = "json",
                     include_metadata: bool = True) -> bytes:
        """
        Exporta bolão
        
        Args:
            ticket: Bolão a exportar
            format: Formato (json, csv, txt)
            include_metadata: Incluir metadados
        
        Returns:
            Bytes do arquivo exportado
        """
        if format == "json":
            return self._export_ticket_json(ticket, include_metadata)
        elif format == "csv":
            return self._export_ticket_csv(ticket, include_metadata)
        elif format == "txt":
            return self._export_ticket_txt(ticket, include_metadata)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def export_experiment(self,
                         experiment_data: Dict[str, Any],
                         format: str = "json") -> bytes:
        """
        Exporta experimento completo
        
        Args:
            experiment_data: Dados do experimento
            format: Formato (json, csv)
        
        Returns:
            Bytes do arquivo exportado
        """
        if format == "json":
            return self._export_experiment_json(experiment_data)
        elif format == "csv":
            return self._export_experiment_csv(experiment_data)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def export_dna(self,
                  dna: DNA,
                  format: str = "json") -> bytes:
        """
        Exporta DNA
        
        Args:
            dna: DNA a exportar
            format: Formato (json, csv, txt)
        
        Returns:
            Bytes do arquivo exportado
        """
        if format == "json":
            return self._export_dna_json(dna)
        elif format == "csv":
            return self._export_dna_csv(dna)
        elif format == "txt":
            return self._export_dna_txt(dna)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def save_export(self,
                   data: bytes,
                   filename: str,
                   experiment_id: Optional[str] = None) -> str:
        """
        Salva exportação em arquivo
        
        Args:
            data: Dados a salvar
            filename: Nome do arquivo
            experiment_id: ID do experimento (opcional)
        
        Returns:
            Caminho do arquivo salvo
        """
        if experiment_id:
            exp_dir = self.base_path / experiment_id
            exp_dir.mkdir(exist_ok=True)
            file_path = exp_dir / filename
        else:
            file_path = self.base_path / filename
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return str(file_path)
    
    def validate_export(self,
                       exported_data: bytes,
                       format: str) -> bool:
        """
        Valida exportação
        
        Args:
            exported_data: Dados exportados
            format: Formato esperado
        
        Returns:
            True se válido
        """
        try:
            if format == "json":
                json.loads(exported_data.decode('utf-8'))
                return True
            elif format == "csv":
                # Tenta ler como CSV
                csv.reader(StringIO(exported_data.decode('utf-8')))
                return True
            elif format == "txt":
                # Tenta decodificar
                exported_data.decode('utf-8')
                return True
            else:
                return False
        except Exception:
            return False
    
    # Métodos privados de exportação
    
    def _export_ticket_json(self,
                           ticket: Ticket,
                           include_metadata: bool) -> bytes:
        """Exporta bolão em JSON"""
        data = {
            "games": [game.numbers for game in ticket.games],
            "total_games": len(ticket.games),
            "total_cost": ticket.total_cost
        }
        
        if include_metadata:
            data["metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "format": "json",
                "version": "1.0"
            }
            
            if ticket.dna:
                data["dna"] = ticket.dna.genes.to_dict()
        
        return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    
    def _export_ticket_csv(self,
                          ticket: Ticket,
                          include_metadata: bool) -> bytes:
        """Exporta bolão em CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        if include_metadata:
            writer.writerow(["# Bolão Lotofácil"])
            writer.writerow(["# Total de jogos:", len(ticket.games)])
            writer.writerow(["# Custo total:", f"R$ {ticket.total_cost:.2f}"])
            writer.writerow(["# Exportado em:", datetime.now().isoformat()])
            writer.writerow([])
        
        # Cabeçalho dos jogos
        max_numbers = max(len(game.numbers) for game in ticket.games)
        header = ["Jogo"] + [f"N{i+1}" for i in range(max_numbers)]
        writer.writerow(header)
        
        # Jogos
        for i, game in enumerate(ticket.games, 1):
            row = [f"Jogo {i}"] + sorted(game.numbers)
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    def _export_ticket_txt(self,
                          ticket: Ticket,
                          include_metadata: bool) -> bytes:
        """Exporta bolão em TXT"""
        lines = []
        
        if include_metadata:
            lines.append("=" * 50)
            lines.append("BOLÃO LOTOFÁCIL")
            lines.append("=" * 50)
            lines.append(f"Total de jogos: {len(ticket.games)}")
            lines.append(f"Custo total: R$ {ticket.total_cost:.2f}")
            lines.append(f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            lines.append("=" * 50)
            lines.append("")
        
        # Jogos
        for i, game in enumerate(ticket.games, 1):
            numbers = " - ".join(f"{n:02d}" for n in sorted(game.numbers))
            lines.append(f"Jogo {i:3d}: {numbers}")
        
        if include_metadata:
            lines.append("")
            lines.append("=" * 50)
            lines.append(f"Boa sorte!")
            lines.append("=" * 50)
        
        return "\n".join(lines).encode('utf-8')
    
    def _export_experiment_json(self, experiment_data: Dict[str, Any]) -> bytes:
        """Exporta experimento em JSON"""
        data = {
            "experiment": experiment_data,
            "exported_at": datetime.now().isoformat(),
            "format": "json",
            "version": "1.0"
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    
    def _export_experiment_csv(self, experiment_data: Dict[str, Any]) -> bytes:
        """Exporta experimento em CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(["# Experimento Lotofácil"])
        writer.writerow(["# ID:", experiment_data.get("id", "N/A")])
        writer.writerow(["# Nome:", experiment_data.get("name", "N/A")])
        writer.writerow([])
        
        # Configuração
        writer.writerow(["Configuração"])
        config = experiment_data.get("config", {})
        for key, value in config.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # Resultado
        writer.writerow(["Resultado"])
        result = experiment_data.get("result", {})
        writer.writerow(["Melhor Fitness", result.get("best_fitness", "N/A")])
        writer.writerow(["Melhor ROI", result.get("best_roi", "N/A")])
        writer.writerow(["Gerações", result.get("generations_run", "N/A")])
        writer.writerow(["Tempo Total (s)", result.get("total_time", "N/A")])
        
        return output.getvalue().encode('utf-8')
    
    def _export_dna_json(self, dna: DNA) -> bytes:
        """Exporta DNA em JSON"""
        data = {
            "dna": dna.genes.to_dict(),
            "fitness": dna.fitness,
            "roi": dna.roi,
            "risk": dna.risk,
            "generation": dna.generation,
            "exported_at": datetime.now().isoformat()
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    
    def _export_dna_csv(self, dna: DNA) -> bytes:
        """Exporta DNA em CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(["Gene", "Valor"])
        
        # Genes
        for gene, value in dna.genes.to_dict().items():
            writer.writerow([gene, value])
        
        # Métricas
        writer.writerow([])
        writer.writerow(["Métrica", "Valor"])
        writer.writerow(["Fitness", dna.fitness])
        writer.writerow(["ROI", dna.roi])
        writer.writerow(["Risco", dna.risk])
        writer.writerow(["Geração", dna.generation])
        
        return output.getvalue().encode('utf-8')
    
    def _export_dna_txt(self, dna: DNA) -> bytes:
        """Exporta DNA em TXT"""
        lines = []
        
        lines.append("=" * 50)
        lines.append("DNA EVOLUTIVO")
        lines.append("=" * 50)
        lines.append("")
        
        # Genes
        lines.append("GENES:")
        for gene, value in dna.genes.to_dict().items():
            lines.append(f"  {gene:20s}: {value:8.4f}")
        
        lines.append("")
        
        # Métricas
        lines.append("MÉTRICAS:")
        lines.append(f"  {'Fitness':20s}: {dna.fitness:8.4f}")
        lines.append(f"  {'ROI':20s}: {dna.roi:8.4f}")
        lines.append(f"  {'Risco':20s}: {dna.risk:8.4f}")
        lines.append(f"  {'Geração':20s}: {dna.generation}")
        
        lines.append("")
        lines.append("=" * 50)
        
        return "\n".join(lines).encode('utf-8')
