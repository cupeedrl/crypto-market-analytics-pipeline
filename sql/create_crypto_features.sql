CREATE TABLE IF NOT EXISTS crypto_features (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open_price NUMERIC(20, 8),
    close_price NUMERIC(20, 8),
    high_price NUMERIC(20, 8),
    low_price NUMERIC(20, 8),
    daily_return NUMERIC(10, 4),
    volatility_7d NUMERIC(10, 4),
    volatility_30d NUMERIC(10, 4),
    total_volume NUMERIC(30, 8),
    volume_change_pct NUMERIC(10, 4),
    rsi_14 NUMERIC(10, 4),
    price_to_volume_ratio NUMERIC(20, 8),
    trend_strength NUMERIC(10, 4),
    is_bullish BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_crypto_features_symbol_date 
    ON crypto_features(symbol, date DESC);

CREATE INDEX IF NOT EXISTS idx_crypto_features_date 
    ON crypto_features(date DESC);