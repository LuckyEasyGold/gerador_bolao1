export interface OptimizeFormValues {
  name: string;
  budget: number;
  seed?: number;
  population_size: number;
  generations: number;
  simulations: number;
}

export interface VisualGoal {
  label: string;
  description: string;
  target: {
    x: number;
    y: number;
    z: number;
  };
  metrics: {
    fitness: number;
    roi: number;
    risk_inverse: number;
  };
}

export interface VisualIndividual {
  id: string;
  generation: number;
  fitness: number;
  roi: number;
  risk: number;
  distance_to_goal: number;
  x: number;
  y: number;
  z: number;
  scale: number;
  opacity: number;
  color: string;
  is_elite: boolean;
  genes: Record<string, number>;
}

export interface VisualSnapshot {
  generation: number;
  individuals: VisualIndividual[];
  objective: VisualGoal;
  population_size: number;
  best_fitness: number;
  avg_fitness: number;
  avg_distance_to_goal: number;
  centroid: {
    x: number;
    y: number;
    z: number;
  };
}

export interface GenerationStat {
  generation: number;
  best_fitness: number;
  avg_fitness: number;
  worst_fitness: number;
  std_fitness: number;
  best_roi: number;
  avg_roi: number;
  diversity: number;
  elapsed_time: number;
}

export interface OptimizeResultPayload {
  best_dna: Record<string, number>;
  best_fitness: number;
  generations_run: number;
  total_time: number;
  convergence_generation: number | null;
  generation_stats: GenerationStat[];
  visual_goal: VisualGoal;
  visual_history: VisualSnapshot[];
}

export interface OptimizeStatus {
  id: string;
  name: string;
  budget: number;
  config?: Record<string, number>;
  seed?: number;
  status: "starting" | "running" | "completed" | "failed";
  progress: number;
  current_generation: number;
  best_fitness: number | null;
  best_roi: number | null;
  visual_goal?: VisualGoal;
  visual_history?: VisualSnapshot[];
  current_visual?: VisualSnapshot | null;
  result?: OptimizeResultPayload | null;
  error?: string;
  visual_summary?: {
    generation: number;
    population_size: number;
    avg_distance_to_goal: number | null;
    best_individual: VisualIndividual | null;
  };
}

export interface OptimizeResultResponse {
  success: boolean;
  experiment_id: string;
  name: string;
  budget: number;
  result: OptimizeResultPayload;
  visual_goal: VisualGoal;
  visual_history: VisualSnapshot[];
}

export interface OptimizeStartResponse {
  success: boolean;
  experiment_id: string;
  message: string;
  config: Record<string, number>;
  visual_goal: VisualGoal;
}

export interface VisualEvolutionResponse {
  success: boolean;
  experiment_id: string;
  name: string;
  status: string;
  goal: VisualGoal;
  current_generation: number;
  timeline: VisualSnapshot[];
  current_visual: VisualSnapshot | null;
}

export interface ExperimentListItem {
  id: string;
  name: string;
  status: string;
  progress: number;
  current_generation: number;
  best_fitness: number | null;
  best_roi: number | null;
}

export interface ExperimentListResponse {
  success: boolean;
  total: number;
  experiments: ExperimentListItem[];
}
