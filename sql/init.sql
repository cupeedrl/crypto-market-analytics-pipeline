
-- DIMENSION TABLE: COIN METADATA
CREATE TABLE IF NOT EXISTS dim_coin (
    coin_id VARCHAR(100) PRIMARY KEY,
    coin_name VARCHAR(200) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ODS LAYER: DAILY METRICS (BATCH DATA)
CREATE TABLE IF NOT EXISTS ods_daily_metrics (
    id SERIAL PRIMARY KEY,

    coin_id VARCHAR(100) NOT NULL REFERENCES dim_coin(coin_id),

    current_price NUMERIC(18,8) NOT NULL,
    market_cap NUMERIC(20,2),
    total_volume NUMERIC(20,2),

    price_change_24h NUMERIC(10,4),
    price_change_percent_24h NUMERIC(8,4),

    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    is_processed BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT chk_price_positive CHECK (current_price > 0),

    CONSTRAINT chk_volume_non_negative CHECK (total_volume >= 0)
);

-- ============================================
-- AUDIT LOG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,

    coin_id VARCHAR(100) NOT NULL REFERENCES dim_coin(coin_id),

    action VARCHAR(50) NOT NULL,

    details JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_action
        CHECK (
            action IN (
                'INSERT',
                'UPDATE',
                'DELETE'
            )
        )
);
-- Real-time streaming prices table
CREATE TABLE IF NOT EXISTS real_time_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    current_price NUMERIC(20, 8) NOT NULL,
    price_change NUMERIC(20, 8),
    price_change_percent NUMERIC(10, 4),
    volume NUMERIC(30, 8),
    processed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    kafka_offset BIGINT,
    kafka_partition INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for fast queries
CREATE INDEX IF NOT EXISTS idx_real_time_prices_symbol ON real_time_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_real_time_prices_processed_at ON real_time_prices(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_real_time_prices_symbol_time ON real_time_prices(symbol, processed_at DESC);

-- INDEXES

CREATE INDEX IF NOT EXISTS idx_ods_coin_time
ON ods_daily_metrics (coin_id, fetched_at);

CREATE INDEX IF NOT EXISTS idx_ods_processed
ON ods_daily_metrics (is_processed)
WHERE is_processed = FALSE;

CREATE INDEX IF NOT EXISTS idx_audit_time
ON audit_log (created_at);

CREATE INDEX IF NOT EXISTS idx_audit_coin
ON audit_log (coin_id);

-- VIEW: DAILY VOLUME SUMMARY
CREATE OR REPLACE VIEW v_daily_volume AS
SELECT
    c.coin_id,
    c.coin_name,
    c.symbol,

    DATE(m.fetched_at) AS fetch_date,
    AVG(m.current_price) AS avg_price,
    SUM(m.total_volume) AS total_volume,
    COUNT(*) AS record_count
FROM ods_daily_metrics m

JOIN dim_coin c
    ON m.coin_id = c.coin_id

GROUP BY
    c.coin_id,
    c.coin_name,
    c.symbol,
    DATE(m.fetched_at);

-- MATERIALIZED VIEW: TOP COINS BY VOLUME (7 DAYS)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_coins AS
SELECT
    c.coin_id,
    c.coin_name,
    c.symbol,

    AVG(m.current_price) AS avg_price_7d,

    SUM(m.total_volume) AS total_volume_7d,

    AVG(m.price_change_percent_24h) AS avg_change_7d

FROM ods_daily_metrics m

JOIN dim_coin c
    ON m.coin_id = c.coin_id

WHERE m.fetched_at >= CURRENT_DATE - INTERVAL '7 days'

GROUP BY
    c.coin_id,
    c.coin_name,
    c.symbol;

-- Required for REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_coins_coin
ON mv_top_coins (coin_id);

-- FUNCTION: AUTO UPDATE updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS
$$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: AUTO UPDATE updated_at
CREATE TRIGGER trg_dim_coin_updated
BEFORE UPDATE
ON dim_coin
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- PROCEDURE: REFRESH MATERIALIZED VIEW

CREATE OR REPLACE PROCEDURE refresh_mv_top_coins()
LANGUAGE plpgsql
AS
$$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_coins;
END;
$$;

-- FUNCTION: AUDIT INSERTS

CREATE OR REPLACE FUNCTION log_metric_insert()
RETURNS TRIGGER AS
$$
BEGIN

    INSERT INTO audit_log (
        coin_id,
        action,
        details
    )
    VALUES (
        NEW.coin_id,
        'INSERT',
        jsonb_build_object(
            'price', NEW.current_price,
            'volume', NEW.total_volume
        )
    );

    RETURN NEW;

END;
$$ LANGUAGE plpgsql;

-- TRIGGER: LOG INSERTS
CREATE TRIGGER trg_metric_insert
AFTER INSERT
ON ods_daily_metrics
FOR EACH ROW
EXECUTE FUNCTION log_metric_insert();

-- PROCEDURE: MARK RECORDS OF A COIN AS PROCESSED
CREATE OR REPLACE PROCEDURE mark_as_processed(
    p_coin_id VARCHAR
)
LANGUAGE plpgsql
AS
$$
BEGIN

    UPDATE ods_daily_metrics
    SET is_processed = TRUE
    WHERE coin_id = p_coin_id
      AND is_processed = FALSE;

END;
$$;

-- PROCEDURE: MARK BATCH AS PROCESSED
CREATE OR REPLACE PROCEDURE mark_batch_processed(
    p_before_date DATE
)
LANGUAGE plpgsql
AS
$$
BEGIN

    UPDATE ods_daily_metrics
    SET is_processed = TRUE
    WHERE fetched_at < (p_before_date + INTERVAL '1 day')
      AND is_processed = FALSE;

END;
$$;

-- EXAMPLE TRANSACTION

/*
BEGIN;

INSERT INTO audit_log (
    coin_id,
    action,
    details
)
VALUES (
    'bitcoin',
    'UPDATE',
    '{"reason":"manual correction"}'
);

UPDATE ods_daily_metrics
SET is_processed = TRUE
WHERE id = 1;

COMMIT;

-- If error:
-- ROLLBACK;
*/

