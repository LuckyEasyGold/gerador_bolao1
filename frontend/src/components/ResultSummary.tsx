import type { OptimizeResultPayload, VisualSnapshot } from "../types/api";

interface ResultSummaryProps {
  result?: OptimizeResultPayload | null;
  snapshot?: VisualSnapshot | null;
}

export function ResultSummary({ result, snapshot }: ResultSummaryProps) {
  const dnaEntries = result ? Object.entries(result.best_dna).slice(0, 8) : [];

  return (
    <section className="panel summary-panel">
      <div className="panel-heading">
        <p className="eyebrow">Resultado</p>
        <h2>Leitura rápida do experimento</h2>
      </div>

      {result ? (
        <>
          <div className="summary-grid">
            <div>
              <span>Melhor fitness</span>
              <strong>{result.best_fitness.toFixed(4)}</strong>
            </div>
            <div>
              <span>Gerações executadas</span>
              <strong>{result.generations_run}</strong>
            </div>
            <div>
              <span>Tempo total</span>
              <strong>{result.total_time.toFixed(1)}s</strong>
            </div>
            <div>
              <span>Convergência</span>
              <strong>
                {result.convergence_generation !== null
                  ? `na geração ${result.convergence_generation}`
                  : "não detectada"}
              </strong>
            </div>
          </div>

          <div className="dna-preview">
            <h3>Genes dominantes do melhor indivíduo</h3>
            <div className="dna-tags">
              {dnaEntries.map(([key, value]) => (
                <span key={key} className="dna-tag">
                  {key}: {typeof value === "number" ? value.toFixed(3) : String(value)}
                </span>
              ))}
            </div>
          </div>
        </>
      ) : (
        <p className="empty-state">
          O resumo final aparece quando o experimento concluir. Enquanto isso, a cena 3D mostra a
          população em movimento.
        </p>
      )}

      {snapshot ? (
        <div className="snapshot-insight">
          <h3>Snapshot selecionado</h3>
          <p>
            População: {snapshot.population_size} indivíduos | Melhor fitness:{" "}
            {snapshot.best_fitness.toFixed(4)} | Distância média ao objetivo:{" "}
            {snapshot.avg_distance_to_goal.toFixed(4)}
          </p>
        </div>
      ) : null}
    </section>
  );
}
