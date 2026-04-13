import { useEffect, useMemo, useState } from "react";
import { ConvergencePanel } from "./components/ConvergencePanel";
import { EvolutionScene } from "./components/EvolutionScene";
import { EvolutionTimeline } from "./components/EvolutionTimeline";
import { ExperimentControlPanel } from "./components/ExperimentControlPanel";
import { MetricsBar } from "./components/MetricsBar";
import { ResultSummary } from "./components/ResultSummary";
import {
  getOptimizationResult,
  getOptimizationStatus,
  getVisualEvolution,
  listExperiments,
  startOptimization
} from "./services/api";
import type {
  ExperimentListItem,
  OptimizeFormValues,
  OptimizeResultPayload,
  OptimizeStatus,
  VisualEvolutionResponse,
  VisualSnapshot
} from "./types/api";

function formatMetric(value: number | null | undefined, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return value.toFixed(digits);
}

export default function App() {
  const [experiments, setExperiments] = useState<ExperimentListItem[]>([]);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);
  const [status, setStatus] = useState<OptimizeStatus | null>(null);
  const [result, setResult] = useState<OptimizeResultPayload | null>(null);
  const [visualData, setVisualData] = useState<VisualEvolutionResponse | null>(null);
  const [selectedGeneration, setSelectedGeneration] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshExperiments() {
    const response = await listExperiments();
    setExperiments(response.experiments);
    if (!selectedExperimentId && response.experiments[0]) {
      setSelectedExperimentId(response.experiments[0].id);
    }
  }

  async function refreshSelectedExperiment(experimentId: string) {
    const [nextStatus, nextVisual] = await Promise.all([
      getOptimizationStatus(experimentId),
      getVisualEvolution(experimentId)
    ]);

    setStatus(nextStatus);
    setVisualData(nextVisual);
    setSelectedGeneration(nextVisual.current_generation);

    if (nextStatus.status === "completed") {
      const resultResponse = await getOptimizationResult(experimentId);
      setResult(resultResponse.result);
    } else {
      setResult(null);
    }
  }

  useEffect(() => {
    void refreshExperiments().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Falha ao carregar experimentos.");
    });
  }, []);

  useEffect(() => {
    if (!selectedExperimentId) {
      return;
    }

    void refreshSelectedExperiment(selectedExperimentId).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Falha ao carregar experimento.");
    });
  }, [selectedExperimentId]);

  useEffect(() => {
    if (!selectedExperimentId || !status || !["starting", "running"].includes(status.status)) {
      return;
    }

    const interval = window.setInterval(() => {
      void refreshSelectedExperiment(selectedExperimentId).catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Falha ao atualizar experimento.");
      });
    }, 3000);

    return () => window.clearInterval(interval);
  }, [selectedExperimentId, status]);

  async function handleStartExperiment(values: OptimizeFormValues) {
    setLoading(true);
    setError(null);

    try {
      const response = await startOptimization(values);
      await refreshExperiments();
      setSelectedExperimentId(response.experiment_id);
      await refreshSelectedExperiment(response.experiment_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Falha ao iniciar experimento.");
    } finally {
      setLoading(false);
    }
  }

  const availableGenerations = useMemo(
    () => visualData?.timeline.map((snapshot) => snapshot.generation) ?? [],
    [visualData]
  );

  const activeSnapshot = useMemo<VisualSnapshot | null>(() => {
    const fromTimeline =
      visualData?.timeline.find((snapshot) => snapshot.generation === selectedGeneration) ?? null;

    return fromTimeline ?? visualData?.current_visual ?? status?.current_visual ?? null;
  }, [selectedGeneration, status, visualData]);

  const metrics = useMemo(
    () => [
      {
        label: "Status",
        value: status?.status ?? "sem experimento",
        accent: status?.status === "completed" ? "#b7ff7c" : "#ffd166"
      },
      {
        label: "Progresso",
        value: status ? `${status.progress}%` : "--"
      },
      {
        label: "Melhor fitness",
        value: formatMetric(status?.best_fitness, 4)
      },
      {
        label: "Melhor ROI",
        value: formatMetric(status?.best_roi, 4)
      },
      {
        label: "Distância média ao objetivo",
        value: formatMetric(status?.visual_summary?.avg_distance_to_goal, 4)
      },
      {
        label: "População visível",
        value: status?.visual_summary?.population_size?.toString() ?? "--"
      }
    ],
    [status]
  );

  return (
    <main className="app-shell">
      <section className="hero-banner">
        <div>
          <p className="eyebrow">Fase 7</p>
          <h1>Frontend evolutivo para o otimizador de bolões</h1>
        </div>
        <p>
          A população deixa de ser só tabela e vira organismo visual: cada indivíduo ocupa um
          espaço, reage à qualidade da solução e mostra quão perto está do alvo evolutivo.
        </p>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="main-grid">
        <ExperimentControlPanel
          experiments={experiments}
          selectedExperimentId={selectedExperimentId}
          loading={loading}
          onSelectExperiment={setSelectedExperimentId}
          onStartExperiment={handleStartExperiment}
        />

        <div className="workspace-column">
          <MetricsBar items={metrics} />

          <EvolutionScene snapshot={activeSnapshot} goal={visualData?.goal ?? status?.visual_goal ?? null} />

          <EvolutionTimeline
            generations={availableGenerations}
            selectedGeneration={selectedGeneration}
            maxGeneration={status?.current_generation ?? 0}
            onChange={setSelectedGeneration}
          />

          <div className="insight-grid">
            <ConvergencePanel generationStats={result?.generation_stats ?? []} />
            <ResultSummary result={result} snapshot={activeSnapshot} />
          </div>
        </div>
      </section>
    </main>
  );
}
