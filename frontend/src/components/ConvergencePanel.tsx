import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { GenerationStat } from "../types/api";

interface ConvergencePanelProps {
  generationStats: GenerationStat[];
}

export function ConvergencePanel({ generationStats }: ConvergencePanelProps) {
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <p className="eyebrow">Convergência</p>
        <h2>Evolução das métricas por geração</h2>
      </div>

      {generationStats.length === 0 ? (
        <p className="empty-state">Os gráficos aparecem assim que houver resultado consolidado.</p>
      ) : (
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={generationStats}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="generation" stroke="#9fb2c7" />
              <YAxis stroke="#9fb2c7" />
              <Tooltip
                contentStyle={{
                  background: "#10263a",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: 16
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="best_fitness" stroke="#ffd166" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="avg_fitness" stroke="#4dd0e1" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="diversity" stroke="#94f7a2" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
