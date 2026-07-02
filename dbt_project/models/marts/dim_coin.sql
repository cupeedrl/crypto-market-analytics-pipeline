{{ config(materialized='table') }}

select distinct
    coin_id,
    coin_name,
    symbol,
    min(fetched_at) as first_seen,
    max(fetched_at) as last_updated
from {{ ref('stg_crypto_prices') }}
group by coin_id, coin_name, symbol