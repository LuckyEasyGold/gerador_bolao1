import type {
  ExperimentListResponse,
  OptimizeFormValues,
  OptimizeResultResponse,
  OptimizeStartResponse,
  OptimizeStatus,
  VisualEvolutionResponse
} from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Falha na requisição para ${path}`);
  }

  return (await response.json()) as T;
}

export async function listExperiments() {
  return request<ExperimentListResponse>("/optimize/list");
}

export async function startOptimization(values: OptimizeFormValues) {
  const payload = {
    name: values.name,
    budget: values.budget,
    seed: values.seed,
    config: {
      population_size: values.population_size,
      generations: values.generations,
      simulations: values.simulations
    }
  };

  return request<OptimizeStartResponse>("/optimize/start", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getOptimizationStatus(experimentId: string) {
  return request<OptimizeStatus>(`/optimize/status/${experimentId}`);
}

export async function getOptimizationResult(experimentId: string) {
  return request<OptimizeResultResponse>(`/optimize/result/${experimentId}`);
}

export async function getVisualEvolution(experimentId: string) {
  return request<VisualEvolutionResponse>(`/optimize/visual/${experimentId}`);
}
