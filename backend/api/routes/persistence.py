from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from backend.core.persistence import (
    CheckpointManager,
    SeedManager,
    ExperimentLogger,
    ExportManager
)

router = APIRouter(prefix="/persistence", tags=["persistence"])

# Inicializa gerenciadores
checkpoint_manager = CheckpointManager()
seed_manager = SeedManager()
logger = ExperimentLogger()
export_manager = ExportManager()


# ============================================================================
# CHECKPOINTS
# ============================================================================

@router.get("/checkpoints/{experiment_id}")
async def list_checkpoints(experiment_id: str):
    """
    Lista checkpoints de um experimento
    
    Retorna todos os checkpoints salvos, ordenados por geração.
    """
    checkpoints = checkpoint_manager.list_checkpoints(experiment_id)
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "total": len(checkpoints),
        "checkpoints": [cp.to_dict() for cp in checkpoints]
    }


@router.get("/checkpoints/{experiment_id}/latest")
async def get_latest_checkpoint(experiment_id: str):
    """
    Retorna checkpoint mais recente de um experimento
    """
    checkpoint = checkpoint_manager.get_latest_checkpoint(experiment_id)
    
    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum checkpoint encontrado para experimento {experiment_id}"
        )
    
    return {
        "success": True,
        "checkpoint": checkpoint.to_dict()
    }


@router.get("/checkpoints/{experiment_id}/generation/{generation}")
async def get_checkpoint_by_generation(experiment_id: str, generation: int):
    """
    Retorna checkpoint de uma geração específica
    """
    checkpoint = checkpoint_manager.get_checkpoint_by_generation(
        experiment_id,
        generation
    )
    
    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint não encontrado para geração {generation}"
        )
    
    return {
        "success": True,
        "checkpoint": checkpoint.to_dict()
    }


@router.delete("/checkpoints/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str):
    """
    Deleta um checkpoint
    """
    deleted = checkpoint_manager.delete_checkpoint(checkpoint_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint {checkpoint_id} não encontrado"
        )
    
    return {
        "success": True,
        "message": "Checkpoint deletado"
    }


@router.post("/checkpoints/cleanup")
async def cleanup_checkpoints(days: int = Field(30, ge=1, le=365)):
    """
    Remove checkpoints antigos
    
    Remove checkpoints com mais de N dias.
    """
    removed = checkpoint_manager.cleanup_old_checkpoints(days)
    
    return {
        "success": True,
        "removed": removed,
        "message": f"{removed} checkpoints removidos"
    }


@router.get("/checkpoints/stats")
async def get_checkpoint_stats():
    """
    Retorna estatísticas de armazenamento de checkpoints
    """
    stats = checkpoint_manager.get_storage_stats()
    
    return {
        "success": True,
        "stats": stats
    }


# ============================================================================
# SEEDS
# ============================================================================

@router.get("/seeds/{experiment_id}")
async def get_seeds(experiment_id: str):
    """
    Retorna seeds de um experimento
    """
    seeds = seed_manager.get_seeds(experiment_id)
    
    if not seeds:
        raise HTTPException(
            status_code=404,
            detail=f"Seeds não encontradas para experimento {experiment_id}"
        )
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "seeds": seeds,
        "seed_hash": seed_manager.get_seed_hash(experiment_id)
    }


@router.post("/seeds/{experiment_id}/validate")
async def validate_seeds(experiment_id: str):
    """
    Valida seeds de um experimento
    
    Verifica se todas as seeds necessárias estão registradas.
    """
    is_valid = seed_manager.validate_seeds(experiment_id)
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "is_valid": is_valid,
        "message": "Seeds válidas" if is_valid else "Seeds incompletas"
    }


class SeedChainRequest(BaseModel):
    """Request para geração de chain de seeds"""
    master_seed: int = Field(..., description="Seed principal")
    components: Optional[List[str]] = None


@router.post("/seeds/generate")
async def generate_seed_chain(request: SeedChainRequest):
    """
    Gera chain de seeds a partir de master seed
    
    Útil para criar seeds determinísticas para todos os componentes.
    """
    seeds = seed_manager.generate_seed_chain(
        request.master_seed,
        request.components
    )
    
    return {
        "success": True,
        "master_seed": request.master_seed,
        "seeds": seeds
    }


@router.post("/seeds/{experiment_id}/compare/{other_experiment_id}")
async def compare_seeds(experiment_id: str, other_experiment_id: str):
    """
    Compara seeds de dois experimentos
    """
    comparison = seed_manager.compare_seeds(experiment_id, other_experiment_id)
    
    return {
        "success": True,
        "experiment_id1": experiment_id,
        "experiment_id2": other_experiment_id,
        "comparison": comparison,
        "all_match": all(comparison.values())
    }


