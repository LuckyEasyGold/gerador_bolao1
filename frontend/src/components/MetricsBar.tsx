interface MetricItem {
  label: string;
  value: string;
  accent?: string;
}

interface MetricsBarProps {
  items: MetricItem[];
}

export function MetricsBar({ items }: MetricsBarProps) {
  return (
    <section className="metrics-grid">
      {items.map((item) => (
        <article key={item.label} className="metric-card">
          <p>{item.label}</p>
          <strong style={item.accent ? { color: item.accent } : undefined}>{item.value}</strong>
        </article>
      ))}
    </section>
  );
}
