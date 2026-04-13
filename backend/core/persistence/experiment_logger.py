"""
ExperimentLogger - Sistema de Logs Estruturados
Registra eventos, métricas e erros de experimentos
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class LogLevel(str, Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogType(str, Enum):
    """Tipos de log"""
    START = "START"
    GENERATION = "GENERATION"
    CONVERGENCE = "CONVERGENCE"
    COMPLETION = "COMPLETION"
    ERROR = "ERROR"
    CHECKPOINT = "CHECKPOINT"
    METRIC = "METRIC"
    EVENT = "EVENT"


@dataclass
class LogEntry:
    """Entrada de log"""
    timestamp: datetime
    experiment_id: str
    level: LogLevel
    log_type: LogType
    message: str
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "experiment_id": self.experiment_id,
            "level": self.level.value,
            "type": self.log_type.value,
            "message": self.message,
            "data": self.data
        }


class ExperimentLogger:
    """
    Logger estruturado para experimentos
    
    Registra todos os eventos importantes de um experimento
    para auditoria e debug.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: Diretório base para logs
        """
        self.base_path = Path(base_path or "data/logs")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def log_start(self,
                 experiment_id: str,
                 config: Dict[str, Any]) -> None:
        """
        Registra início de experimento
        
        Args:
            experiment_id: ID do experimento
            config: Configuração do experimento
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.INFO,
            log_type=LogType.START,
            message="Experimento iniciado",
            data={
                "config": config,
                "start_time": datetime.now().isoformat()
            }
        )
    
    def log_generation(self,
                      experiment_id: str,
                      generation: int,
                      stats: Dict[str, Any]) -> None:
        """
        Registra estatísticas de uma geração
        
        Args:
            experiment_id: ID do experimento
            generation: Número da geração
            stats: Estatísticas da geração
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.INFO,
            log_type=LogType.GENERATION,
            message=f"Geração {generation} concluída",
            data={
                "generation": generation,
                "stats": stats
            }
        )
    
    def log_convergence(self,
                       experiment_id: str,
                       generation: int,
                       reason: str = "Threshold atingido") -> None:
        """
        Registra convergência
        
        Args:
            experiment_id: ID do experimento
            generation: Geração onde convergiu
            reason: Motivo da convergência
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.INFO,
            log_type=LogType.CONVERGENCE,
            message=f"Convergência detectada na geração {generation}",
            data={
                "generation": generation,
                "reason": reason
            }
        )
    
    def log_completion(self,
                      experiment_id: str,
                      result: Dict[str, Any]) -> None:
        """
        Registra conclusão de experimento
        
        Args:
            experiment_id: ID do experimento
            result: Resultado final
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.INFO,
            log_type=LogType.COMPLETION,
            message="Experimento concluído",
            data={
                "result": result,
                "end_time": datetime.now().isoformat()
            }
        )
    
    def log_error(self,
                 experiment_id: str,
                 error: Exception,
                 context: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra erro
        
        Args:
            experiment_id: ID do experimento
            error: Exceção ocorrida
            context: Contexto adicional
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.ERROR,
            log_type=LogType.ERROR,
            message=str(error),
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
        )
    
    def log_checkpoint(self,
                      experiment_id: str,
                      checkpoint_id: str,
                      generation: int) -> None:
        """
        Registra criação de checkpoint
        
        Args:
            experiment_id: ID do experimento
            checkpoint_id: ID do checkpoint
            generation: Geração do checkpoint
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.INFO,
            log_type=LogType.CHECKPOINT,
            message=f"Checkpoint criado para geração {generation}",
            data={
                "checkpoint_id": checkpoint_id,
                "generation": generation
            }
        )
    
    def log_metric(self,
                  experiment_id: str,
                  metric_name: str,
                  metric_value: float,
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra métrica
        
        Args:
            experiment_id: ID do experimento
            metric_name: Nome da métrica
            metric_value: Valor da métrica
            metadata: Metadados adicionais
        """
        self._log(
            experiment_id=experiment_id,
            level=LogLevel.INFO,
            log_type=LogType.METRIC,
            message=f"Métrica: {metric_name} = {metric_value}",
            data={
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metadata": metadata
            }
        )
    
    def log_event(self,
                 experiment_id: str,
                 event_name: str,
                 event_data: Optional[Dict[str, Any]] = None,
                 level: LogLevel = LogLevel.INFO) -> None:
        """
        Registra evento genérico
        
        Args:
            experiment_id: ID do experimento
            event_name: Nome do evento
            event_data: Dados do evento
            level: Nível do log
        """
        self._log(
            experiment_id=experiment_id,
            level=level,
            log_type=LogType.EVENT,
            message=event_name,
            data=event_data
        )
    
    def get_logs(self,
                experiment_id: str,
                level: Optional[LogLevel] = None,
                log_type: Optional[LogType] = None,
                limit: Optional[int] = None) -> List[LogEntry]:
        """
        Retorna logs de um experimento
        
        Args:
            experiment_id: ID do experimento
            level: Filtrar por nível (opcional)
            log_type: Filtrar por tipo (opcional)
            limit: Limitar número de resultados (opcional)
        
        Returns:
            Lista de LogEntry
        """
        file_path = self.base_path / f"{experiment_id}.jsonl"
        
        if not file_path.exists():
            return []
        
        logs = []
        
        with open(file_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                
                # Filtros
                if level and data["level"] != level.value:
                    continue
                
                if log_type and data["type"] != log_type.value:
                    continue
                
                entry = LogEntry(
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    experiment_id=data["experiment_id"],
                    level=LogLevel(data["level"]),
                    log_type=LogType(data["type"]),
                    message=data["message"],
                    data=data.get("data")
                )
                
                logs.append(entry)
                
                # Limite
                if limit and len(logs) >= limit:
                    break
        
        return logs
    
    def get_errors(self, experiment_id: str) -> List[LogEntry]:
        """
        Retorna apenas erros de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            Lista de LogEntry com erros
        """
        return self.get_logs(experiment_id, level=LogLevel.ERROR)
    
    def get_metrics(self, experiment_id: str) -> List[LogEntry]:
        """
        Retorna apenas métricas de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            Lista de LogEntry com métricas
        """
        return self.get_logs(experiment_id, log_type=LogType.METRIC)
    
    def get_summary(self, experiment_id: str) -> Dict[str, Any]:
        """
        Retorna resumo dos logs
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            Dict com estatísticas dos logs
        """
        logs = self.get_logs(experiment_id)
        
        if not logs:
            return {
                "total_logs": 0,
                "by_level": {},
                "by_type": {},
                "errors": 0,
                "start_time": None,
                "end_time": None
            }
        
        # Contadores
        by_level = {}
        by_type = {}
        
        for log in logs:
            by_level[log.level.value] = by_level.get(log.level.value, 0) + 1
            by_type[log.log_type.value] = by_type.get(log.log_type.value, 0) + 1
        
        return {
            "total_logs": len(logs),
            "by_level": by_level,
            "by_type": by_type,
            "errors": by_level.get(LogLevel.ERROR.value, 0),
            "start_time": logs[0].timestamp.isoformat(),
            "end_time": logs[-1].timestamp.isoformat()
        }
    
    def clear_logs(self, experiment_id: str) -> bool:
        """
        Remove logs de um experimento
        
        Args:
            experiment_id: ID do experimento
        
        Returns:
            True se removido, False se não encontrado
        """
        file_path = self.base_path / f"{experiment_id}.jsonl"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def _log(self,
            experiment_id: str,
            level: LogLevel,
            log_type: LogType,
            message: str,
            data: Optional[Dict[str, Any]] = None) -> None:
        """Registra entrada de log"""
        entry = LogEntry(
            timestamp=datetime.now(),
            experiment_id=experiment_id,
            level=level,
            log_type=log_type,
            message=message,
            data=data
        )
        
        # Salva em arquivo JSONL (uma linha por log)
        file_path = self.base_path / f"{experiment_id}.jsonl"
        
        with open(file_path, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
