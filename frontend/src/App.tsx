import { useState } from "react";
import "./App.css";

interface BolaoResult {
  j15: number;
  j16: number;
  j17: number;
  custo_total: number;
  total_jogos: number;
}

export default function App() {
  const [valor_total, setValorTotal] = useState<string>("1000");
  const [cotas, setCotas] = useState<string>("5");
  const [valor_unitario, setValorUnitario] = useState<string>("200");
  
  const [resultado, setResultado] = useState<BolaoResult | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const gerarBolao = async () => {
    setCarregando(true);
    setErro(null);
    setResultado(null);

    try {
      const response = await fetch("http://localhost:8000/bolao/gerar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          valor_total_do_bolao: parseFloat(valor_total),
          cotas: parseInt(cotas),
          valor_unitario_do_bolao: parseFloat(valor_unitario),
          usar_pool_cache: true,
        }),
      });

      if (!response.ok) {
        throw new Error("Erro ao gerar bolão");
      }

      const data = await response.json();
      setResultado(data.saida);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setCarregando(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      gerarBolao();
    }
  };

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <header className="header">
          <h1>Gerador de Bolões</h1>
          <p className="subtitle">Lotofácil</p>
        </header>

        {/* Form */}
        <form className="form" onSubmit={(e) => { e.preventDefault(); gerarBolao(); }}>
          <div className="form-group">
            <label htmlFor="valor_total">Valor Total (R$)</label>
            <input
              id="valor_total"
              type="number"
              value={valor_total}
              onChange={(e) => setValorTotal(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="1000.00"
              step="0.01"
              min="10"
            />
          </div>

          <div className="form-group">
            <label htmlFor="cotas">Número de Cotas</label>
            <input
              id="cotas"
              type="number"
              value={cotas}
              onChange={(e) => setCotas(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="5"
              step="1"
              min="1"
            />
          </div>

          <div className="form-group">
            <label htmlFor="valor_unitario">Valor por Cota (R$)</label>
            <input
              id="valor_unitario"
              type="number"
              value={valor_unitario}
              onChange={(e) => setValorUnitario(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="200.00"
              step="0.01"
              min="1"
            />
          </div>

          <button type="submit" className="btn-gerar" disabled={carregando}>
            {carregando ? "Processando..." : "Gerar Bolão"}
          </button>
        </form>

        {/* Erro */}
        {erro && (
          <div className="erro">
            <p>❌ {erro}</p>
          </div>
        )}

        {/* Resultado */}
        {resultado && (
          <div className="resultado">
            <h2>Resultado</h2>
            
            <div className="resultado-grid">
              <div className="resultado-item j15">
                <span className="label">Jogos 15 números</span>
                <span className="valor">{resultado.j15}</span>
                <span className="preco">R$ {(resultado.j15 * 10).toFixed(2)}</span>
              </div>

              <div className="resultado-item j16">
                <span className="label">Jogos 16 números</span>
                <span className="valor">{resultado.j16}</span>
                <span className="preco">R$ {(resultado.j16 * 20).toFixed(2)}</span>
              </div>

              <div className="resultado-item j17">
                <span className="label">Jogos 17 números</span>
                <span className="valor">{resultado.j17}</span>
                <span className="preco">R$ {(resultado.j17 * 30).toFixed(2)}</span>
              </div>
            </div>

            <div className="resultado-resumo">
              <div className="resumo-row">
                <span>Total de Jogos:</span>
                <strong>{resultado.total_jogos}</strong>
              </div>
              <div className="resumo-row">
                <span>Custo Total:</span>
                <strong>R$ {resultado.custo_total.toFixed(2)}</strong>
              </div>
            </div>
          </div>
        )}

        {/* Estado inicial */}
        {!resultado && !erro && !carregando && (
          <div className="info-vazio">
            <p>Preencha os valores e clique em "Gerar Bolão"</p>
          </div>
        )}
      </div>
    </div>
  );
}
