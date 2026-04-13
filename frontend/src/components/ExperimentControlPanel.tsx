import { useState, type FormEvent } from "react";
import type { ExperimentListItem, OptimizeFormValues } from "../types/api";

interface ExperimentControlPanelProps {
  experiments: ExperimentListItem[];
  selectedExperimentId: string | null;
  loading: boolean;
  onSelectExperiment: (experimentId: string) => void;
  onStartExperiment: (values: OptimizeFormValues) => Promise<void>;
}

const initialForm: OptimizeFormValues = {
  name: "Campanha Evolutiva Visual",
  budget: 100,
  seed: 42,
  population_size: 20,
  generations: 24,
  simulations: 500
};

export function ExperimentControlPanel({
  experiments,
  selectedExperimentId,
  loading,
  onSelectExperiment,
  onStartExperiment
}: ExperimentControlPanelProps) {
  const [formValues, setFormValues] = useState<OptimizeFormValues>(initialForm);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onStartExperiment(formValues);
  }

  function updateField<K extends keyof OptimizeFormValues>(field: K, value: OptimizeFormValues[K]) {
    setFormValues((current) => ({
      ...current,
      [field]: value
    }));
  }

  return (
    <section className="panel panel-form">
      <div className="panel-heading">
        <p className="eyebrow">Controle</p>
        <h2>Nova campanha evolutiva</h2>
      </div>

      <form className="control-form" onSubmit={handleSubmit}>
        <label>
          <span>Nome do experimento</span>
          <input
            value={formValues.name}
            onChange={(event) => updateField("name", event.target.value)}
            placeholder="Nome da campanha"
            required
          />
        </label>

        <div className="grid-2">
          <label>
            <span>Orçamento</span>
            <input
              type="number"
              min={1}
              step={1}
              value={formValues.budget}
              onChange={(event) => updateField("budget", Number(event.target.value))}
              required
            />
          </label>

          <label>
            <span>Seed</span>
            <input
              type="number"
              step={1}
              value={formValues.seed ?? ""}
              onChange={(event) =>
                updateField("seed", event.target.value ? Number(event.target.value) : undefined)
              }
            />
          </label>
        </div>

        <div className="grid-3">
          <label>
            <span>População</span>
            <input
              type="number"
              min={10}
              max={100}
              value={formValues.population_size}
              onChange={(event) => updateField("population_size", Number(event.target.value))}
              required
            />
          </label>

          <label>
            <span>Gerações</span>
            <input
              type="number"
              min={1}
              max={100}
              value={formValues.generations}
              onChange={(event) => updateField("generations", Number(event.target.value))}
              required
            />
          </label>

          <label>
            <span>Simulações</span>
            <input
              type="number"
              min={100}
              step={100}
              value={formValues.simulations}
              onChange={(event) => updateField("simulations", Number(event.target.value))}
              required
            />
          </label>
        </div>

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Criando..." : "Iniciar experimento"}
        </button>
      </form>

      <div className="panel-heading section-gap">
        <p className="eyebrow">Histórico</p>
        <h3>Experimentos disponíveis</h3>
      </div>

      <div className="experiment-list">
        {experiments.length === 0 ? (
          <p className="empty-state">Nenhum experimento em memória ainda.</p>
        ) : null}

        {experiments.map((experiment) => {
          const isSelected = experiment.id === selectedExperimentId;
          return (
            <button
              key={experiment.id}
              type="button"
              className={`experiment-list-item ${isSelected ? "selected" : ""}`}
              onClick={() => onSelectExperiment(experiment.id)}
            >
              <strong>{experiment.name}</strong>
              <span>{experiment.status}</span>
              <span>{experiment.progress}% concluído</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
