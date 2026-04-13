interface EvolutionTimelineProps {
  generations: number[];
  selectedGeneration: number;
  maxGeneration: number;
  onChange: (generation: number) => void;
}

export function EvolutionTimeline({
  generations,
  selectedGeneration,
  maxGeneration,
  onChange
}: EvolutionTimelineProps) {
  const safeMaxGeneration = Math.max(maxGeneration, generations[generations.length - 1] ?? 0, 0);

  return (
    <section className="panel timeline-panel">
      <div className="panel-heading">
        <p className="eyebrow">Timeline</p>
        <h2>Exploração das gerações</h2>
      </div>

      <div className="timeline-body">
        <input
          type="range"
          min={0}
          max={safeMaxGeneration}
          value={Math.min(selectedGeneration, safeMaxGeneration)}
          onChange={(event) => onChange(Number(event.target.value))}
        />

        <div className="timeline-labels">
          <span>Geração 0</span>
          <strong>Geração {selectedGeneration}</strong>
          <span>Máximo {safeMaxGeneration}</span>
        </div>

        <div className="timeline-chips">
          {generations.map((generation) => (
            <button
              key={generation}
              type="button"
              className={`generation-chip ${generation === selectedGeneration ? "active" : ""}`}
              onClick={() => onChange(generation)}
            >
              {generation}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
