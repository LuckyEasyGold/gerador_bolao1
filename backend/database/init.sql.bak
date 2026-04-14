-- Schema inicial do banco de dados Lotofácil Optimizer

-- Tabela de concursos históricos
CREATE TABLE IF NOT EXISTS contests (
    contest_id INTEGER PRIMARY KEY,
    draw_date DATE NOT NULL,
    numbers INTEGER[] NOT NULL CHECK (array_length(numbers, 1) = 15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_numbers CHECK (
        (SELECT COUNT(DISTINCT n) FROM unnest(numbers) n WHERE n BETWEEN 1 AND 25) = 15
    )
);

CREATE INDEX idx_contests_date ON contests(draw_date DESC);
CREATE INDEX idx_contests_numbers ON contests USING GIN(numbers);

-- Tabela de experimentos evolutivos
CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    budget DECIMAL(10,2) NOT NULL,
    population_size INTEGER NOT NULL,
    generations INTEGER NOT NULL,
    seed INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    best_fitness DECIMAL(15,6),
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);

-- Tabela de indivíduos (DNA)
CREATE TABLE IF NOT EXISTS individuals (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES experiments(id) ON DELETE CASCADE,
    generation INTEGER NOT NULL,
    dna JSONB NOT NULL,
    fitness DECIMAL(15,6),
    roi DECIMAL(15,6),
    risk DECIMAL(15,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_individuals_experiment ON individuals(experiment_id, generation);
CREATE INDEX idx_individuals_fitness ON individuals(fitness DESC);

-- Tabela de bolões gerados
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES experiments(id) ON DELETE CASCADE,
    individual_id INTEGER REFERENCES individuals(id) ON DELETE CASCADE,
    games JSONB NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    game_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tickets_experiment ON tickets(experiment_id);

-- Tabela de resultados de simulação
CREATE TABLE IF NOT EXISTS simulation_results (
    id SERIAL PRIMARY KEY,
    individual_id INTEGER REFERENCES individuals(id) ON DELETE CASCADE,
    simulations INTEGER NOT NULL,
    avg_return DECIMAL(15,6),
    std_return DECIMAL(15,6),
    win_rate DECIMAL(8,6),
    max_prize DECIMAL(15,2),
    prize_distribution JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_simulation_individual ON simulation_results(individual_id);

-- Tabela de features cacheadas
CREATE TABLE IF NOT EXISTS feature_cache (
    id SERIAL PRIMARY KEY,
    feature_type VARCHAR(100) NOT NULL,
    contest_id INTEGER,
    data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feature_cache_type ON feature_cache(feature_type, contest_id);

-- Tabela de logs de execução
CREATE TABLE IF NOT EXISTS execution_logs (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES experiments(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_experiment ON execution_logs(experiment_id, created_at DESC);

-- View para estatísticas de experimentos
CREATE OR REPLACE VIEW experiment_stats AS
SELECT 
    e.id,
    e.name,
    e.status,
    e.generations,
    COUNT(DISTINCT i.generation) as completed_generations,
    MAX(i.fitness) as best_fitness,
    AVG(i.fitness) as avg_fitness,
    e.started_at,
    e.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(e.completed_at, NOW()) - e.started_at)) as duration_seconds
FROM experiments e
LEFT JOIN individuals i ON e.id = i.experiment_id
GROUP BY e.id;

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_feature_cache_updated_at BEFORE UPDATE ON feature_cache
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