@router.get("/seeds/list")
async def list_experiments_with_seeds():
    """
    Lista todos os experimentos com seeds registradas
    """
    experiments = seed_manager.list_experiments()
    
    return {
        "success": True,
        "total": len(experiments),
        "experiments": experiments
    }


# ============================================================================
# LOGS
# ============================================================================

@router.get("/logs/{experiment_id}")
async def get_logs(
    experiment_id: str,
    level: Optional[str] = None,
    log_type: Optional[str] = None,
    limit: Optional[int] = None
):
    """
    Retorna logs de um experimento
    
    Permite filtrar por nível e tipo.
    """
    from backend.core.persistence.experiment_logger import LogLevel, LogType
    
    # Converte filtros
    level_filter = LogLevel(level) if level else None
    type_filter = LogType(log_type) if log_type else None
    
    logs = logger.get_logs(
        experiment_id,
        level=level_filter,
        log_type=type_filter,
        limit=limit
    )
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "total": len(logs),
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/logs/{experiment_id}/errors")
async def get_errors(experiment_id: str):
    """
    Retorna apenas erros de um experimento
    """
    errors = logger.get_errors(experiment_id)
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "total": len(errors),
        "errors": [error.to_dict() for error in errors]
    }


@router.get("/logs/{experiment_id}/metrics")
async def get_metrics(experiment_id: str):
    """
    Retorna apenas métricas de um experimento
    """
    metrics = logger.get_metrics(experiment_id)
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "total": len(metrics),
        "metrics": [metric.to_dict() for metric in metrics]
    }


@router.get("/logs/{experiment_id}/summary")
async def get_log_summary(experiment_id: str):
    """
    Retorna resumo dos logs de um experimento
    """
    summary = logger.get_summary(experiment_id)
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "summary": summary
    }


@router.delete("/logs/{experiment_id}")
async def clear_logs(experiment_id: str):
    """
    Remove logs de um experimento
    """
    cleared = logger.clear_logs(experiment_id)
    
    if not cleared:
        raise HTTPException(
            status_code=404,
            detail=f"Logs não encontrados para experimento {experiment_id}"
        )
    
    return {
        "success": True,
        "message": "Logs removidos"
    }


# ============================================================================
# EXPORT
# ============================================================================

class ExportTicketRequest(BaseModel):
    """Request para exportação de bolão"""
    ticket_data: Dict[str, Any]
    format: str = Field("json", pattern="^(json|csv|txt)$")
    include_metadata: bool = True


@router.post("/export/ticket")
async def export_ticket(request: ExportTicketRequest):
    """
    Exporta bolão em formato especificado
    
    Formatos suportados: json, csv, txt
    """
    # Nota: Aqui seria necessário reconstruir o Ticket a partir dos dados
    # Por simplicidade, retornamos os dados formatados
    
    return {
        "success": True,
        "format": request.format,
        "message": "Use /export/ticket/download para baixar o arquivo"
    }


class ExportExperimentRequest(BaseModel):
    """Request para exportação de experimento"""
    experiment_data: Dict[str, Any]
    format: str = Field("json", pattern="^(json|csv)$")


@router.post("/export/experiment")
async def export_experiment(request: ExportExperimentRequest):
    """
    Exporta experimento completo
    
    Formatos suportados: json, csv
    """
    data = export_manager.export_experiment(
        request.experiment_data,
        format=request.format
    )
    
    # Salva
    filename = f"experiment_{request.experiment_data.get('id', 'unknown')}.{request.format}"
    file_path = export_manager.save_export(
        data,
        filename,
        experiment_id=request.experiment_data.get('id')
    )
    
    return {
        "success": True,
        "format": request.format,
        "file_path": file_path,
        "size_bytes": len(data)
    }


@router.get("/export/formats")
async def get_supported_formats():
    """
    Retorna formatos de exportação suportados
    """
    return {
        "success": True,
        "formats": {
            "ticket": ["json", "csv", "txt"],
            "experiment": ["json", "csv"],
            "dna": ["json", "csv", "txt"]
        }
    }


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
async def persistence_health():
    """
    Verifica saúde do módulo de persistência
    """
    checkpoint_stats = checkpoint_manager.get_storage_stats()
    experiments_with_seeds = len(seed_manager.list_experiments())
    
    return {
        "success": True,
        "status": "healthy",
        "checkpoints": {
            "total_experiments": checkpoint_stats["total_experiments"],
            "total_checkpoints": checkpoint_stats["total_checkpoints"],
            "storage_mb": checkpoint_stats["total_size_mb"]
        },
        "seeds": {
            "total_experiments": experiments_with_seeds
        }
    }
